"""
experiment_g14_correct.py — CORRECTED G14 verification

Critical mathematical insight discovered:
  digit_root(sum of group d) = (d * count_d) mod 9
  Stable iff d*(count-1) ≡ 0 (mod 9)

This means:
  Root 9:    ALWAYS stable (trivially, 9k ≡ 0 mod 9)
  Roots 3,6: stable iff count ≡ 1 (mod 3)  — probability ≈ 1/3
  Other roots: stable iff count ≡ 1 (mod 9) — probability ≈ 1/9

G14 self-preservation is a COUNTING property, not a value property.
The correct test: given 114 items distributed across 9 digit-root bins,
what is the probability that BOTH root-3 and root-6 counts ≡ 1 (mod 3)?

IP: Emad Sulaiman Alwan
"""

import sys
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from math import comb, factorial
from scipy.stats import multinomial
import numpy as np

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_jummal, digit_root, DATA_DIR

KSA = timezone(timedelta(hours=3))

IDENTITIES = {
    "text_a": "القرآن الكريم",
    "text_b": "صحيح البخاري",
    "text_c": "المعلقات السبع",
}

# ─── Data loaders ───

def load_text_a():
    groups = defaultdict(list)
    for line in (DATA_DIR / "quran_simple_clean.txt").read_text("utf-8").splitlines():
        if not line or line.startswith("#"): continue
        parts = line.split("|", 2)
        if len(parts) < 3: continue
        groups[int(parts[0])].append(parts[2])
    return [sum(compute_jummal(t) for t in groups[s]) for s in sorted(groups.keys())]

def load_text_b():
    lines = [l for l in (DATA_DIR / "bukhari_sample.txt").read_text("utf-8").splitlines() if l.strip()]
    k, m = divmod(len(lines), 114)
    chunks, idx = [], 0
    for i in range(114):
        size = k + (1 if i < m else 0)
        chunks.append(sum(compute_jummal(l) for l in lines[idx:idx+size]))
        idx += size
    return chunks

def load_text_c():
    lines = [l for l in (DATA_DIR / "muallaqat.txt").read_text("utf-8").splitlines() if l.strip()]
    return [compute_jummal(l) for l in lines]

# ─── Mathematical analysis ───

def stability_condition(d, n):
    """Check if root d with count n is self-preserving."""
    if d == 0 or n == 0:
        return False
    return (d * (n - 1)) % 9 == 0

def analyze_text(jummal_values, label):
    """Full G14 analysis with correct mathematical framework."""
    # Count surahs per digit root
    dr_counts = Counter()
    for j in jummal_values:
        dr_counts[digit_root(j)] += 1

    # Build t_map
    t_map = {}
    for d in range(1, 10):
        n = dr_counts.get(d, 0)
        stable = stability_condition(d, n)
        # Actual sum for verification
        group_vals = [j for j in jummal_values if digit_root(j) == d]
        group_sum = sum(group_vals)
        group_dr = digit_root(group_sum) if group_sum > 0 else 0
        # Verify mathematical formula
        formula_dr = (d * n) % 9
        if formula_dr == 0 and n > 0:
            formula_dr = 9

        t_map[d] = {
            "count": n,
            "group_sum": group_sum,
            "group_dr_actual": group_dr,
            "group_dr_formula": formula_dr,
            "stable": stable,
            "mod3": n % 3 if d in {3, 6} else None,
            "mod9": n % 9 if d not in {3, 6, 9} else None,
        }

    return t_map, dr_counts


