from collections import Counter


ACTION_FAMILIES = ["proceed", "inspect", "complete", "reasses", "escalate", "abstain"]
FORCE_LEVELS = ["advisory", "strong", "mandatory", "blocking"]
RULE_CLASSES = ["validity", "completion", "sensitivity", "interpretation"]
PRECEDENCE = {"validity": 1, "completion": 2, "sensitivity": 3, "interpretation": 4}


CONSTRAINT_MATRIX: dict[str, set[str]] = {
    "proceed":  {"advisory"},
    "inspect":  {"advisory", "strong", "mandatory"},
    "complete": {"strong", "mandatory", "blocking"},
    "reassess": {"strong", "mandatory", "blocking"},
    "escalate": {"mandatory", "blocking"},
    "abstain":  {"blocking"},
}

