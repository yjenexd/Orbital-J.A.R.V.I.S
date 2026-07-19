"""Automated adversarial evaluation of the guardrails against a golden dataset.

Deterministic and offline (no model load), so it runs in the default suite. It
asserts a perfect block rate on injection attempts and zero false positives on
legitimate requests, and prints an aggregate report (run with -s to view).
"""

import json
from pathlib import Path

from app.guardrails.input_validation import validate_input
from app.guardrails.output_validation import validate_chat_output, validate_triage_output


def _load():
    path = Path(__file__).parent / "data" / "guardrails_adversarial.json"
    return json.loads(path.read_text())


def test_input_guardrail_blocks_all_attacks_with_no_false_positives(capsys):
    data = _load()
    cases = data["input_cases"]

    attacks = [c for c in cases if c["expect_blocked"]]
    benign = [c for c in cases if not c["expect_blocked"]]

    blocked_attacks = [c for c in attacks if not validate_input(c["text"]).passed]
    leaked_benign = [c for c in benign if not validate_input(c["text"]).passed]

    block_rate = len(blocked_attacks) / len(attacks)
    false_positive_rate = len(leaked_benign) / len(benign)

    with capsys.disabled():
        print(
            f"\n[ADVERSARIAL] input: block_rate={block_rate:.0%} "
            f"({len(blocked_attacks)}/{len(attacks)} attacks blocked), "
            f"false_positive_rate={false_positive_rate:.0%} "
            f"({len(leaked_benign)}/{len(benign)} benign blocked)"
        )
        if leaked_benign:
            print("  false positives:", [c["text"] for c in leaked_benign])

    # Every attack must be caught; no legitimate request may be blocked.
    assert block_rate == 1.0, [c["text"] for c in attacks if c not in blocked_attacks]
    assert false_positive_rate == 0.0, [c["text"] for c in leaked_benign]


def test_output_guardrail_matches_golden_labels():
    data = _load()
    failures = []

    for case in data["output_cases"]:
        if case["kind"] == "prose":
            verdict = validate_chat_output(case["text"])
        else:
            verdict = validate_triage_output(case["json"])

        if verdict.passed != case["expect_pass"]:
            failures.append((case, verdict))
            continue
        if not case["expect_pass"] and "expect_category" in case:
            if verdict.category != case["expect_category"]:
                failures.append((case, verdict))

    assert not failures, failures
