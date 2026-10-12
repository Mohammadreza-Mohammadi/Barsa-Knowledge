"""The manager — the only thing that writes state, and the only thing trusted.

Rules it never breaks, taken from the workflow this mirrors:

  - it never "fixes" anything automatically: a failed gate stops the run,
    reports, and leaves the manifest untouched
  - it never trusts a role's self-reported result for a transition it can check
    itself -- the five verification gates run here, not in the role
  - it writes nothing outside `.agent-work/`
  - it never applies a batch to Barsa. That is a human action, and the last
    gate waits for a human to say they did it

One `run` iteration is exactly one transition. A handler that calls a role and
returns without deciding is the pattern that produced a polite infinite loop in
the system this is modelled on, so it does not exist here.
"""

import json
import os
import shutil
import subprocess

from . import barsa_host
from . import config as config_mod
from . import connection as connection_mod
from . import prompts, systems as systems_mod, verify
from .states import (
    EXIT_AWAITING_HUMAN, EXIT_NO_PROGRESS, EXIT_OK, EXIT_STOPPED,
    GATE_APPLY_APPROVAL, GATE_CLARIFICATION, GATE_SPEC_APPROVAL,
    KNOWN_RESULT_OUTCOMES, LANES, LOCK_RELEASED_STATES, ROLE_BY_STATE,
    RUN_MAX_ITERATIONS, RUN_STOPPED_STATES, TASK_TRANSITIONS, allows, lane_of,
)
from .store import Store, StoreError, now, sha256_file

SCHEMA_VERSION = 1

_UNSET = object()

NEED_KINDS = ("report.create", "report.update", "report.delete",
              "entity.create", "field.add", "folder.place")

RUNBOOK = {
    "needs-investigation": ("یک بررسی انسانی لازم است: evidence.md را بنویس و "
                            "بعد run بزن."),
    "failed": "مسیر بازگشت از failed به architecture است.",
    "conflict": ("اشیاء هدف از زمان نقشه عوض شده‌اند: نقشه را دوباره بساز یا "
                 "scope را تنگ‌تر کن."),
    "blocked": "بازگشایی blocked تصمیم انسان است.",
}


class ManagerError(Exception):
    """A gate failed, or the command is not valid for this state."""


