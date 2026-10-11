"""`.agent-work/` — the source of truth on disk.

Every write goes through here, and every write is verified by reading it back.
A manifest that silently failed to save is worse than a crash: the board would
show a state the store does not hold.

Nothing outside `.agent-work/` is ever written by this module.
"""

import datetime
import hashlib
import json
import os
import re

from . import yamlite
from .states import LOCK_RELEASED_STATES

SCHEMA_VERSION = 1
WORK_DIRNAME = ".agent-work"
TRANSITION_LOCK = ".transition.lock"
MANAGER_LOCK = ".manager.lock"


class StoreError(Exception):
    """The store refused a write, or found itself inconsistent."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# A slug may hold Persian letters -- real tasks are named in Persian -- but
# never a path separator or a dot segment.
_SLUG_OK = re.compile(r"^[\w؀-ۿ][\w؀-ۿ-]*$", re.UNICODE)


def assert_safe_segment(value, what):
    if not isinstance(value, str) or not _SLUG_OK.match(value):
        raise StoreError("%s is not a safe path segment: %r" % (what, value))
    if ".." in value or "/" in value or "\\" in value:
        raise StoreError("%s must not traverse: %r" % (what, value))
    return value


class Store:
    def __init__(self, root):
        self.repo_root = os.path.abspath(root)
        self.work = os.path.join(self.repo_root, WORK_DIRNAME)
        self.tasks_dir = os.path.join(self.work, "tasks")
        self.config_dir = os.path.join(self.work, "config")
        self.logs_dir = os.path.join(self.work, "logs")
        self.board_path = os.path.join(self.work, "BOARD.md")

    # -- layout ------------------------------------------------------------

    def ensure(self):
        for path in (self.work, self.tasks_dir, self.config_dir, self.logs_dir,
                     os.path.join(self.config_dir, "prompts")):
            os.makedirs(path, exist_ok=True)

    def task_dirs(self):
        if not os.path.isdir(self.tasks_dir):
            return []
        out = []
        for name in sorted(os.listdir(self.tasks_dir)):
            full = os.path.join(self.tasks_dir, name)
            if os.path.isdir(full) and os.path.isfile(
                    os.path.join(full, "manifest.yaml")):
                out.append(full)
        return out

    def find_task(self, task_id):
        for path in self.task_dirs():
            if os.path.basename(path).split("-", 1)[0] == str(task_id):
                return path
        return None

    def task_dir_or_fail(self, task_id):
        path = self.find_task(task_id)
        if path is None:
            raise StoreError("no task %s under %s"
                             % (task_id, _rel(self.repo_root, self.tasks_dir)))
        return path

    def next_id(self):
        used = []
        for path in self.task_dirs():
            head = os.path.basename(path).split("-", 1)[0]
            if head.isdigit():
                used.append(int(head))
        return "%04d" % ((max(used) + 1) if used else 1)

    def create_task_dir(self, task_id, slug):
        assert_safe_segment(slug, "slug")
        if not re.fullmatch(r"\d{4,6}", str(task_id)):
            raise StoreError("task id must be 4-6 digits: %r" % (task_id,))
        if self.find_task(task_id) is not None:
            raise StoreError("task %s already exists" % task_id)
        path = os.path.join(self.tasks_dir, "%s-%s" % (task_id, slug))
        os.makedirs(os.path.join(path, "attempts"), exist_ok=False)
        return path

    # -- reading and writing files ----------------------------------------

    def read_text(self, task_dir, rel):
        path = self.resolve_in_task(task_dir, rel)
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def write_text(self, task_dir, rel, text):
        path = self.resolve_in_task(task_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _atomic_write(path, text)
        with open(path, encoding="utf-8") as fh:
            if fh.read() != text:
                raise StoreError("read-after-write mismatch: %s" % rel)
        return path

    def resolve_in_task(self, task_dir, rel):
        """Resolve a task-relative path, refusing traversal."""
        if os.path.isabs(rel):
            raise StoreError("artifact path must be relative: %r" % rel)
        full = os.path.normpath(os.path.join(task_dir, rel))
        base = os.path.normpath(task_dir)
        if full != base and not full.startswith(base + os.sep):
            raise StoreError("artifact path escapes the task directory: %r"
                             % rel)
        return full

    # -- manifest ----------------------------------------------------------

    def read_manifest(self, task_dir):
        path = os.path.join(task_dir, "manifest.yaml")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        try:
            doc = yamlite.loads(text)
        except yamlite.YamlError as exc:
            raise StoreError("%s is malformed: %s"
                             % (_rel(self.repo_root, path), exc))
        if doc.get("schemaVersion") != SCHEMA_VERSION:
            raise StoreError("%s has schemaVersion %r, expected %d"
                             % (_rel(self.repo_root, path),
                                doc.get("schemaVersion"), SCHEMA_VERSION))
        return doc

    def write_manifest(self, task_dir, manifest):
        """Write it, read it back, and compare semantically before returning."""
        text = yamlite.dumps(manifest)
        path = os.path.join(task_dir, "manifest.yaml")
        _atomic_write(path, text)
        back = self.read_manifest(task_dir)
        if back != manifest:
            raise StoreError(
                "manifest did not survive the round trip; nothing may rely on "
                "it now. wrote %r, read %r" % (manifest, back))
        return path

    # -- events ------------------------------------------------------------

    def append_event(self, task_dir, task_id, event):
        row = {"at": now(), "task": str(task_id)}
        row.update(event)
        path = os.path.join(task_dir, "events.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row

    def read_events(self, task_dir):
        path = os.path.join(task_dir, "events.jsonl")
        if not os.path.isfile(path):
            return []
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    rows.append({"error": "unparsable event line",
                                 "raw": line[:200]})
        return rows

    # -- attempts ----------------------------------------------------------

    def attempts(self, task_dir):
        base = os.path.join(task_dir, "attempts")
        if not os.path.isdir(base):
            return []
        return [name for name in sorted(os.listdir(base))
                if re.fullmatch(r"\d{3}", name)
                and os.path.isdir(os.path.join(base, name))]

    def next_attempt(self, task_dir, role):
        existing = self.attempts(task_dir)
        n = (int(existing[-1]) + 1) if existing else 1
        name = "%03d" % n
        path = os.path.join(task_dir, "attempts", name)
        os.makedirs(path, exist_ok=False)
        return name, path

    def read_result(self, task_dir, attempt):
        path = os.path.join(task_dir, "attempts", attempt, "result.yaml")
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        try:
            return yamlite.loads(text)
        except yamlite.YamlError as exc:
            raise StoreError("attempts/%s/result.yaml is malformed: %s"
                             % (attempt, exc))

    # -- locks -------------------------------------------------------------

    def transition_lock_path(self, task_dir):
        return os.path.join(task_dir, TRANSITION_LOCK)

    def read_lock(self, path):
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                return json.loads(fh.read())
        except ValueError:
            return {"malformed": True}

    def write_lock(self, path, payload):
        row = dict(payload)
        row.setdefault("pid", os.getpid())
        row.setdefault("startedAt", now())
        row.setdefault("hostname", _hostname())
        _atomic_write(path, json.dumps(row, ensure_ascii=False,
                                       sort_keys=True) + "\n")
        return row

    def clear_lock(self, path):
        if os.path.isfile(path):
            os.remove(path)

    def manager_lock_path(self):
        return os.path.join(self.work, MANAGER_LOCK)

    # -- scope locks -------------------------------------------------------

    def scope_conflict(self, task_id, entries):
        """Is any of these scope entries already held by a live task?

        A scope entry here is a Barsa object, `objectType:selector` -- the
        analogue of a file path in a code workflow. Two tasks editing the same
        report would produce two change batches whose outcome depends on who
        applied first, so the second one waits.
        """
        wanted = set(entries or ())
        if not wanted:
            return None
        for path in self.task_dirs():
            manifest = self.read_manifest(path)
            if str(manifest.get("id")) == str(task_id):
                continue
            if manifest.get("state") in LOCK_RELEASED_STATES:
                continue
            held = set((manifest.get("scope") or {}).get("allow") or ())
            clash = wanted & held
            if clash:
                return {"task": manifest.get("id"),
                        "state": manifest.get("state"),
                        "entries": sorted(clash)}
        return None


def _atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _hostname():
    try:
        import socket
        return socket.gethostname()
    except Exception:
        return None


def _rel(root, path):
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path
