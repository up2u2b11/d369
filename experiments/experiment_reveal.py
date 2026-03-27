"""
experiment_reveal.py — Identity reveal
Same data, same calculations — now with names.

IP: Emad Sulaiman Alwan
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiment_blind import run_blind

IDENTITIES = {
    "text_a": "القرآن الكريم",
    "text_b": "صحيح البخاري",
    "text_c": "المعلقات السبع",
}


def print_table(title, system_results):
    print()
    print(f"  {'─' * 72}")
    print(f"  {title}")
    print(f"  {'─' * 72}")
    print(f"  {'Label':<10} {'Identity':<20} {'Units':>6} {'In {3,6,9}':>11} {'%':>7} {'p-value':>10}")
    print(f"  {'-'*10} {'-'*20} {'-'*6} {'-'*11} {'-'*7} {'-'*10}")

    for label in ["text_a", "text_b", "text_c"]:
        r = system_results[label]
        name = IDENTITIES[label]
        sig = " ***" if r["significant"] else ""
        print(f"  {label:<10} {name:<20} {r['units']:>6} {r['in_369']:>11} {r['proportion']*100:>6.1f}% {r['p_value']:>10.6f}{sig}")

    print(f"  {'-'*10} {'-'*20} {'-'*6} {'-'*11} {'-'*7} {'-'*10}")
    print(f"  {'Expected':<10} {'':20} {'':>6} {'':>11} {'33.3%':>7}")


def print_reveal(results):
    print()
    print("=" * 74)
    print("  REVEAL — DIGIT ROOT {3,6,9} DISTRIBUTION")
    print("=" * 74)

    print_table("System 1: Traditional Abjad (Kabir)", results["abjad"])
    print_table("System 2: Special-6 Encoding (K6)", results["k6"])

    print()
    print("  *** = statistically significant (p < 0.05)")

    # ─── Interpretation ───
    k6 = results["k6"]
    qa, qb, qc = k6["text_a"], k6["text_b"], k6["text_c"]

    print()
    print("  " + "=" * 56)
    print("  التفسير:")
    print("  " + "=" * 56)
    print()

    if qa["significant"] and not qb["significant"] and not qc["significant"]:
        print(f"  القرآن الكريم:   {qa['in_369']}/{qa['units']} = {qa['proportion']*100:.1f}%  (p = {qa['p_value']:.6f}) ***")
        print(f"  صحيح البخاري:    {qb['in_369']}/{qb['units']} = {qb['proportion']*100:.1f}%  (p = {qb['p_value']:.6f})")
        print(f"  المعلقات السبع:   {qc['in_369']}/{qc['units']} = {qc['proportion']*100:.1f}%  (p = {qc['p_value']:.6f})")
        print()
        print("  النتيجة: القرآن وحده يُظهر انحرافاً إحصائياً.")
        print("  النصان الآخران — رغم أنهما عربيان — لا يحملان هذا النمط.")
        print()
        print("  هل تغيّر التحليل بعد كشف الهوية؟")
        print("  الجواب: لا. الأرقام هي نفسها. الهوية لا تُغيّر الإحصاء.")
    elif not qa["significant"] and not qb["significant"] and not qc["significant"]:
        print("  لا يوجد انحراف إحصائي في أي نص بنظام K6.")
    else:
        print("  النتائج مختلطة — تحتاج مراجعة.")
    print()


if __name__ == "__main__":
    results = run_blind()
    print_reveal(results)