class Manager:
    def __init__(self, repo_root):
        self.store = Store(repo_root)
        self.repo_root = self.store.repo_root
        self._config = None
        self._contract = None
        self._connection = _UNSET
        self._vocabulary = _UNSET

    # -- lazily loaded context --------------------------------------------

    @property
    def config(self):
        if self._config is None:
            self._config = config_mod.load(self.store)
        return self._config

    @property
    def contract(self):
        if self._contract is None:
            dist = (self.config["repository"].get("knowledge") or {}).get(
                "dist", "dist")
            self._contract = verify.load_contract(self.repo_root, dist)
            if self._contract is None:
                raise ManagerError(
                    "%s/index/semantic-contract.json is missing; nothing can "
                    "be verified without the write contract. Run "
                    "tools/extract.py first." % dist)
        return self._contract

    @property
    def vocabulary(self):
        """What the Host's own documents say, when dist/ carries them."""
        if self._vocabulary is _UNSET:
            dist = (self.config["repository"].get("knowledge") or {}).get(
                "dist", "dist")
            self._vocabulary = verify.load_vocabulary(self.repo_root, dist)
        return self._vocabulary

    @property
    def pack_dir(self):
        return (self.config["repository"].get("knowledge") or {}).get(
            "pack", "dist-report")

    def selector_index(self, system_id):
        return verify.load_selector_index(self.repo_root, system_id,
                                          self.pack_dir)

    # -- init --------------------------------------------------------------

    @property
    def connection(self):
        if self._connection is _UNSET:
            self._connection = connection_mod.load(self.store)
        return self._connection

    def reload_config(self):
        """Forget the cached config, so an edited file is picked up.

        The console is long-running: someone editing connection.yaml should
        not have to restart it to point at a different Barsa.
        """
        self._config = None
        self._contract = None
        self._connection = _UNSET
        self._vocabulary = _UNSET
        return self

    def systems(self):
        """Every system in the pack, with whether it can be authored."""
        knowledge = self.config["repository"].get("knowledge") or {}
        return systems_mod.catalogue(self.repo_root,
                                     knowledge.get("dist", "dist"),
                                     knowledge.get("pack", "dist-report"))

    def resolve_system(self, needle):
        knowledge = self.config["repository"].get("knowledge") or {}
        return systems_mod.find(self.repo_root, needle,
                                knowledge.get("dist", "dist"),
                                knowledge.get("pack", "dist-report"))

    def init(self, system_id=None):
        self.store.ensure()
        written = config_mod.write_templates(self.store, system_id)
        written += prompts.write_templates(self.store)
        made = connection_mod.write_template(self.store)
        if made:
            written.append(made)
        self.render_board()
        return written

    # -- creating a task ---------------------------------------------------

    def create_task(self, payload):
        """`import-issue`: a raw request becomes a task in state `new`."""
        self.store.ensure()
        request_text = payload.get("requestText")
        if not isinstance(request_text, str) or not request_text.strip():
            raise ManagerError("requestText is required and must not be empty")
        slug = payload.get("slug")
        if not slug:
            raise ManagerError("slug is required")
        task_type = payload.get("type") or "task"
        if task_type not in ("task", "spike"):
            raise ManagerError("type must be 'task' or 'spike', not %r"
                               % (task_type,))

        source = payload.get("source")
        if source and source.get("externalId"):
            dup = self._find_by_external_id(str(source["externalId"]))
            if dup:
                raise ManagerError(
                    "issue %s was already imported as task %s"
                    % (source["externalId"], dup))

        # No implicit default. If the request did not name a system, intake
        # works it out from the text, or asks. A quiet default is how a task
        # ends up planned against the wrong system's objects.
        system_id = payload.get("system")
        if system_id:
            row, candidates = self.resolve_system(system_id)
            if row is None:
                raise ManagerError(
                    "سیستم %r یکتا نیست. یکی از این‌ها را بده: %s"
                    % (system_id, "، ".join(
                        "%s (%s)" % (c["caption"], c["id"])
                        for c in candidates[:8])))
            system_id = row["id"]
        task_id = payload.get("id") or self.store.next_id()
        task_dir = self.store.create_task_dir(task_id, slug)

        self.store.write_text(task_dir, "request.md", _request_doc(
            task_id, request_text, source))
        limits = config_mod.budget_limits(self.config)
        manifest = {
            "schemaVersion": SCHEMA_VERSION,
            "id": str(task_id),
            "slug": slug,
            "type": task_type,
            "title": payload.get("title") or _first_line(request_text),
            "state": "new",
            "stateSince": now(),
            "previousState": None,
            "createdAt": now(),
            "need": {"kind": payload.get("kind"), "system": system_id},
            "spec": {"requestHash": None, "taskHash": None},
            "awaitingHuman": None,
            "blocker": None,
            "source": dict(source) if source else None,
            "budget": {name: {"used": 0, "max": limits[name]}
                       for name in sorted(limits)},
            "scope": {"allow": [], "deny": []},
            "gates": list((self.config["repository"].get("verification") or
                           {}).get("gates") or verify.GATES),
            "batch": {"path": None, "sha256": None, "commands": None,
                      "verifiedAt": None, "approvedSha256": None},
            "lastAttempt": None,
            # The console renders these when present; a Barsa task has no git
            # worktree and no diff, and saying so explicitly is better than
            # letting the UI guess.
            "git": None,
            "diff": None,
        }
        self.store.write_manifest(task_dir, manifest)
        self.store.append_event(task_dir, task_id, {
            "event": "task.created", "state": "new", "slug": slug,
            "system": system_id})
        self.render_board()
        return {"ok": True, "taskId": str(task_id),
                "taskDir": os.path.relpath(task_dir, self.repo_root)}

    def _find_by_external_id(self, external_id):
        for path in self.store.task_dirs():
            manifest = self.store.read_manifest(path)
            src = manifest.get("source") or {}
            if str(src.get("externalId") or "") == external_id:
                return manifest.get("id")
        return None

    # -- verification ------------------------------------------------------

    def verify_task(self, task_id, write=True):
        """Run the gates against the task's batch. Reports; changes nothing."""
        task_dir = self.store.task_dir_or_fail(task_id)
        manifest = self.store.read_manifest(task_dir)
        batch_path = os.path.join(task_dir, "change-batch.json")
        if not os.path.isfile(batch_path):
            return {"ok": False, "reason": "no change-batch.json yet",
                    "findings": [], "summary": None}
        try:
            with open(batch_path, encoding="utf-8") as fh:
                batch = json.load(fh)
        except ValueError as exc:
            findings = [verify.finding("lint", "error",
                                       "change-batch.json is not valid JSON: "
                                       "%s" % exc, "change-batch.json")]
            return {"ok": False, "findings": findings,
                    "summary": {"passed": False}}

        system_id = (manifest.get("need") or {}).get("system")
        gates = manifest.get("gates") or verify.GATES
        findings, summary = verify.run(
            batch, self.contract, manifest.get("scope"),
            self.selector_index(system_id), gates, self.vocabulary)
        result = {
            "ok": summary["passed"],
            "checkedAt": now(),
            "gates": list(gates),
            "summary": summary,
            "findings": findings,
            "batch": {"path": "change-batch.json",
                      "sha256": sha256_file(batch_path),
                      "commands": len(batch.get("changes") or ())},
        }
        if write:
            self.store.write_text(task_dir, "verify.json",
                                  json.dumps(result, ensure_ascii=False,
                                             indent=1, sort_keys=True) + "\n")
        return result

    # -- status ------------------------------------------------------------

    def status(self, task_id=None):
        repo_config = self.config["repository"]
        tasks = []
        targets = ([self.store.task_dir_or_fail(task_id)] if task_id
                   else self.store.task_dirs())
        for path in targets:
            try:
                tasks.append(self._task_status(path))
            except StoreError as exc:
                tasks.append({"id": os.path.basename(path).split("-", 1)[0],
                              "state": "unknown", "error": str(exc)})
        return {
            "generatedAt": now(),
            "repo": {
                "id": os.path.basename(self.repo_root),
                "path": self.repo_root,
                "head": None,
                # The console branches its last gate on this value; here it is
                # always human, because nothing in this repository can apply a
                # batch to Barsa.
                "mergedBy": (repo_config.get("integration") or {}).get(
                    "appliedBy", "human"),
            },
            "repository": {"health": self._repository_health()},
            "barsa": self._barsa_target(),
            "lanes": [{"title": lane["title"], "states": list(lane["states"])}
                      for lane in LANES],
            "tasks": tasks,
        }

    def _task_status(self, task_dir):
        manifest = self.store.read_manifest(task_dir)
        attempts = []
        for name in self.store.attempts(task_dir):
            result = self.store.read_result(task_dir, name) or {}
            adir = os.path.join(task_dir, "attempts", name)
            attempts.append({
                "n": int(name), "id": name,
                "role": result.get("role"),
                "outcome": result.get("outcome"),
                "requestedTransition": result.get("requestedTransition"),
                "artifacts": sorted(os.listdir(adir)) if os.path.isdir(adir)
                else [],
            })
        verify_doc = None
        raw = self.store.read_text(task_dir, "verify.json")
        if raw:
            try:
                verify_doc = json.loads(raw)
            except ValueError:
                verify_doc = {"malformed": True}

        task = dict(manifest)
        task["stateLane"] = lane_of(manifest.get("state"))
        task["attempts"] = attempts
        task["artifacts"] = sorted(
            name for name in os.listdir(task_dir)
            if os.path.isfile(os.path.join(task_dir, name)))
        task["verify"] = _verify_status(manifest, verify_doc)
        task["review"] = self._review_status(task_dir, attempts)
        task["releaseNote"] = self._release_note(task_dir)
        task["health"] = self._task_health(task_dir, manifest)
        return task

    def _review_status(self, task_dir, attempts):
        reviewer = [a for a in attempts if a.get("role") == "reviewer"]
        if not reviewer:
            return None
        last = reviewer[-1]
        result = self.store.read_result(task_dir, last["id"]) or {}
        evidence = result.get("evidence")
        problems = []
        if evidence is None:
            status = "missing"
        elif not isinstance(evidence, dict):
            status = "malformed"
            problems.append("evidence is not a mapping")
        else:
            status = "ok"
            for key in ("acceptance", "testCoverage", "additionalChecks"):
                rows = evidence.get(key)
                if rows is not None and not isinstance(rows, list):
                    status = "malformed"
                    problems.append("evidence.%s is not a list" % key)
        return {
            "attempt": last["id"],
            "decision": result.get("decision") or result.get(
                "requestedTransition"),
            "evidence": evidence if isinstance(evidence, dict) else {},
            "inconsistentWithReviewMd":
                self.store.read_text(task_dir, "review.md") is None,
            "evidenceStatus": status,
            "malformed": status == "malformed",
            "problems": problems,
        }

    def _release_note(self, task_dir):
        text = self.store.read_text(task_dir, "release-note.md")
        if text is None:
            return None
        front = _front_matter(text)
        problems = []
        user_visible = front.get("userVisible")
        if user_visible is None:
            problems.append("userVisible is missing")
        if user_visible is True and not front.get("headline"):
            problems.append("headline is missing")
        if user_visible is False and not front.get("reason"):
            problems.append("userVisible: false needs a reason")
        if front.get("headline") and len(str(front["headline"])) > 72:
            problems.append("headline is longer than 72 characters")
        return {
            "userVisible": user_visible,
            "headline": front.get("headline"),
            "body": text.split("---", 2)[-1].strip() or None,
            "approvedByHuman": False,
            "artifactPath": "release-note.md",
            "malformed": bool(problems),
            "problems": problems,
        }

    def _task_health(self, task_dir, manifest):
        lock = self.store.read_lock(self.store.transition_lock_path(task_dir))
        stuck_reasons = []
        if lock:
            alive = _pid_alive(lock.get("pid"), lock.get("hostname"))
            lock = {"pid": lock.get("pid"), "alive": alive,
                    "fromState": lock.get("fromState"),
                    "startedAt": lock.get("startedAt")}
            if alive is not True:
                stuck_reasons.append("stale-lock")
        state = manifest.get("state")
        recovery = {"suggested": None, "reason": None, "commands": []}
        if state not in LOCK_RELEASED_STATES and stuck_reasons:
            if lock and lock.get("alive") is None:
                recovery = {"suggested": "unlock",
                            "reason": "قفل روی ماشین دیگری نوشته شده؛ زنده "
                                      "بودنش قابل تشخیص نیست.",
                            "commands": ["unlock"]}
            else:
                recovery = {"suggested": "run",
                            "reason": "قفل کهنه است؛ run خودش پسش می‌گیرد.",
                            "commands": ["run"]}
        return {"transitionLock": lock, "dirtyPaths": [],
                "stuck": bool(stuck_reasons), "stuckReasons": stuck_reasons,
                "recovery": recovery}

    def _barsa_target(self):
        """Where this repository is pointed, as configured -- not as probed.

        Deliberately no network call: `status` is read by the board every few
        seconds, and a hanging host must never freeze the board. The console
        asks for live health separately.
        """
        settings = connection_mod.host_settings(self.config, self.connection)
        expected = (self.connection or {}).get("database") or {}
        key_env = settings.get("apiKeyEnv") or "BARSA_AI_HOST_KEY"
        return {
            "label": (self.connection or {}).get("label"),
            "appliedBy": (self.config["repository"].get("integration")
                          or {}).get("appliedBy", "human"),
            "prefix": settings.get("prefix"),
            "apiKeyEnv": key_env,
            "apiKeyPresent": bool(os.environ.get(key_env)),
            "expectedDatabase": {k: expected.get(k)
                                 for k in ("server", "name", "instance")},
            "enforceDatabase": expected.get("enforce") is not False,
            "configured": self.connection is not None,
        }

    def _repository_health(self):
        lock = self.store.read_lock(self.store.manager_lock_path())
        if lock:
            alive = _pid_alive(lock.get("pid"), lock.get("hostname"))
            lock = {"pid": lock.get("pid"), "alive": alive,
                    "task": lock.get("task"), "startedAt": lock.get("startedAt")}
        return {"managerLock": lock, "unownedDirtyFiles": [],
                "acceptsOperations": not (lock and lock.get("alive") is not False)}

    # -- the board ---------------------------------------------------------

    def render_board(self):
        rows = []
        for path in self.store.task_dirs():
            try:
                m = self.store.read_manifest(path)
            except StoreError:
                continue
            rows.append(m)
        lines = ["<!-- DO NOT EDIT. Generated from task manifests "
                 "(tools/manager.py). -->", "", "# Board", ""]
        lines.append("| Task | Slug | Need | State | Lane | Since | منتظر |")
        lines.append("|---|---|---|---|---|---|---|")
        for m in rows:
            gate = (m.get("awaitingHuman") or {}).get("kind") or ""
            lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                m.get("id"), m.get("slug"), (m.get("need") or {}).get("kind")
                or "", m.get("state"), lane_of(m.get("state")) or "",
                m.get("stateSince"), gate))
        lines.append("")
        lines.append("## Scope locks")
        lines.append("")
        lines.append("| Object | Task | State |")
        lines.append("|---|---|---|")
        for m in rows:
            if m.get("state") in LOCK_RELEASED_STATES:
                continue
            for entry in (m.get("scope") or {}).get("allow") or ():
                lines.append("| %s | #%s | %s |"
                             % (entry, m.get("id"), m.get("state")))
        text = "\n".join(lines) + "\n"
        os.makedirs(self.store.work, exist_ok=True)
        with open(self.store.board_path, "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(text)
        return self.store.board_path

    # -- transitions -------------------------------------------------------

    def _transition(self, task_dir, manifest, to_state, note=None,
                    extra=None):
        from_state = manifest.get("state")
        if not allows(from_state, to_state) and not (
                from_state == "blocked"
                and to_state == manifest.get("previousState")):
            raise ManagerError("%s → %s is not a legal transition"
                               % (from_state, to_state))
        manifest = dict(manifest)
        manifest["previousState"] = from_state
        manifest["state"] = to_state
        manifest["stateSince"] = now()
        if to_state not in ("blocked",):
            manifest["blocker"] = None
        if extra:
            manifest.update(extra)
        if to_state in LOCK_RELEASED_STATES:
            # Locks are released only here. A blocked task keeps them.
            manifest["awaitingHuman"] = None
        self.store.write_manifest(task_dir, manifest)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "state.changed", "from": from_state, "to": to_state,
            "note": note})
        self.render_board()
        return manifest

    def _set(self, task_dir, manifest, **fields):
        manifest = dict(manifest)
        manifest.update(fields)
        self.store.write_manifest(task_dir, manifest)
        self.render_board()
        return manifest

    def _open_gate(self, task_dir, manifest, kind, artifact=None):
        gate = {"kind": kind, "artifact": artifact, "since": now()}
        manifest = self._set(task_dir, manifest, awaitingHuman=gate)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "gate.opened", "gate": kind, "artifact": artifact})
        return manifest

    def _block(self, task_dir, manifest, kind, reason):
        manifest = dict(manifest)
        manifest["blocker"] = {"kind": kind, "reason": reason}
        manifest["previousState"] = manifest.get("state")
        return self._transition(task_dir, manifest, "blocked", note=reason,
                                extra={"blocker": {"kind": kind,
                                                   "reason": reason}})

    # -- budget ------------------------------------------------------------

    def _budget_key(self, role):
        return {"intake": "intakeRuns", "architect": "architectRuns",
                "implementer": "implementerRuns",
                "reviewer": "reviewerRuns"}[role]

    def _spend(self, task_dir, manifest, role):
        key = self._budget_key(role)
        budget = dict(manifest.get("budget") or {})
        row = dict(budget.get(key) or {"used": 0, "max": 0})
        if row["used"] >= row["max"]:
            raise _BudgetExhausted(key, row["max"])
        row["used"] += 1
        budget[key] = row
        total = dict(budget.get("attempts") or {"used": 0, "max": 0})
        if total["max"] and total["used"] >= total["max"]:
            raise _BudgetExhausted("attempts", total["max"])
        total["used"] = total.get("used", 0) + 1
        budget["attempts"] = total
        return self._set(task_dir, manifest, budget=budget)

    # -- role invocation ---------------------------------------------------

    def _pending_attempt(self, task_dir, role):
        """The attempt this role has open and not yet consumed, if any.

        An attempt is consumed exactly once. Without that mark, a role that
        was rejected and re-run would have its old result.yaml read a second
        time and the task would advance on a stale verdict -- the same class
        of bug as a progress counter fooled by a new attempt folder.
        """
        for name in reversed(self.store.attempts(task_dir)):
            adir = os.path.join(task_dir, "attempts", name)
            meta_path = os.path.join(adir, "attempt.json")
            if not os.path.isfile(meta_path):
                continue
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)
            if meta.get("role") != role or meta.get("consumedAt"):
                continue
            result = self.store.read_result(task_dir, name)
            return name, adir, meta, result
        return None, None, None, None

    def _mark_consumed(self, adir):
        meta_path = os.path.join(adir, "attempt.json")
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["consumedAt"] = now()
        with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=1)

    def _invoke_role(self, task_dir, manifest, role, log):
        """Return a consumed result, or None when the role still owes us one.

        With the manual provider this is where a run stops: the attempt folder
        is prepared, the gate says which role owes which files, and the next
        `run` picks the result up. With an agent provider the agent runs here
        and the same consumption path follows.
        """
        name, adir, meta, result = self._pending_attempt(task_dir, role)
        if name is not None and result is None:
            provider = (meta or {}).get("provider")
            if provider == "manual":
                # Say again what is still missing. A run that returns silently
                # teaches the operator to guess.
                self._report_pending(task_dir, adir, role, log)
                return None, manifest, name, adir
            # An agent provider that produced no result.yaml is a failed
            # attempt, not a reason to wait forever.
            raise ManagerError(
                "attempt %s for role %s has no result.yaml. Without it no "
                "decision can be made; write it or re-run." % (name, role))
        if name is not None and result is not None:
            outcome = result.get("outcome")
            if outcome not in KNOWN_RESULT_OUTCOMES:
                raise ManagerError(
                    "outcome=%r in attempts/%s/result.yaml is outside the "
                    "closed enum (%s). This stops; an unknown outcome that "
                    "passes silently is the worst case."
                    % (outcome, name, ", ".join(sorted(KNOWN_RESULT_OUTCOMES))))
            if result.get("role") != role:
                raise ManagerError(
                    "attempts/%s/result.yaml says role=%r but this transition "
                    "belongs to %r" % (name, result.get("role"), role))
            self._mark_consumed(adir)
            manifest = self._set(task_dir, manifest, awaitingHuman=None,
                                 lastAttempt={"n": int(name), "role": role,
                                              "outcome": outcome,
                                              "at": now()})
            self.store.append_event(task_dir, manifest["id"], {
                "event": "attempt.consumed", "attempt": name, "role": role,
                "outcome": outcome,
                "requestedTransition": result.get("requestedTransition")})
            return result, manifest, name, adir

        # No open attempt: start one.
        provider_name, settings = config_mod.provider_for(self.config, role)
        manifest = self._spend(task_dir, manifest, role)
        name, adir = self.store.next_attempt(task_dir, role)
        self._prepare_attempt(task_dir, manifest, role, name, adir,
                              provider_name)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "attempt.started", "attempt": name, "role": role,
            "provider": provider_name})

        if provider_name == "manual":
            rel = os.path.relpath(adir, self.repo_root)
            from .states import ROLE_OUTPUTS
            outputs = ROLE_OUTPUTS[role]
            log("نقش %s باید این‌ها را بنویسد:" % role)
            for out in outputs["required"]:
                log("  - %s" % out)
            log("  - %s/result.yaml" % rel)
            if outputs["optional"]:
                log("اختیاری: %s" % ", ".join(outputs["optional"]))
            log("دستور کامل نقش: %s/prompt.md" % rel)
            manifest = self._open_gate(task_dir, manifest, "role:%s" % role,
                                       os.path.join(rel, "prompt.md"))
            return None, manifest, name, adir

        self._run_provider(provider_name, settings, role, adir, log)
        result = self.store.read_result(task_dir, name)
        if result is None:
            raise ManagerError(
                "provider %s produced no result.yaml in attempts/%s"
                % (provider_name, name))
        return self._invoke_role(task_dir, manifest, role, log)

    def _vocabulary_table(self):
        """What a role may write, as the Host's own docs state it."""
        vocab = self.vocabulary
        if not vocab:
            return ("_بستهٔ دانش واژگانی ندارد: شرط غیرخالی، `parameters` و "
                    "`folder.kind` قابل نوشتن نیستند._")
        rows = []
        for key, title in (("comparisonOperators", "عملگرهای شرط"),
                           ("nullBehaviors", "nullBehavior"),
                           ("folderKinds", "folder.kind"),
                           ("reportParameterKeys", "کلیدهای parameter")):
            item = vocab.get(key)
            if isinstance(item, dict) and item.get("values"):
                rows.append("- **%s**: %s" % (
                    title, "، ".join("`%s`" % v for v in item["values"])))
                rows.append("  <br>منبع: `%s`" % item.get("document"))
        chain = vocab.get("navigationChain")
        if isinstance(chain, dict) and chain.get("values"):
            rows.append("- **مسیر navigation**: %s" % " ← ".join(
                "`%s` (زیرِ %s)" % (r["kind"], r["parent"])
                for r in chain["values"]))
            rows.append("  <br>منبع: `%s`" % chain.get("document"))
        ref = vocab.get("tempIdReferenceEncoding")
        if isinstance(ref, dict) and ref.get("values"):
            rows.append("- **ارجاع درون‌بسته‌ای**: هر ارجاع به شیئی که در "
                        "همین batch ساخته می‌شود باید %s را با هم داشته "
                        "باشد؛ فقط `tempId` کافی نیست."
                        % "، ".join("`%s`" % v for v in ref["values"]))
            rows.append("  <br>منبع: `%s`" % ref.get("document"))
        if not rows:
            return "_هیچ واژگانی استخراج نشده._"
        rows.append("")
        rows.append("هر مقداری بیرون این فهرست‌ها از گیت `unknowns` رد "
                    "می‌شود. فهرست را گسترش نده — اگر چیزی لازم داری که "
                    "اینجا نیست، در `questions.md` بنویس.")
        return "\n".join(rows)

    def _systems_table(self):
        rows = self.systems()
        if not rows:
            return "_هیچ سیستمی در بسته نیست._"
        out = ["| id | نام | موجودیت | گزارش | قابل authoring |",
               "|---|---|---|---|---|"]
        for row in rows:
            out.append("| `%s` | %s | %s | %s | %s |" % (
                row["id"], row["caption"] or "—", row["entities"],
                row["reports"],
                "بله" if row["authorable"] else "نه — بستهٔ selector ندارد"))
        return "\n".join(out)

    def _report_pending(self, task_dir, adir, role, log):
        from .states import ROLE_OUTPUTS
        rel = os.path.relpath(adir, self.repo_root)
        outputs = ROLE_OUTPUTS[role]
        missing = self._missing(task_dir, outputs["required"])
        log("منتظر نقش %s (attempt %s)." % (role, os.path.basename(adir)))
        if missing:
            log("  هنوز نوشته نشده: %s" % ", ".join(missing))
        log("  هنوز نوشته نشده: %s/result.yaml" % rel)
        log("  دستور کامل نقش: %s/prompt.md" % rel)

    def _prepare_attempt(self, task_dir, manifest, role, name, adir, provider):
        """The context package: exactly what the role is allowed to read."""
        system_id = (manifest.get("need") or {}).get("system")
        subs = {"TASK_DIR": os.path.relpath(task_dir, self.repo_root),
                "ATTEMPT_DIR": os.path.relpath(adir, self.repo_root),
                "PACK_DIR": self.pack_dir,
                "SYSTEM_ID": system_id or "<no system>",
                "SYSTEMS": self._systems_table(),
                "VOCABULARY": self._vocabulary_table(),
                "TASK_ID": manifest.get("id")}
        with open(os.path.join(adir, "prompt.md"), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(prompts.render(self.store, role, subs))
        with open(os.path.join(adir, "attempt.json"), "w", encoding="utf-8",
                  newline="\n") as fh:
            json.dump({"role": role, "provider": provider,
                       "startedAt": now(), "state": manifest.get("state")},
                      fh, ensure_ascii=False, indent=1)

        for source in _context_files(role):
            src = os.path.join(task_dir, source)
            if os.path.isfile(src):
                shutil.copyfile(src, os.path.join(adir, source))

        # The last rejection of this same role, so the next attempt does not
        # repeat it. This is the one file every prompt says to read first.
        rejection = self.store.read_text(task_dir, ".last-rejection-%s.md"
                                         % role)
        if rejection:
            with open(os.path.join(adir, "previous-rejection.md"), "w",
                      encoding="utf-8", newline="\n") as fh:
                fh.write(rejection)
        if role == "reviewer":
            verify_doc = self.store.read_text(task_dir, "verify.json")
            if verify_doc:
                with open(os.path.join(adir, "verify.json"), "w",
                          encoding="utf-8", newline="\n") as fh:
                    fh.write(verify_doc)

    # Tools a role needs and nothing more. A role reads the pack and writes
    # its own artifacts; it has no reason to run commands.
    DEFAULT_AGENT_TOOLS = "Read Write Edit Glob Grep"

    def _run_provider(self, provider_name, settings, role, adir, log):
        if provider_name != "claude":
            raise ManagerError("provider %r is not implemented"
                               % (provider_name,))
        command = settings.get("command") or "claude"
        with open(os.path.join(adir, "prompt.md"), encoding="utf-8") as fh:
            prompt = fh.read()

        argv = [command, "-p", prompt,
                "--permission-mode",
                settings.get("permissionMode") or "acceptEdits",
                "--allowedTools"]
        argv += (settings.get("allowedTools")
                 or self.DEFAULT_AGENT_TOOLS).split()
        model = (settings.get("model") or {})
        if isinstance(model, dict):
            model = model.get(role)
        if model:
            argv += ["--model", str(model)]

        before = self._tracked_changes()
        log("اجرای provider %s برای نقش %s …" % (provider_name, role))
        try:
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.run(
                argv, cwd=self.repo_root, capture_output=True, text=True,
                encoding="utf-8", errors="replace", env=env,
                timeout=int(settings.get("timeoutSeconds") or 900))
        except subprocess.TimeoutExpired:
            raise ManagerError(
                "provider %s برای نقش %s در مهلت تمام نشد. attempt باز مانده؛ "
                "یا مهلت را زیاد کن یا نقش را دستی بنویس."
                % (provider_name, role))
        except OSError as exc:
            raise ManagerError("provider %s اجرا نشد: %s"
                               % (provider_name, exc))
        with open(os.path.join(adir, "agent-transcript.log"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(proc.stdout or "")
            if proc.stderr:
                fh.write("\n--- stderr ---\n")
                fh.write(proc.stderr)
        if proc.returncode != 0:
            raise ManagerError(
                "provider %s با کد %d تمام شد؛ agent-transcript.log را ببین."
                % (provider_name, proc.returncode))

        # File ownership, enforced rather than requested: a role writes inside
        # its own task directory. Anything else it touched is reported here,
        # not discovered later in a diff nobody read.
        stray = self._stray_writes(before, adir)
        if stray:
            raise ManagerError(
                "نقش %s بیرون از پوشهٔ تسک نوشت: %s\n"
                "این transition انجام نشد. فایل‌ها را خودت بررسی کن — هیچ "
                "چیزی برگردانده نشده."
                % (role, "، ".join(sorted(stray)[:20])))

    def _tracked_changes(self):
        """`git status --porcelain` as a set, or None outside a repository."""
        try:
            # -z also turns off git's path quoting, so a Persian task
            # directory arrives as itself rather than as octal escapes.
            proc = subprocess.run(
                ["git", "status", "--porcelain", "-z"], cwd=self.repo_root,
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=60)
        except (OSError, subprocess.SubprocessError):
            return None
        if proc.returncode != 0:
            return None
        return {row[3:] for row in proc.stdout.split("\0") if len(row) > 3}

    def _stray_writes(self, before, adir):
        if before is None:
            return set()
        after = self._tracked_changes()
        if after is None:
            return set()
        task_rel = os.path.relpath(os.path.dirname(adir.rstrip(os.sep)),
                                   self.repo_root).replace(os.sep, "/")
        task_rel = task_rel.rsplit("/attempts", 1)[0] + "/"
        return {path for path in (after - before)
                if not path.startswith(task_rel)}

    def _record_rejection(self, task_dir, role, text):
        self.store.write_text(task_dir, ".last-rejection-%s.md" % role, text)

    # -- the run loop ------------------------------------------------------

    def run(self, task_id, log=print, max_iterations=RUN_MAX_ITERATIONS):
        """One iteration, one transition. Returns a contract exit code."""
        task_dir = self.store.task_dir_or_fail(task_id)
        lock_path = self.store.transition_lock_path(task_dir)
        self._reclaim_stale_lock(lock_path, log)

        progressed = False
        for _ in range(max_iterations):
            manifest = self.store.read_manifest(task_dir)
            state = manifest.get("state")
            gate = manifest.get("awaitingHuman")

            if gate and not str(gate.get("kind", "")).startswith("role:"):
                log("منتظر تو: %s" % gate.get("kind"))
                log("  پاسخ: python3 tools/manager.py answer %s --approve | "
                    "--reject --reason-file <f> | --clarify --file <f>"
                    % manifest["id"])
                return EXIT_AWAITING_HUMAN
            if state in RUN_STOPPED_STATES:
                blocker = manifest.get("blocker") or {}
                log("state=%s — %s" % (state, blocker.get("reason")
                                       or RUNBOOK.get(state, "")))
                return EXIT_STOPPED
            if state == "integrated":
                log("تمام شد — integrated")
                return EXIT_OK

            handler = getattr(self, "_step_%s" % state.replace("-", "_"), None)
            if handler is None:
                log("برای state=%s اتوماسیون ندارم. %s"
                    % (state, RUNBOOK.get(state, "")))
                return EXIT_STOPPED if progressed else EXIT_NO_PROGRESS

            self.store.write_lock(lock_path, {
                "task": manifest["id"], "fromState": state, "role": "manager"})
            try:
                outcome = handler(task_dir, manifest, log)
            except _BudgetExhausted as exc:
                self._block(task_dir, self.store.read_manifest(task_dir),
                            "budget-exhausted",
                            "بودجهٔ %s (حداکثر %s) تمام شد."
                            % (exc.key, exc.maximum))
                log("بودجهٔ %s تمام شد — تسک blocked شد." % exc.key)
                return EXIT_STOPPED
            finally:
                self.store.clear_lock(lock_path)

            if outcome == "wait":
                return EXIT_AWAITING_HUMAN
            if outcome == "stop":
                return EXIT_STOPPED
            progressed = True

        log("سقف %d تکرار رسید بدون رسیدن به حالت پایانی." % max_iterations)
        return EXIT_NO_PROGRESS

    def _reclaim_stale_lock(self, lock_path, log):
        lock = self.store.read_lock(lock_path)
        if not lock:
            return
        alive = _pid_alive(lock.get("pid"), lock.get("hostname"))
        if alive is True:
            raise ManagerError(
                "یک اجرای دیگر (pid %s) همین تسک را در دست دارد."
                % lock.get("pid"))
        if alive is None:
            raise ManagerError(
                "قفل روی ماشین دیگری نوشته شده و زنده بودنش قابل تشخیص نیست. "
                "اگر مطمئنی مرده: unlock <id> --reason \"...\" --force")
        log("قفل کهنه (pid %s) پس گرفته شد." % lock.get("pid"))
        self.store.clear_lock(lock_path)

    # -- one step per state ------------------------------------------------

    def _step_new(self, task_dir, manifest, log):
        result, manifest, attempt, adir = self._invoke_role(
            task_dir, manifest, "intake", log)
        if result is None:
            return "wait"
        outcome = result.get("outcome")
        if outcome == "needs_clarification":
            self._require(task_dir, ["questions.md"], "intake")
            self._open_gate(task_dir, manifest, GATE_CLARIFICATION,
                            "questions.md")
            return "wait"
        if outcome != "completed":
            self._block(task_dir, manifest, "intake-failed",
                        "Intake با outcome=%s برگشت." % outcome)
            return "stop"
        self._require(task_dir, ["proposed-task.md", "release-note.md"],
                      "intake")

        # The system intake settled, if it settled one. This is the only
        # channel for that decision, exactly like the architect's proposal.
        chosen = result.get("systemId")
        if chosen:
            row, candidates = self.resolve_system(chosen)
            if row is None:
                log("Intake سیستم %r را داد که یکتا نیست؛ نادیده گرفته شد."
                    % chosen)
            else:
                need = dict(manifest.get("need") or {})
                need["system"] = row["id"]
                manifest = self._set(task_dir, manifest, need=need)
                log("سیستم تعیین شد: %s (%s)" % (row["caption"], row["id"]))
        # The spec gate stands between a proposal and a plan: nothing is
        # designed against an unapproved spec.
        self._open_gate(task_dir, manifest, GATE_SPEC_APPROVAL,
                        "proposed-task.md")
        log("Intake تمام شد. گیت spec-approval باز است: proposed-task.md را "
            "ببین.")
        return "wait"

    def _step_architecture(self, task_dir, manifest, log):
        result, manifest, attempt, adir = self._invoke_role(
            task_dir, manifest, "architect", log)
        if result is None:
            return "wait"
        outcome = result.get("outcome")
        requested = result.get("requestedTransition")

        if outcome == "needs_clarification" or requested == "needs-clarification":
            self._require(task_dir, ["questions.md"], "architect")
            self._transition(task_dir, manifest, "needs-clarification")
            manifest = self.store.read_manifest(task_dir)
            self._open_gate(task_dir, manifest, GATE_CLARIFICATION,
                            "questions.md")
            return "wait"
        if requested == "needs-investigation":
            self._transition(task_dir, manifest, "needs-investigation")
            log("architect بررسی انسانی خواست: evidence.md را بنویس.")
            return "stop"
        if outcome != "completed" or requested != "ready":
            self._record_rejection(task_dir, "architect",
                                   "attempt %s با outcome=%s و "
                                   "requestedTransition=%s برگشت."
                                   % (attempt, outcome, requested))
            self._block(task_dir, manifest, "architect-failed",
                        "Architect به ready نرسید (outcome=%s)." % outcome)
            return "stop"

        proposal = result.get("proposal")
        problems = self._validate_proposal(proposal)
        if problems:
            text = ("پیشنهاد attempt %s رد شد:\n\n" % attempt
                    + "\n".join("- " + p for p in problems))
            self._record_rejection(task_dir, "architect", text)
            self.store.write_text(task_dir,
                                  "attempts/%s/proposal-rejection.md" % attempt,
                                  text)
            log("بلوک proposal معتبر نبود:")
            for p in problems:
                log("  - " + p)
            return "stop"

        clash = self.store.scope_conflict(manifest["id"],
                                          proposal["scope"]["allow"])
        if clash:
            self._block(task_dir, manifest, "scope-locked",
                        "این اشیاء در اختیار تسک %s (state=%s) هستند: %s"
                        % (clash["task"], clash["state"],
                           ", ".join(clash["entries"])))
            return "stop"

        self._require(task_dir, ["plan.md", "tests.md", "handoff.md"],
                      "architect")
        need = dict(manifest.get("need") or {})
        if proposal.get("system"):
            need["system"] = str(proposal["system"])
        self._transition(task_dir, manifest, "ready", extra={
            "scope": {"allow": list(proposal["scope"]["allow"]),
                      "deny": list(proposal["scope"].get("deny") or [])},
            "gates": list(proposal.get("gates")
                          or manifest.get("gates") or verify.GATES),
            "need": need,
        })
        log("نقشه پذیرفته شد. scope قفل شد: %s"
            % ", ".join(proposal["scope"]["allow"]))
        return "go"

    def _step_ready(self, task_dir, manifest, log):
        clash = self.store.scope_conflict(
            manifest["id"], (manifest.get("scope") or {}).get("allow"))
        if clash:
            self._block(task_dir, manifest, "scope-locked",
                        "اشیاء هدف در اختیار تسک %s هستند." % clash["task"])
            return "stop"
        self._transition(task_dir, manifest, "implementing")
        return "go"

    def _step_implementing(self, task_dir, manifest, log):
        result, manifest, attempt, adir = self._invoke_role(
            task_dir, manifest, "implementer", log)
        if result is None:
            return "wait"
        outcome = result.get("outcome")
        if outcome == "failed":
            # A self-reported failure is accepted, and it blames the plan.
            text = self.store.read_text(
                task_dir, "attempts/%s/failure.md" % attempt) or \
                "implementer attempt %s با outcome=failed برگشت." % attempt
            self._record_rejection(task_dir, "architect", text)
            self._transition(task_dir, manifest, "architecture",
                             note="implementer نقشه را رد کرد")
            log("implementer شکست را خودش گزارش کرد — برگشت به طراحی.")
            return "go"
        if outcome != "completed":
            self._block(task_dir, manifest, "implementer-%s" % outcome,
                        "implementer با outcome=%s برگشت." % outcome)
            return "stop"

        missing = self._missing(task_dir, ["change-batch.json",
                                          "implementation-report.md"])
        if missing:
            text = ("attempt %s تمام‌شده اعلام شد ولی این فایل‌ها نیستند: %s"
                    % (attempt, ", ".join(missing)))
            self._record_rejection(task_dir, "implementer", text)
            log(text)
            return "stop"

        # The manager verifies; the role's own word is not evidence.
        report = self.verify_task(manifest["id"])
        self.store.write_text(task_dir, "attempts/%s/verify.json" % attempt,
                              json.dumps(report, ensure_ascii=False, indent=1,
                                         sort_keys=True) + "\n")
        self.store.append_event(task_dir, manifest["id"], {
            "event": "verify.ran", "attempt": attempt,
            "passed": report["ok"],
            "errors": sum(g.get("errors", 0) for g in
                          report["summary"].values() if isinstance(g, dict))})
        if not report["ok"]:
            text = _verify_rejection(attempt, report)
            self._record_rejection(task_dir, "implementer", text)
            self.store.write_text(task_dir,
                                  "attempts/%s/verify-rejection.md" % attempt,
                                  text)
            log("verification رد شد:")
            for f in report["findings"][:12]:
                log("  - [%s] %s (%s)" % (f["gate"], f["message"], f["where"]))
            log("attempt بعدی implementer همین متن را در "
                "previous-rejection.md می‌بیند.")
            return "stop"

        batch_path = os.path.join(task_dir, "change-batch.json")
        with open(batch_path, encoding="utf-8") as fh:
            batch = json.load(fh)
        self._transition(task_dir, manifest, "review", extra={
            "batch": {"path": "change-batch.json",
                      "sha256": sha256_file(batch_path),
                      "commands": len(batch.get("changes") or ()),
                      "verifiedAt": report["checkedAt"],
                      "approvedSha256": None}})
        log("هر پنج گیت پاس شد — رفت به بازبینی.")
        return "go"

    def _step_review(self, task_dir, manifest, log):
        result, manifest, attempt, adir = self._invoke_role(
            task_dir, manifest, "reviewer", log)
        if result is None:
            return "wait"
        outcome = result.get("outcome")
        requested = result.get("requestedTransition")
        if outcome != "completed":
            self._block(task_dir, manifest, "reviewer-%s" % outcome,
                        "reviewer با outcome=%s برگشت." % outcome)
            return "stop"
        missing = self._missing(task_dir, ["review.md"])
        if missing:
            log("reviewer بدون review.md تمام‌شده اعلام کرد.")
            return "stop"

        if requested == "rejected":
            text = self.store.read_text(task_dir, "review.md") or ""
            route = result.get("route") or "implementer"
            self._record_rejection(task_dir,
                                   "architect" if route == "architect"
                                   else "implementer", text)
            self._transition(task_dir, manifest, "rejected",
                             note="reviewer رد کرد، route=%s" % route,
                             extra={"blocker": None})
            log("reviewer رد کرد — برگشت به %s." % route)
            return "go"
        if requested != "approved":
            log("requestedTransition=%r از reviewer معتبر نیست." % requested)
            return "stop"

        problems = self._validate_evidence(task_dir, result)
        if problems:
            text = ("داوری attempt %s ناقص بود:\n\n" % attempt
                    + "\n".join("- " + p for p in problems))
            self._record_rejection(task_dir, "reviewer", text)
            log("جدول شواهد کامل نبود:")
            for p in problems:
                log("  - " + p)
            return "stop"

        self._transition(task_dir, manifest, "approved")
        return "go"

    def _step_approved(self, task_dir, manifest, log):
        """Open the last gate: a human applies the batch, then says so."""
        report = self.verify_task(manifest["id"])
        if not report["ok"]:
            log("batch دیگر از گیت‌ها رد نمی‌شود؛ برگشت به پیاده‌سازی.")
            self._record_rejection(task_dir, "implementer",
                                   _verify_rejection("approved", report))
            self._transition(task_dir, manifest, "blocked", extra={
                "blocker": {"kind": "verification-drift",
                            "reason": "batch بعد از تأیید عوض شده است."}})
            return "stop"
        batch = dict(manifest.get("batch") or {})
        batch["sha256"] = report["batch"]["sha256"]
        batch["commands"] = report["batch"]["commands"]
        batch["verifiedAt"] = report["checkedAt"]
        manifest = self._transition(task_dir, manifest, "integrating",
                                    extra={"batch": batch})
        self._open_gate(task_dir, manifest, GATE_APPLY_APPROVAL,
                        "change-batch.json")
        applied_by = (self.config["repository"].get("integration") or {}).get(
            "appliedBy", "human")
        log("گیت apply-approval باز است:")
        log("  %s" % os.path.relpath(
            os.path.join(task_dir, "change-batch.json"), self.repo_root))
        log("  sha256 %s · %s فرمان" % (batch["sha256"][:16],
                                        batch["commands"]))
        if applied_by == "barsa-host":
            log("تأیید تو یعنی «اعمالش کن»؛ Manager خودش به Barsa.Ai.Host "
                "می‌دهد: python3 tools/manager.py answer %s --approve"
                % manifest["id"])
        else:
            log("این batch را خودت روی بارسا اعمال کن، بعد: "
                "python3 tools/manager.py answer %s --approve"
                % manifest["id"])
        return "wait"

    def _step_rejected(self, task_dir, manifest, log):
        self._transition(task_dir, manifest, "implementing")
        return "go"

    def _step_failed(self, task_dir, manifest, log):
        self._transition(task_dir, manifest, "architecture")
        return "go"

    def _step_needs_clarification(self, task_dir, manifest, log):
        self._open_gate(task_dir, manifest, GATE_CLARIFICATION,
                        "questions.md")
        return "wait"

    # -- validation helpers ------------------------------------------------

    def _missing(self, task_dir, names):
        return [n for n in names
                if not os.path.isfile(os.path.join(task_dir, n))]

    def _require(self, task_dir, names, role):
        missing = self._missing(task_dir, names)
        if missing:
            raise ManagerError(
                "نقش %s این فایل‌ها را ننوشته: %s" % (role, ", ".join(missing)))

    def _validate_proposal(self, proposal):
        problems = []
        if not isinstance(proposal, dict):
            return ["بلوک proposal وجود ندارد یا mapping نیست. بدون آن هیچ "
                    "پیشنهادی به Manager نمی‌رسد."]
        scope = proposal.get("scope")
        if not isinstance(scope, dict):
            problems.append("proposal.scope وجود ندارد.")
            return problems
        allow = scope.get("allow")
        if not isinstance(allow, list) or not allow:
            problems.append("proposal.scope.allow نباید خالی باشد.")
            allow = []
        types = {row.get("objectType")
                 for row in (self.contract.get("objectContracts") or ())}
        for entry in allow:
            if not isinstance(entry, str) or ":" not in entry:
                problems.append("عضو scope باید شکل objectType:selector داشته "
                                "باشد، نه %r" % (entry,))
                continue
            otype, selector = entry.split(":", 1)
            if otype not in types:
                problems.append("objectType %r در قرارداد نیست (%s)"
                                % (otype, entry))
            if not selector.startswith("#") and selector != "*":
                problems.append("selector باید با # شروع شود یا * باشد: %s"
                                % entry)
        gates = proposal.get("gates")
        if gates is not None:
            if not isinstance(gates, list):
                problems.append("proposal.gates باید آرایه باشد.")
            else:
                unknown = [g for g in gates if g not in verify.GATES]
                if unknown:
                    problems.append("گیت ناشناس: %s" % ", ".join(unknown))
        system = proposal.get("system")
        allowed = (self.config["repository"].get("systems") or {}).get(
            "allow") or []
        if system and allowed and str(system) not in [str(s) for s in allowed]:
            problems.append("سیستم %s در systems.allow نیست." % system)
        if system and self.selector_index(str(system)) is None:
            problems.append(
                "برای سیستم %s هیچ selector index وجود ندارد؛ بدون آن هیچ "
                "selectorی قابل اثبات نیست. اول: python3 "
                "tools/report_compiler.py --scope system=%s" % (system, system))
        return problems

    def _validate_evidence(self, task_dir, result):
        """Every AC must have a row; a verdict without a basis is not evidence."""
        problems = []
        evidence = result.get("evidence")
        if not isinstance(evidence, dict):
            return ["بلوک evidence وجود ندارد. داوری بدون جدول شواهد پذیرفته "
                    "نیست."]
        acceptance = evidence.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance:
            problems.append("evidence.acceptance خالی است.")
            acceptance = []
        covered = {str(row.get("ac")) for row in acceptance
                   if isinstance(row, dict)}
        task_text = self.store.read_text(task_dir, "task.md") or ""
        acs = _acceptance_ids(task_text)
        for ac in acs:
            if ac not in covered:
                problems.append("AC %s هیچ ردیفی در evidence.acceptance ندارد."
                                % ac)
        for row in acceptance:
            if not isinstance(row, dict):
                problems.append("ردیف evidence باید mapping باشد.")
                continue
            if not row.get("basis"):
                problems.append("ردیف %s بدون basis است؛ «به نظر درست است» "
                                "شاهد نیست." % row.get("ac"))
            if row.get("verdict") not in ("pass", "fail", "partial"):
                problems.append("verdict ردیف %s باید pass/fail/partial باشد."
                                % row.get("ac"))
            if row.get("verdict") == "fail":
                problems.append("ردیف %s verdict=fail دارد ولی داوری approved "
                                "است." % row.get("ac"))
        return problems

    # -- answer: the human gates ------------------------------------------

    def answer(self, task_id, approve=False, reject=False, clarify=None,
               reason=None, respec=False, route=None, log=print):
        task_dir = self.store.task_dir_or_fail(task_id)
        manifest = self.store.read_manifest(task_dir)
        gate = manifest.get("awaitingHuman") or {}
        kind = gate.get("kind")
        if not kind:
            raise ManagerError("این تسک منتظر هیچ پاسخی نیست (state=%s)."
                               % manifest.get("state"))
        if str(kind).startswith("role:"):
            raise ManagerError(
                "این تسک منتظر نقش %s است، نه منتظر تأیید. فایل‌های آن attempt "
                "را بنویس و run بزن." % kind.split(":", 1)[1])

        if kind == GATE_CLARIFICATION:
            if clarify is None:
                raise ManagerError("گیت clarification پاسخ متنی می‌خواهد: "
                                   "--clarify --file <path>")
            return self._answer_clarification(task_dir, manifest, clarify,
                                              respec, log)
        if kind == GATE_SPEC_APPROVAL:
            return self._answer_spec(task_dir, manifest, approve, reject,
                                     reason, log)
        if kind == GATE_APPLY_APPROVAL:
            return self._answer_apply(task_dir, manifest, approve, reject,
                                      reason, route, log)
        raise ManagerError("گیت ناشناس: %r" % (kind,))

    def _answer_clarification(self, task_dir, manifest, text, respec, log):
        events = self.store.read_events(task_dir)
        n = sum(1 for e in events if e.get("event") == "clarification.answered")
        request = self.store.read_text(task_dir, "request.md") or ""
        request += ("\n\n## Clarification %03d\n\n%s\n" % (n + 1, text.strip()))
        self.store.write_text(task_dir, "request.md", request)
        budget = dict(manifest.get("budget") or {})
        row = dict(budget.get("clarifications") or {"used": 0, "max": 0})
        row["used"] = row.get("used", 0) + 1
        budget["clarifications"] = row
        manifest = self._set(task_dir, manifest, awaitingHuman=None,
                             budget=budget)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "clarification.answered", "respec": bool(respec)})
        # A clarification spends no role budget: it is the human's turn, not a
        # failed attempt.
        if respec:
            target = "new"
            log("respec: spec از نو از Intake می‌گذرد.")
        else:
            target = ("architecture" if manifest.get("state")
                      in ("needs-clarification",) else manifest.get("state"))
        if manifest.get("state") == "needs-clarification":
            self._transition(task_dir, manifest, target)
        elif respec and manifest.get("state") == "new":
            pass  # already in new; the next run re-runs intake
        log("پاسخ ثبت شد. ادامه: python3 tools/manager.py run %s"
            % manifest["id"])
        return {"ok": True, "respec": bool(respec)}

    def _answer_spec(self, task_dir, manifest, approve, reject, reason, log):
        if reject:
            if not reason:
                raise ManagerError("رد spec دلیل اجباری دارد: --reason-file")
            self._record_rejection(task_dir, "intake", reason)
            manifest = self._set(task_dir, manifest, awaitingHuman=None)
            self.store.append_event(task_dir, manifest["id"], {
                "event": "gate.rejected", "gate": GATE_SPEC_APPROVAL})
            log("spec رد شد. attempt بعدی Intake دلیل را می‌بیند.")
            return {"ok": True, "rejected": True}
        if not approve:
            raise ManagerError("یکی از --approve یا --reject لازم است.")
        proposed = self.store.read_text(task_dir, "proposed-task.md")
        if not proposed:
            raise ManagerError("proposed-task.md وجود ندارد.")
        # Only the manager writes task.md, and only here: the spec becomes
        # official at the moment a human approves it, stamped with the hashes
        # it was approved at.
        self.store.write_text(task_dir, "task.md", proposed)
        request = self.store.read_text(task_dir, "request.md") or ""
        from .store import sha256_text
        spec = {"requestHash": sha256_text(request),
                "taskHash": sha256_text(proposed)}
        manifest = self._set(task_dir, manifest, awaitingHuman=None, spec=spec)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "gate.approved", "gate": GATE_SPEC_APPROVAL,
            "taskHash": spec["taskHash"][:16]})
        self._transition(task_dir, manifest, "architecture")
        log("spec تأیید شد و task.md مهر خورد. ادامه: run %s" % manifest["id"])
        return {"ok": True, "approved": True}

    def _answer_apply(self, task_dir, manifest, approve, reject, reason, route,
                      log):
        if reject:
            if not reason:
                raise ManagerError("رد اعمال دلیل اجباری دارد: --reason-file")
            target = "architecture" if route == "architect" else "implementing"
            self._record_rejection(
                task_dir, "architect" if route == "architect" else "implementer",
                reason)
            manifest = self._set(task_dir, manifest, awaitingHuman=None)
            self.store.append_event(task_dir, manifest["id"], {
                "event": "gate.rejected", "gate": GATE_APPLY_APPROVAL,
                "route": route or "implementer"})
            self._transition(task_dir, manifest, target)
            log("اعمال رد شد — برگشت به %s." % target)
            return {"ok": True, "rejected": True, "route": route}
        if not approve:
            raise ManagerError("یکی از --approve یا --reject لازم است.")

        # Whoever applies it, the same proof comes first: this is still the
        # batch the gate opened on, and it still passes every gate.
        batch = dict(manifest.get("batch") or {})
        report = self.verify_task(manifest["id"])
        if not report["ok"]:
            raise ManagerError(
                "batch دیگر از گیت‌ها رد نمی‌شود، پس تسک بسته نمی‌شود. "
                "verify.json را ببین.")
        if batch.get("sha256") and report["batch"]["sha256"] != batch["sha256"]:
            raise ManagerError(
                "batch بعد از باز شدن گیت عوض شده است (%s → %s). تأیید قبلی "
                "باطل است؛ run بزن تا دوباره داوری شود."
                % (batch["sha256"][:16], report["batch"]["sha256"][:16]))

        applied_by = (self.config["repository"].get("integration") or {}).get(
            "appliedBy", "human")
        if applied_by == "barsa-host":
            batch = self._apply_through_host(task_dir, manifest, batch, log)
        else:
            # `--approve` means "I applied it". There is nothing further to
            # prove from here: this repository cannot see the installation.
            batch["appliedBy"] = "human"

        batch["approvedSha256"] = report["batch"]["sha256"]
        batch["appliedAt"] = now()
        manifest = self._set(task_dir, manifest, awaitingHuman=None,
                             batch=batch)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "gate.approved", "gate": GATE_APPLY_APPROVAL,
            "appliedBy": batch.get("appliedBy"),
            "planId": batch.get("planId"),
            "sha256": batch["approvedSha256"][:16]})
        self._transition(task_dir, manifest, "integrated")
        log("تسک بسته شد. قفل scope آزاد شد.")
        return {"ok": True, "integrated": True,
                "appliedBy": batch.get("appliedBy"),
                "planId": batch.get("planId")}

    def host_client(self):
        """The host client, from connection.yaml when it is there."""
        settings = connection_mod.host_settings(self.config, self.connection)
        client = barsa_host.HostClient(
            prefix=settings.get("prefix"),
            api_key=os.environ.get(settings.get("apiKeyEnv")
                                   or "BARSA_AI_HOST_KEY"),
            timeout=int(settings.get("timeoutSeconds") or 180))
        return client, settings

    def _apply_through_host(self, task_dir, manifest, batch, log):
        """Hand the batch to Barsa.Ai.Host and wait for a real verdict.

        The task closes on the host's own answer. If the host refuses, or
        finishes in any state but applied, nothing is closed: the gate stays
        open and the refusal is written down where the next role will read it.
        """
        client, settings = self.host_client()
        batch_path = os.path.join(task_dir, "change-batch.json")
        with open(batch_path, encoding="utf-8") as fh:
            document = json.load(fh)

        log("اعمال از طریق Barsa.Ai.Host: %s" % client.prefix)
        try:
            health = client.health()
        except barsa_host.HostError as exc:
            raise ManagerError("host در دسترس نیست.\n%s" % exc.detail())
        database = health.get("database") or {}
        if database:
            log("  دیتابیس: %s / %s" % (database.get("server"),
                                        database.get("name")))
        log("  اثر انگشت runtime: %s" % health.get("runtimeFingerprint"))

        # The one check worth stopping everything for: is this the Barsa we
        # said we were pointed at?
        ok, message = connection_mod.check_database(self.connection, health)
        log("  %s" % message)
        if not ok:
            self.store.append_event(task_dir, manifest["id"], {
                "event": "apply.refused", "reason": "database-mismatch"})
            raise ManagerError(
                "host به دیتابیسی وصل است که connection.yaml انتظارش را "
                "ندارد، پس هیچ چیزی اعمال نشد.\n  %s\n"
                "یا host را به دیتابیس درست ببر، یا connection.yaml را "
                "اصلاح کن. این گیت برای همین روز نوشته شده." % message)

        try:
            outcome = client.plan_and_apply(
                document,
                require_clean=settings.get("requireCleanPlan", True) is not False,
                max_wait=int(settings.get("maxWaitSeconds") or 600),
                log=lambda m: log("  " + m))
        except barsa_host.HostError as exc:
            self._record_rejection(task_dir, "implementer",
                                   _host_rejection(exc))
            self.store.write_text(task_dir, "apply-failure.md",
                                  _host_rejection(exc))
            self.store.append_event(task_dir, manifest["id"], {
                "event": "apply.failed", "route": exc.route,
                "status": exc.status})
            raise ManagerError(
                "بارسا این batch را اعمال نکرد، پس تسک بسته نشد. گیت باز "
                "مانده و دلیل در apply-failure.md است.\n%s" % exc.detail())

        self.store.write_text(
            task_dir, "apply-result.json",
            json.dumps(outcome, ensure_ascii=False, indent=1,
                       sort_keys=True) + "\n")
        plan = outcome["plan"]
        batch["appliedBy"] = "barsa-host"
        batch["planId"] = plan.get("planId")
        batch["hostPrefix"] = client.prefix
        batch["runtimeFingerprint"] = (
            (outcome["apply"].get("runtimeFingerprint")
             or health.get("runtimeFingerprint")))
        batch["hostState"] = outcome["status"].get("state")
        log("بارسا اعمال کرد. plan %s، state %s."
            % (batch["planId"], batch["hostState"]))
        return batch

    # -- the synchronous side commands ------------------------------------

    def cancel(self, task_id, reason, abandon=False, log=print):
        if not reason:
            raise ManagerError("دلیل اجباری است: --reason-file")
        task_dir = self.store.task_dir_or_fail(task_id)
        manifest = self.store.read_manifest(task_dir)
        target = "abandoned" if abandon else "cancelled"
        state = manifest.get("state")
        if state in LOCK_RELEASED_STATES:
            raise ManagerError("تسک از قبل در حالت %s است." % state)
        # Cancelling from a mid-flight state goes through blocked, exactly as
        # the transition table allows -- no new edges are invented here.
        if target not in TASK_TRANSITIONS.get(state, ()):
            manifest = self._block(task_dir, manifest,
                                   "cancel-requested", reason)
        self.store.write_text(task_dir, "cancel-reason.md", reason)
        self._transition(task_dir, manifest, target, note=reason)
        log("تسک %s شد و قفل‌هایش آزاد شدند." % target)
        return {"ok": True, "state": target}

    def void(self, task_id, reason, log=print):
        """Undo this task's last transition, with the reason on record."""
        if not reason:
            raise ManagerError("دلیل اجباری است: --reason-file")
        task_dir = self.store.task_dir_or_fail(task_id)
        manifest = self.store.read_manifest(task_dir)
        previous = manifest.get("previousState")
        if not previous:
            raise ManagerError("این تسک transition قبلی ندارد.")
        if manifest.get("state") in ("integrated", "cancelled", "abandoned"):
            raise ManagerError(
                "حالت پایانی void نمی‌شود: %s" % manifest.get("state"))
        self.store.write_text(task_dir, "void-reason.md", reason)
        manifest = dict(manifest)
        state = manifest["state"]
        manifest.update({"state": previous, "previousState": None,
                         "stateSince": now(), "awaitingHuman": None})
        self.store.write_manifest(task_dir, manifest)
        self.store.append_event(task_dir, manifest["id"], {
            "event": "transition.voided", "from": state, "to": previous,
            "reason": reason})
        self.render_board()
        log("برگشت به %s." % previous)
        return {"ok": True, "state": previous}

    def unlock(self, task_id, reason, force=False, log=print):
        if not reason:
            raise ManagerError("دلیل اجباری است: --reason-file")
        task_dir = self.store.task_dir_or_fail(task_id)
        path = self.store.transition_lock_path(task_dir)
        lock = self.store.read_lock(path)
        if not lock:
            raise ManagerError("قفلی روی این تسک نیست.")
        alive = _pid_alive(lock.get("pid"), lock.get("hostname"))
        if alive is True:
            raise ManagerError("pid %s روی همین ماشین زنده است؛ unlock رد شد."
                               % lock.get("pid"))
        if alive is None and not force:
            raise ManagerError(
                "زنده بودن قفل قابل تشخیص نیست (ماشین دیگر). اگر مطمئنی مرده: "
                "--force")
        self.store.clear_lock(path)
        self.store.append_event(task_dir, task_id, {
            "event": "lock.released", "reason": reason, "forced": bool(force)})
        log("قفل آزاد شد. manifest و تاریخچه دست‌نخورده‌اند.")
        return {"ok": True}

    def capabilities(self):
        from . import (MANAGER_CONTRACT_NAME, MANAGER_CONTRACT_VERSION,
                       MANAGER_VERSION, PROTOCOL_VERSION)
        return {
            "contract": MANAGER_CONTRACT_NAME,
            "contractVersion": MANAGER_CONTRACT_VERSION,
            "managerVersion": MANAGER_VERSION,
            "protocolVersion": PROTOCOL_VERSION,
            "domain": "barsa-objects",
            "needKinds": list(NEED_KINDS),
            "verificationGates": list(verify.GATES),
            "capabilities": {
                "status": {"base": True, "verify": True, "review": True,
                           "health": True},
                "taskStatus": True,
                "events": True,
                "artifact": True,
                "run": True,
                "answer": {"approve": True, "reject": True, "clarify": True,
                           "respec": True},
                "importIssue": True,
                "cancel": True,
                "abandon": True,
                "void": True,
                # There is no git here, so there is nothing to rebase.
                "rebase": False,
                "unlock": True,
            },
        }


