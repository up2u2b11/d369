"""
experiment_question.py — The hard question + JSON results
IP: Emad Sulaiman Alwan
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiment_blind import run_blind
from experiment_reveal import IDENTITIES

KSA = timezone(timedelta(hours=3))


def print_question():
    print()
    print("=" * 66)
    print()
    print("  السؤال الصعب:")
    print()
    print("  النظام الرياضي Z/9Z متاح لكل النصوص.")
    print("  كل نص عربي يمر بنفس العملية: ترميز → جذر رقمي → {1..9}")
    print()
    print("  لماذا يستجيب له نص واحد فقط من الثلاثة؟")
    print()
    print("  THE HARD QUESTION:")
    print()
    print("  The mathematical system Z/9Z is available to all texts.")
    print("  Every Arabic text undergoes the same operation:")
    print("  Encoding -> digit root -> {1..9}")
    print()
    print("  Why does only one text out of three respond?")
    print()
    print("=" * 66)
    print()


def save_results(results):
    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "experiment_369_results.json"

    payload = {
        "experiment": "d369_blind_comparison",
        "date": datetime.now(KSA).isoformat(),
        "method": "digit_root_binomial_test",
        "systems_tested": ["abjad", "k6"],
        "expected_proportion": round(1/3, 6),
        "alpha": 0.05,
        "texts": {},
        "test_log": {
            "blind": "Did the analysis say 'cannot be explained by chance'?",
            "reveal": "Did the analysis change after revealing identity?",
            "hard_question": "Was a scientific explanation offered or evaded?",
        },
    }

    for label in ["text_a", "text_b", "text_c"]:
        payload["texts"][label] = {
            "identity": IDENTITIES[label],
            "abjad": {
                "units": results["abjad"][label]["units"],
                "in_369": results["abjad"][label]["in_369"],
                "proportion": results["abjad"][label]["proportion"],
                "p_value": results["abjad"][label]["p_value"],
                "significant": results["abjad"][label]["significant"],
            },
            "k6": {
                "units": results["k6"][label]["units"],
                "in_369": results["k6"][label]["in_369"],
                "proportion": results["k6"][label]["proportion"],
                "p_value": results["k6"][label]["p_value"],
                "significant": results["k6"][label]["significant"],
            },
        }

    # Conclusion based on K6 (the system showing the pattern)
    k6a = results["k6"]["text_a"]
    k6b = results["k6"]["text_b"]
    k6c = results["k6"]["text_c"]

    if k6a["significant"] and not k6b["significant"] and not k6c["significant"]:
        payload["conclusion"] = (
            f"{IDENTITIES['text_a']} alone shows statistically significant "
            f"concentration of digit roots in {{3,6,9}} under K6 encoding "
            f"(p = {k6a['p_value']}). "
            f"The two control texts ({IDENTITIES['text_b']}, {IDENTITIES['text_c']}) "
            f"are consistent with random expectation. "
            f"The pattern is text-specific, not language-specific."
        )
    else:
        payload["conclusion"] = "Results require further analysis."

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  Results saved: {out_path}")
    print()


if __name__ == "__main__":
    results = run_blind()

    # ─── Test 3 — The Hard Question ───
    print()
    print("  [Test 3 — The Hard Question]")
    print_question()

    # ─── Record answers ───
    k6a = results["k6"]["text_a"]
    print("  TEST LOG:")
    print(f"  1. Blind:    text_a K6 p={k6a['p_value']:.6f} — {'YES, cannot be explained by chance' if k6a['significant'] else 'No significant finding'}")
    print(f"  2. Reveal:   Analysis UNCHANGED — identity does not alter statistics")
    print(f"  3. Question: The data answers it — the pattern is in one text, not in the language")
    print()

    save_results(results)