def monte_carlo_p_value(n_total, n_sims=1000000):
    """
    Monte Carlo: distribute n_total items uniformly across 9 bins.
    Test: P(bin_3 ≡ 1 mod 3 AND bin_6 ≡ 1 mod 3)

    This is the correct null model for G14:
    if digit roots were uniformly distributed, what's the probability
    that both root-3 and root-6 counts satisfy the stability condition?
    """
    np.random.seed(42)

    count_both = 0
    count_369_all = 0

    for _ in range(n_sims):
        # Random multinomial: 114 items into 9 equal bins
        bins = np.random.multinomial(n_total, [1/9]*9)
        # bins[0]=root1, bins[1]=root2, ..., bins[2]=root3, bins[5]=root6, bins[8]=root9

        root3_count = bins[2]  # index 2 = root 3
        root6_count = bins[5]  # index 5 = root 6

        root3_stable = (root3_count % 3 == 1)
        root6_stable = (root6_count % 3 == 1)
        # root 9 always stable

        if root3_stable and root6_stable:
            count_both += 1

        # Also check: ALL of {3,6,9} stable AND none of {1,2,4,5,7,8} stable
        all_369 = root3_stable and root6_stable  # root9 always stable
        other_stable = any(
            stability_condition(d+1, bins[d])
            for d in [0,1,3,4,6,7]  # roots 1,2,4,5,7,8
        )
        if all_369 and not other_stable:
            count_369_all += 1

    p_both = count_both / n_sims
    p_exact_pattern = count_369_all / n_sims

    return {
        "p_369_all_stable": round(p_both, 6),
        "p_exact_pattern_369_only": round(p_exact_pattern, 6),
        "n_simulations": n_sims,
    }


def run():
    texts = {
        "text_a": load_text_a(),
        "text_b": load_text_b(),
        "text_c": load_text_c(),
    }

    results = {}
    for txt_id, jummals in texts.items():
        print(f"  Analyzing {txt_id} ({IDENTITIES[txt_id]})...")
        t_map, dr_counts = analyze_text(jummals, txt_id)
        results[txt_id] = {
            "n_units": len(jummals),
            "t_map": t_map,
            "dr_counts": dict(dr_counts),
        }

    # Monte Carlo for Quran (114 units)
    print("  Running Monte Carlo (1M simulations)...")
    mc_114 = monte_carlo_p_value(114, n_sims=1000000)
    results["monte_carlo_114"] = mc_114

    # Monte Carlo for Mu'allaqat (78 units)
    mc_78 = monte_carlo_p_value(78, n_sims=1000000)
    results["monte_carlo_78"] = mc_78

    return results


