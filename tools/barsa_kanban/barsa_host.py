"""A client for Barsa.Ai.Host — the door a change batch actually goes through.

`Barsa.Ai.Host.exe` is an HTTP listener that fronts the semantic write path.
Everything below was recovered from that assembly's own IL -- the route
strings, the header name, the request and response keys -- not guessed:

    GET  /health                     is the host up, and against which database
    GET  /systems                    the systems it can see
    POST /lint          <batch>      the structural linter, server side
    POST /plan          <batch>      -> planId + a disposition
    POST /apply         {planId}     -> applies that plan
    GET  /apply-status  ?planId=     -> ready|applying|applied|faulted|unknown

    header  X-Barsa-Ai-Key
    prefix  http://127.0.0.1:17840/   (AiHost.HttpPrefix)

A plan lives in the host process (`PlanStore`), so a plan built by one host is
not applicable by another: "Plan is not available in this Host process. Build
the plan again." That is why apply always re-plans here rather than reusing a
planId from an earlier session.

**How much of this is confirmed:** the routes, the header and the payload keys
were read out of the binary, and later checked against the Host's own API
reference (`startup/host-api.fa.md`), which corrected the `/apply-status`
state set. No real host has answered this client yet: it is tested against a
stub implementing the same contract (`tools/test_kanban_host.py`). The first
real run may still find something this reconstruction has wrong -- treat a
mismatch as a finding about this file, not as a reason to loosen a gate.

One place this client is deliberately stricter than the Host: its reference
says plan diagnostics are non-blocking and a parsed plan may enter Apply
anyway. `require_clean` refuses that by default. That is our policy, not the
Host's rule, and `requireCleanPlan: false` turns it off.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_PREFIX = "http://127.0.0.1:17840/"
API_KEY_HEADER = "X-Barsa-Ai-Key"
CONTENT_TYPE = "application/json; charset=utf-8"

# The states /apply-status reports, from the Host's own API reference:
#
#   ready | applying | applied | faulted | unknown
#
# An earlier version of this file guessed `failed`/`completed`/`error` from
# the binary's strings and had no `faulted` at all, so a genuinely failed
# apply looked like one still running and was polled until the timeout.
#
# `unknown` is the dangerous one: the Host uses it when it cannot prove what
# the previous run did, and its reference says an automatic re-apply is
# forbidden in that state. It is terminal here for exactly that reason -- a
# retry is a decision for a person with the Host's log in front of them.
NON_TERMINAL_STATES = ("ready", "applying")
SUCCESS_STATES = ("applied",)
FAILURE_STATES = ("faulted",)
UNPROVABLE_STATES = ("unknown",)


class HostError(Exception):
    """The host refused, or could not be reached. Never retried silently."""

    def __init__(self, message, status=None, body=None, route=None):
        super().__init__(message)
        self.status = status
        self.body = body
        self.route = route

    def detail(self):
        rows = [str(self)]
        if self.route:
            rows.append("route: %s" % self.route)
        if self.status is not None:
            rows.append("HTTP %s" % self.status)
        if self.body:
            rows.append(str(self.body)[:800])
        return "\n".join(rows)


class HostClient:
    def __init__(self, prefix=None, api_key=None, timeout=180):
        self.prefix = (prefix or DEFAULT_PREFIX).rstrip("/") + "/"
        self.api_key = api_key
        self.timeout = timeout

    # -- the routes --------------------------------------------------------

    def health(self):
        return self._call("GET", "health")

    @staticmethod
    def profile_mismatch(health):
        """The host's semantic profile against the one we author for.

        Observed on a live 4.1.203 host: /health reports
        runtimeFingerprint.semanticProfileVersion, and every batch this
        repository writes declares profileVersion. If the two ever disagree,
        every batch is addressed to a contract the host no longer speaks --
        and the five local gates cannot see that, because they validate
        against the profile compiled into this repository, not the one
        running. Returns (ours, theirs) on a mismatch, or None.
        """
        from barsa_extractor.change_batch import PROFILE_VERSION
        finger = (health or {}).get("runtimeFingerprint")
        if not isinstance(finger, dict):
            return None          # nothing to compare, so no disagreement
        theirs = finger.get("semanticProfileVersion")
        if theirs is None:
            return None          # not reported is not a disagreement
        try:
            theirs = int(theirs)
        except (TypeError, ValueError):
            return (PROFILE_VERSION, theirs)
        if theirs != PROFILE_VERSION:
            return (PROFILE_VERSION, theirs)
        return None

    def systems(self):
        """The host's systems, with every id carried as a string.

        The host answers `id` as a JSON number, and a real one is
        1011413550000000100 -- a hundred times past 2**53, where a double
        stops being able to hold consecutive integers. Python reads it
        exactly, so nothing here is wrong today, but the moment such a
        number is handed to a JSON parser backed by doubles (every browser,
        so this console's own UI) it silently becomes
        1011413550000000128: a different system, with no error anywhere.

        Coercing here, at the one place host systems enter this codebase,
        means that value can never leave as a number.
        """
        payload = self._call("GET", "systems")
        for row in (payload.get("systems") or ()):
            if isinstance(row, dict) and "id" in row:
                row["id"] = str(row["id"])
        return payload

    def lint(self, batch):
        return self._call("POST", "lint", body=batch)

    def plan(self, batch, compact=True):
        route = "plan?compact=true" if compact else "plan"
        return self._call("POST", route, body=batch)

    def apply(self, plan_id, reference_semantic_file=None):
        body = {"planId": plan_id}
        if reference_semantic_file:
            body["referenceSemanticFile"] = reference_semantic_file
        return self._call("POST", "apply", body=body)

    def apply_status(self, plan_id):
        return self._call("GET", "apply-status?planId=%s"
                          % urllib.parse.quote(str(plan_id)))

    # -- the sequence ------------------------------------------------------

    def plan_and_apply(self, batch, require_clean=True, reference=None,
                       poll_seconds=2, max_wait=600, log=None):
        """Plan, check the disposition, apply, and wait for a real verdict.

        Returns {plan, apply, status, applied}. Raises HostError rather than
        returning a half-answer: a batch that was partially applied is a thing
        someone has to know about, not a value to branch on quietly.
        """
        say = log or (lambda _m: None)

        plan = self.plan(batch)
        plan_id = plan.get("planId")
        if not plan_id:
            raise HostError("the host returned no planId", body=plan,
                            route="plan")
        say("plan %s: %s command(s), %s error(s)"
            % (plan_id, plan.get("commandCount"), plan.get("errorCount")))

        if plan.get("isValid") is False:
            raise HostError(
                "the host rejected the batch at plan time; nothing was "
                "applied", body=_diagnostics(plan), route="plan")
        if require_clean and plan.get("canApplyCleanly") is False:
            raise HostError(
                "the host says this plan cannot be applied cleanly "
                "(canApplyAny=%s, canApplyAll=%s). Nothing was applied; set "
                "integration.host.requireCleanPlan to false only if a partial "
                "apply is really what you want."
                % (plan.get("canApplyAny"), plan.get("canApplyAll")),
                body=_diagnostics(plan), route="plan")

        applied = self.apply(plan_id, reference)
        if str(applied.get("status", "")).lower() == "rejected":
            raise HostError("the host rejected the apply",
                            body=applied, route="apply")
        say("apply accepted; waiting for the host to finish")

        status = self.wait(plan_id, poll_seconds, max_wait, say)
        state = str(status.get("state", "")).lower()
        if state in UNPROVABLE_STATES:
            raise HostError(
                "the host reports state 'unknown': it cannot prove what the "
                "previous apply did. Do NOT re-apply automatically -- read "
                "the Host log for plan %s and decide by hand." % plan_id,
                body={"status": status, "apply": applied},
                route="apply-status")
        if state not in SUCCESS_STATES:
            raise HostError(
                "the host finished in state %r" % state,
                body={"status": status, "apply": applied}, route="apply-status")
        return {"plan": plan, "apply": applied, "status": status,
                "applied": True}

    def wait(self, plan_id, poll_seconds=2, max_wait=600, log=None):
        say = log or (lambda _m: None)
        waited = 0.0
        last = None
        while waited <= max_wait:
            last = self.apply_status(plan_id)
            state = str(last.get("state", "")).lower()
            # Anything the reference does not list as in-flight is terminal.
            # Treating an unrecognised state as "keep waiting" is how a
            # failure turns into a timeout.
            if state and state not in NON_TERMINAL_STATES:
                return last
            say("  state=%s …" % (state or "—"))
            time.sleep(poll_seconds)
            waited += poll_seconds
        raise HostError(
            "the host did not reach a terminal state within %ds. It may still "
            "be applying -- check /apply-status for plan %s before doing "
            "anything else." % (max_wait, plan_id), body=last,
            route="apply-status")

    # -- transport ---------------------------------------------------------

    def _call(self, method, route, body=None):
        url = self.prefix + route
        data = None
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers[API_KEY_HEADER] = self.api_key
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = CONTENT_TYPE
        request = urllib.request.Request(url, data=data, headers=headers,
                                         method=method)
        try:
            # No proxy: the host is local, and a proxy in the environment
            # would silently send a change batch somewhere else.
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8", "replace")
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            if exc.code == 401:
                raise HostError(
                    "the host refused the key. Set the environment variable "
                    "named by host.apiKeyEnv in connection.yaml to the value "
                    "of AiHost.ApiKey.", status=401, body=raw, route=route)
            raise HostError("the host returned an error", status=exc.code,
                            body=raw, route=route)
        except urllib.error.URLError as exc:
            raise HostError(
                "cannot reach Barsa.Ai.Host at %s (%s). Start the host, or "
                "correct host.prefix in .agent-work/config/connection.yaml."
                % (self.prefix, exc.reason),
                route=route)
        try:
            return json.loads(raw) if raw.strip() else {}
        except ValueError:
            raise HostError("the host did not return JSON", status=status,
                            body=raw[:500], route=route)


def from_config(config, env=None):
    """Build a client from `integration.host`, or None when not configured."""
    env = env if env is not None else os.environ
    integration = (config["repository"].get("integration") or {})
    host = integration.get("host") or {}
    key_env = host.get("apiKeyEnv") or "BARSA_AI_HOST_KEY"
    return HostClient(prefix=host.get("prefix"),
                      api_key=env.get(key_env),
                      timeout=int(host.get("timeoutSeconds") or 180)), host


def _diagnostics(plan):
    """The part of a plan response a human needs when it is refused."""
    diagnostics = plan.get("diagnostics") or {}
    return {"planId": plan.get("planId"),
            "isValid": plan.get("isValid"),
            "canApplyCleanly": plan.get("canApplyCleanly"),
            "canApplyAny": plan.get("canApplyAny"),
            "canApplyAll": plan.get("canApplyAll"),
            "hasBatchFatalError": plan.get("hasBatchFatalError"),
            "hasCommandLocalErrors": plan.get("hasCommandLocalErrors"),
            "errorCount": plan.get("errorCount"),
            "summary": plan.get("summary"),
            "diagnostics": diagnostics.get("items") or diagnostics}
