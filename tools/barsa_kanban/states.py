"""The state machine, lifted from the BarsaAgent workflow unchanged.

The states and edges are the same ones that workflow proved out; what moves
along them is a Barsa change, not an Angular commit. Keeping the table
identical is deliberate: the console already knows these names, and every edge
here exists because some real task needed it.
"""

TASK_TRANSITIONS = {
    "new": ["architecture", "blocked", "cancelled"],
    "architecture": ["ready", "needs-clarification", "needs-investigation",
                     "blocked", "cancelled"],
    # A clarification answer that changes the spec itself has to go back
    # through intake, because the architect may not rewrite task.md.
    "needs-clarification": ["architecture", "new", "cancelled", "abandoned"],
    "needs-investigation": ["architecture", "blocked"],
    "ready": ["implementing", "blocked", "cancelled"],
    # FAILED is one hop back to architecture, not two through a middle state.
    "implementing": ["review", "failed", "architecture", "blocked"],
    "review": ["approved", "rejected", "failed", "blocked"],
    # A reviewer may reject the plan rather than the implementation.
    "rejected": ["implementing", "architecture", "blocked"],
    "failed": ["architecture", "blocked"],
    "approved": ["integrating", "blocked"],
    # The apply-approval gate can route back to either role.
    "integrating": ["integrated", "conflict", "blocked", "implementing",
                    "architecture"],
    "conflict": ["implementing", "blocked"],
    "blocked": ["cancelled", "abandoned"],  # plus <previousState>
}

# Scope locks are released in these three states only. A blocked task still
# holds its locks -- it is in the middle of something, not finished with it.
LOCK_RELEASED_STATES = frozenset(["integrated", "cancelled", "abandoned"])

TERMINAL_STATES = frozenset(["integrated", "cancelled", "abandoned"])

RUN_STOPPED_STATES = frozenset(["blocked", "cancelled", "abandoned"])

# The closed enum of result.yaml.outcome. A value outside it stops the run; an
# unknown outcome that silently passes is the worst kind of bug.
KNOWN_RESULT_OUTCOMES = frozenset(["completed", "failed", "needs_clarification",
                                   "blocked"])

ROLE_BY_STATE = {
    "new": "intake",
    "architecture": "architect",
    "implementing": "implementer",
    "review": "reviewer",
}

# The board the console draws. Same seven lanes as BarsaAgent.
LANES = [
    {"title": "ورودی", "states": ["new"]},
    {"title": "طراحی", "states": ["architecture", "needs-clarification",
                                  "needs-investigation", "failed"]},
    {"title": "آماده", "states": ["ready"]},
    {"title": "پیاده‌سازی", "states": ["implementing", "rejected"]},
    {"title": "بازبینی", "states": ["review"]},
    {"title": "آماده اعمال", "states": ["approved", "integrating", "conflict"]},
    {"title": "تمام", "states": ["integrated"]},
]

# `run` exit codes, as the contract defines them.
EXIT_OK = 0
EXIT_AWAITING_HUMAN = 10
EXIT_STOPPED = 20
EXIT_NO_PROGRESS = 30
EXIT_REPEATED_REJECTION = 42

EXIT_LABELS = {
    EXIT_OK: "تمام شد — integrated",
    EXIT_AWAITING_HUMAN: "منتظر توست",
    EXIT_STOPPED: "متوقف",
    EXIT_NO_PROGRESS: "بدون پیشرفت — احتمالاً باگ",
    EXIT_REPEATED_REJECTION: "رد تکراری — دوباره اجرا نکن",
    1: "خطای اجرایی",
}

GATE_SPEC_APPROVAL = "spec-approval"
GATE_CLARIFICATION = "clarification"
# The analogue of merge-approval. Nothing in this repository may write to a
# Barsa installation, so the last gate hands the validated batch to a human and
# waits to be told it was applied.
GATE_APPLY_APPROVAL = "apply-approval"

RUN_MAX_ITERATIONS = 20

# What each role may write, split into what a finished attempt must carry and
# what it may carry. Telling a role that six files are required when three are
# is how a protocol teaches people to ignore it.
ROLE_OUTPUTS = {
    "intake": {"required": ["proposed-task.md", "release-note.md"],
               "optional": ["questions.md"]},
    "architect": {"required": ["plan.md", "tests.md", "handoff.md"],
                  "optional": ["questions.md", "risks.md"]},
    "implementer": {"required": ["change-batch.json",
                                 "implementation-report.md"],
                    "optional": ["changelog.md", "failure.md"]},
    "reviewer": {"required": ["review.md"], "optional": []},
}

# Only the manager writes these, ever.
MANAGER_OWNED = ["manifest.yaml", "events.jsonl", "task.md"]


def allows(from_state, to_state):
    return to_state in TASK_TRANSITIONS.get(from_state, ())


def lane_of(state):
    for lane in LANES:
        if state in lane["states"]:
            return lane["title"]
    return None