def print_results(results):
    print()
    print("=" * 78)
    print("  G14 CORRECTED — Self-Preservation is a COUNTING Property")
    print("=" * 78)
    print()
    print("  Mathematical proof:")
    print("  digit_root(sum of group d) = (d × count) mod 9")
    print("  Stable iff d×(count−1) ≡ 0 (mod 9)")
    print()
    print("  Root 9:    ALWAYS stable (trivial)")
    print("  Roots 3,6: stable iff count ≡ 1 (mod 3)  — prob ≈ 1/3 each")
    print("  Others:    stable iff count ≡ 1 (mod 9)  — prob ≈ 1/9 each")
    print()

    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        name = IDENTITIES[txt_id]
        t_map = r["t_map"]

        print(f"  {'─'*74}")
        print(f"  {name} ({txt_id}) — {r['n_units']} units")
        print(f"  {'─'*74}")
        print()
        print(f"  {'Root':>6} {'Count':>6} {'Condition':>20} {'Met?':>6} {'Stable':>8} {'Verify':>8}")
        print(f"  {'-'*6} {'-'*6} {'-'*20} {'-'*6} {'-'*8} {'-'*8}")

        stable_roots = []
        for d in range(1, 10):
            v = t_map.get(d, {"count":0, "stable":False, "group_dr_actual":0, "group_dr_formula":0})
            n = v["count"]
            if d == 9:
                cond = "always"
                met = "✓"
            elif d in {3, 6}:
                cond = f"count%3=={n%3} (need 1)"
                met = "✓" if n % 3 == 1 else "✗"
            else:
                cond = f"count%9=={n%9} (need 1)"
                met = "✓" if n % 9 == 1 else "✗"

            verify = "✓" if v.get("group_dr_actual") == v.get("group_dr_formula") else "✗"
            mark = " ←" if d in {3,6,9} else ""
            if v["stable"]:
                stable_roots.append(d)
            print(f"  {d:>6} {n:>6} {cond:>20} {met:>6} {'YES' if v['stable'] else 'no':>8} {verify:>8}{mark}")

        print()
        print(f"  Stable roots: {stable_roots}")
        print()

    # Monte Carlo results
    mc = results["monte_carlo_114"]
    print(f"  {'─'*74}")
    print(f"  Monte Carlo — 1,000,000 simulations (114 items, 9 uniform bins)")
    print(f"  {'─'*74}")
    print()
    print(f"  P(roots 3 AND 6 both stable) = {mc['p_369_all_stable']:.4f}")
    print(f"  P(EXACTLY {{3,6,9}} stable, others not) = {mc['p_exact_pattern_369_only']:.4f}")
    print()

    # ─── Honest interpretation ───
    print("  " + "=" * 60)
    print("  التفسير الأمين:")
    print("  " + "=" * 60)
    print()
    print(f"  احتمال أن يكون كلا الجذرين 3 و 6 مستقرّين بالصدفة:")
    print(f"  p = {mc['p_369_all_stable']:.4f} (≈ 1/9)")
    print()
    print(f"  احتمال أن يكون النمط بالضبط {{3,6,9}} فقط مستقرة:")
    print(f"  p = {mc['p_exact_pattern_369_only']:.4f}")
    print()

    if mc['p_exact_pattern_369_only'] < 0.05:
        print("  ✓ النمط الدقيق (فقط {3,6,9} مستقرة) معنوي إحصائياً.")
    elif mc['p_369_all_stable'] < 0.05:
        print("  ⚠ استقرار {3,6,9} معنوي، لكن ليس حصرياً لها.")
    else:
        print("  ✗ الاستقرار ليس نادراً إحصائياً بالقدر المُدّعى.")
        print("    السبب: الجذور 3 و 6 لها شرط أسهل (mod 3 بدل mod 9).")
        print("    هذا يجعل استقرارها 3× أكثر احتمالاً من الجذور الأخرى.")
    print()

    print("  المعادلة الحاسمة:")
    print("  ─────────────────")
    print("  القرآن: 13 سورة جذرها 3 → 13 mod 3 = 1 ✓")
    print("  القرآن: 10 سور جذرها 6  → 10 mod 3 = 1 ✓")
    print("  البخاري: 9 مجموعات جذرها 3 → 9 mod 3 = 0 ✗")
    print()
    print("  السؤال الحقيقي ليس 'هل {3,6,9} مستقرة'")
    print("  بل: 'لماذا عدد السور ذات الجذر 3 يساوي 13 (≡1 mod 3)")
    print("  وعدد السور ذات الجذر 6 يساوي 10 (≡1 mod 3)؟'")
    print()


def save_results(results):
    out_dir = PROJ_ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "experiment_g14_correct.json"

    payload = {
        "experiment": "g14_corrected_counting_property",
        "date": datetime.now(KSA).isoformat(),
        "critical_insight": "G14 stability = d*(count-1) ≡ 0 (mod 9). Pure counting property.",
        "stability_rules": {
            "root_9": "ALWAYS stable",
            "roots_3_6": "stable iff count ≡ 1 (mod 3) — prob ≈ 1/3",
            "roots_1_2_4_5_7_8": "stable iff count ≡ 1 (mod 9) — prob ≈ 1/9",
        },
        "results": {},
    }

    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        t_clean = {}
        for d, v in r["t_map"].items():
            t_clean[str(d)] = {k: int(vv) if isinstance(vv, (np.integer,)) else vv for k, vv in v.items()}
        payload["results"][txt_id] = {
            "identity": IDENTITIES[txt_id],
            "n_units": r["n_units"],
            "t_map": t_clean,
            "dr_counts": {str(k): v for k, v in r["dr_counts"].items()},
        }

    payload["monte_carlo_114"] = results["monte_carlo_114"]
    payload["monte_carlo_78"] = results["monte_carlo_78"]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    results = run()
    print_results(results)
    save_results(results)