def _host_rejection(exc):
    return "\n".join([
        "# بارسا این batch را اعمال نکرد",
        "",
        "این متن از خودِ host آمده، نه از این ابزار.",
        "",
        "```text",
        exc.detail(),
        "```",
        "",
        "اگر دلیلش یک خطای واقعی در batch است، اصلاحش کن. اگر host می‌گوید "
        "plan تمیز اعمال نمی‌شود، نقشه را بازبینی کن — این یک گیت نیست که "
        "دورش زد.",
        "",
    ])


class _BudgetExhausted(Exception):
    def __init__(self, key, maximum):
        super().__init__("budget %s exhausted (max %s)" % (key, maximum))
        self.key = key
        self.maximum = maximum


# -- small helpers ---------------------------------------------------------

def _context_files(role):
    return {
        "intake": ["request.md"],
        "architect": ["task.md", "request.md", "evidence.md"],
        "implementer": ["task.md", "plan.md", "tests.md", "handoff.md"],
        "reviewer": ["task.md", "tests.md", "plan.md", "review.md",
                     "implementation-report.md", "change-batch.json"],
    }[role]


def _request_doc(task_id, text, source):
    lines = ["# Request — task %s" % task_id, ""]
    if source:
        lines += ["> منبع: %s %s" % (source.get("system") or "",
                                     source.get("externalId") or ""), ""]
        if source.get("url"):
            lines += ["> %s" % source["url"], ""]
    lines.append(text.strip())
    lines.append("")
    return "\n".join(lines)


