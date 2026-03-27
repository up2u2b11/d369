"""
experiment_g14_verify.py — Independent G14 verification
Self-preservation test: group surahs by digit root → sum → check if root preserved
Permutation test for statistical significance.

IP: Emad Sulaiman Alwan
"""

import sys
import re
import json
import random
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_jummal, compute_special_6, digit_root, JUMMAL_MAP, DATA_DIR

KSA = timezone(timedelta(hours=3))
_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

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
    result = []
    for s in sorted(groups.keys()):
        result.append(sum(compute_jummal(t) for t in groups[s]))
    return result

def load_text_b():
    lines = [l for l in (DATA_DIR / "bukhari_sample.txt").read_text("utf-8").splitlines() if l.strip()]
    k, m = divmod(len(lines), 114)
    chunks, idx = [], 0
    for i in range(114):
        size = k + (1 if i < m else 0)
        total = sum(compute_jummal(l) for l in lines[idx:idx+size])
        chunks.append(total)
        idx += size
    return chunks

def load_text_c():
    lines = [l for l in (DATA_DIR / "muallaqat.txt").read_text("utf-8").splitlines() if l.strip()]
    return [compute_jummal(l) for l in lines]


# ─── G14 Core ───

def compute_t_map(jummal_values):
    """Build transformation map: group by digit root → sum → new digit root."""
    groups = defaultdict(list)
    for j in jummal_values:
        dr = digit_root(j)
        groups[dr].append(j)

    t_map = {}
    for dr in sorted(groups.keys()):
        group_sum = sum(groups[dr])
        group_dr = digit_root(group_sum)
        stable = (group_dr == dr)
        t_map[dr] = {
            "count": len(groups[dr]),
            "group_sum": group_sum,
            "group_root": group_dr,
            "stable": stable,
        }
    return t_map


def count_stable(t_map):
    """Count how many digit roots are self-preserving."""
    return sum(1 for v in t_map.values() if v["stable"])


def count_369_stable(t_map):
    """Check if specifically {3,6,9} are ALL self-preserving."""
    targets = {3, 6, 9}
    present = {k for k in t_map if k in targets}
    stable_targets = {k for k, v in t_map.items() if k in targets and v["stable"]}
    return len(stable_targets), len(present)


# ─── Permutation Test ───

def permutation_test(jummal_values, n_perms=100000):
    """
    Null hypothesis: the assignment of jummal values to units is random.
    Test statistic: number of self-preserving digit roots out of 9.
    """
    random.seed(42)

    # Observed
    t_map_obs = compute_t_map(jummal_values)
    observed_stable = count_stable(t_map_obs)
    observed_369 = count_369_stable(t_map_obs)

    # Permutations: shuffle jummal values and recompute
    # Key: we keep the SAME digit root group sizes, but shuffle which values go where
    # Actually, the cleaner test: shuffle the jummal values themselves
    # This preserves the set of values but breaks any structural relationship
    count_ge_stable = 0
    count_ge_369 = 0

    vals = list(jummal_values)
    for _ in range(n_perms):
        random.shuffle(vals)
        t_map_perm = compute_t_map(vals)
        perm_stable = count_stable(t_map_perm)
        perm_369_stable, _ = count_369_stable(t_map_perm)

        if perm_stable >= observed_stable:
            count_ge_stable += 1
        if perm_369_stable >= observed_369[0]:
            count_ge_369 += 1

    p_stable = count_ge_stable / n_perms
    p_369 = count_ge_369 / n_perms

    return {
        "observed_stable": observed_stable,
        "observed_369_stable": observed_369[0],
        "observed_369_present": observed_369[1],
        "p_all_stable": round(p_stable, 6),
        "p_369_stable": round(p_369, 6),
        "n_permutations": n_perms,
    }


# ─── Run ───