def _first_line(text):
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return "(بی‌عنوان)"


def _acceptance_ids(text):
    import re
    return sorted(set(re.findall(r"\bAC-\d+", text)))


def _front_matter(text):
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    from . import yamlite
    try:
        return yamlite.loads(parts[1])
    except yamlite.YamlError:
        return {}


def _verify_status(manifest, verify_doc):
    gates = manifest.get("gates") or []
    doc = verify_doc or {}
    summary = doc.get("summary") or {}
    disabled = [{"gate": g, "reason": "در repository.yaml فعال نیست"}
                for g in verify.GATES if g not in gates]
    return {
        "gates": list(gates),
        "disabled": disabled,
        "passed": summary.get("passed"),
        "checkedAt": doc.get("checkedAt"),
        "perGate": {k: v for k, v in summary.items() if isinstance(v, dict)},
        "findings": doc.get("findings") or [],
        # The console's VerifyStatus shape, so an unmodified BarsaAgent still
        # renders something meaningful for a domain it was not written for.
        "build": [], "test": [], "lint": list(gates),
    }


def _verify_rejection(attempt, report):
    lines = ["# چرا attempt %s رد شد" % attempt, "",
             "verification مستقل Manager این موارد را پیدا کرد. متن "
             "`result.yaml` در این تصمیم نقشی ندارد.", ""]
    for gate, row in sorted((report.get("summary") or {}).items()):
        if isinstance(row, dict) and not row.get("passed"):
            lines.append("## گیت %s — %d خطا، %d هشدار"
                         % (gate, row.get("errors", 0), row.get("warnings", 0)))
            lines.append("")
            for f in report["findings"]:
                if f["gate"] != gate:
                    continue
                lines.append("- **%s** — %s" % (f.get("where") or "-",
                                                f["message"]))
                if f.get("hint"):
                    lines.append("  - %s" % f["hint"])
            lines.append("")
    lines.append("همان اشتباه را تکرار نکن.")
    lines.append("")
    return "\n".join(lines)


def _pid_alive(pid, hostname):
    """True, False, or None for 'cannot tell' -- never a guess."""
    if not pid:
        return None
    import socket
    try:
        here = socket.gethostname()
    except Exception:
        here = None
    if hostname and here and hostname != here:
        return None
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return None