def run():
    texts = {
        "text_a": load_text_a(),
        "text_b": load_text_b(),
        "text_c": load_text_c(),
    }

    results = {}
    for txt_id, jummals in texts.items():
        print(f"  Computing {txt_id} ({IDENTITIES[txt_id]})...")
        t_map = compute_t_map(jummals)
        perm = permutation_test(jummals, n_perms=100000)
        results[txt_id] = {
            "t_map": t_map,
            "permutation": perm,
            "n_units": len(jummals),
        }
        print(f"    t_map done. {perm['observed_stable']}/9 stable. p={perm['p_369_stable']}")

    return results


def print_results(results):
    print()
    print("=" * 74)
    print("  G14 VERIFICATION — Self-Preservation Test")
    print("  Group by digit root → Sum → Does the root survive?")
    print("  Permutation test: 100,000 shuffles")
    print("=" * 74)

    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        name = IDENTITIES[txt_id]
        t_map = r["t_map"]
        perm = r["permutation"]

        print()
        print(f"  {'─'*70}")
        print(f"  {name} ({txt_id}) — {r['n_units']} units")
        print(f"  {'─'*70}")
        print()
        print(f"  {'Root':>6} {'Count':>6} {'Group Sum':>12} {'Group DR':>10} {'Stable':>8}")
        print(f"  {'-'*6} {'-'*6} {'-'*12} {'-'*10} {'-'*8}")

        for dr in sorted(t_map.keys()):
            v = t_map[dr]
            marker = " ✓" if v["stable"] else ""
            in_369 = " ←" if dr in {3, 6, 9} else ""
            print(f"  {dr:>6} {v['count']:>6} {v['group_sum']:>12,} {v['group_root']:>10} {'YES' if v['stable'] else 'no':>8}{marker}{in_369}")

        stable_list = [k for k, v in t_map.items() if v["stable"]]
        print()
        print(f"  Self-preserving roots: {stable_list} ({len(stable_list)}/9)")
        print(f"  {3,6,9} all stable: {'YES' if perm['observed_369_stable'] == perm['observed_369_present'] else 'NO'}")
        print()
        print(f"  Permutation test (n={perm['n_permutations']:,}):")
        sig_all = " ***" if perm["p_all_stable"] < 0.05 else ""
        sig_369 = " ***" if perm["p_369_stable"] < 0.05 else ""
        print(f"    p(≥{perm['observed_stable']} stable roots)  = {perm['p_all_stable']:.6f}{sig_all}")
        print(f"    p({{3,6,9}} all stable)     = {perm['p_369_stable']:.6f}{sig_369}")

    # ─── Summary ───
    print()
    print("=" * 74)
    print("  SUMMARY — G14 Self-Preservation")
    print("=" * 74)
    print()
    print(f"  {'Text':<20} {'Stable roots':>14} {'p(all stable)':>14} {'p({3,6,9})':>14}")
    print(f"  {'-'*20} {'-'*14} {'-'*14} {'-'*14}")
    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        perm = r["permutation"]
        stable = [k for k, v in r["t_map"].items() if v["stable"]]
        sig = " ***" if perm["p_369_stable"] < 0.05 else ""
        print(f"  {IDENTITIES[txt_id]:<20} {str(stable):>14} {perm['p_all_stable']:>14.6f} {perm['p_369_stable']:>14.6f}{sig}")
    print()


def save_results(results):
    out_dir = PROJ_ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "experiment_g14_verify.json"

    payload = {
        "experiment": "g14_self_preservation_verification",
        "date": datetime.now(KSA).isoformat(),
        "method": "permutation_test_100k",
        "results": {},
    }
    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        t_map_clean = {}
        for dr, v in r["t_map"].items():
            t_map_clean[str(dr)] = v
        payload["results"][txt_id] = {
            "identity": IDENTITIES[txt_id],
            "n_units": r["n_units"],
            "t_map": t_map_clean,
            "permutation": r["permutation"],
        }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    results = run()
    print_results(results)
    save_results(results)
