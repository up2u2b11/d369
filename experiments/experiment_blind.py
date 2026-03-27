"""
experiment_blind.py — Blind digit-root analysis
Three texts, anonymous labels only: text_a, text_b, text_c
Two calculation systems tested: Abjad (traditional) and K6 (special-6)
No identity revealed.

IP: Emad Sulaiman Alwan
"""

import sys
from pathlib import Path
from collections import defaultdict

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_jummal, compute_special_6, digit_root, DATA_DIR
from scipy.stats import binomtest

# ─── Data loaders ───

def _load_structured(path):
    """Load surah|ayah|text format, return dict of {surah_id: [texts]}."""
    lines = path.read_text(encoding="utf-8").splitlines()
    groups = defaultdict(list)
    for line in lines:
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        groups[int(parts[0])].append(parts[2])
    return groups


def _chunk_list(lst, n_chunks):
    k, m = divmod(len(lst), n_chunks)
    chunks, idx = [], 0
    for i in range(n_chunks):
        size = k + (1 if i < m else 0)
        chunks.append(lst[idx:idx + size])
        idx += size
    return chunks


def load_text_a():
    """114 units from a structured text."""
    groups = _load_structured(DATA_DIR / "quran_simple_clean.txt")
    return [groups[s] for s in sorted(groups.keys())]


def load_text_b():
    """999 entries chunked into 114 groups."""
    path = DATA_DIR / "bukhari_sample.txt"
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return _chunk_list(lines, 114)


def load_text_c():
    """Each non-empty line = one unit (list of 1-element lists)."""
    path = DATA_DIR / "muallaqat.txt"
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [[line] for line in lines]


# ─── Analysis ───

def analyze(units, calc_fn):
    """Compute digit-root distribution for a list of text-units using calc_fn."""
    jummals = []
    for unit_texts in units:
        total = sum(calc_fn(t) for t in unit_texts)
        jummals.append(total)
    drs = [digit_root(j) for j in jummals]
    n = len(drs)
    in_369 = sum(1 for d in drs if d in {3, 6, 9})
    prop = in_369 / n
    result = binomtest(in_369, n, 1/3, alternative='greater')
    return {
        "units": n,
        "in_369": in_369,
        "proportion": round(prop, 4),
        "p_value": round(result.pvalue, 6),
        "significant": bool(result.pvalue < 0.05),
        "digit_roots": drs,
    }


def run_blind():
    loaders = [("text_a", load_text_a), ("text_b", load_text_b), ("text_c", load_text_c)]
    results = {"abjad": {}, "k6": {}}
    for label, loader in loaders:
        units = loader()
        results["abjad"][label] = analyze(units, compute_jummal)
        results["k6"][label] = analyze(units, compute_special_6)
    return results


# ─── Output ───

def print_table(title, system_results):
    print()
    print(f"  {'─' * 56}")
    print(f"  {title}")
    print(f"  {'─' * 56}")
    print(f"  {'Text':<10} {'Units':>6} {'In {3,6,9}':>11} {'Proportion':>12} {'p-value':>10}")
    print(f"  {'-'*10} {'-'*6} {'-'*11} {'-'*12} {'-'*10}")

    for label in ["text_a", "text_b", "text_c"]:
        r = system_results[label]
        sig = " ***" if r["significant"] else ""
        print(f"  {label:<10} {r['units']:>6} {r['in_369']:>11} {r['proportion']*100:>11.1f}% {r['p_value']:>10.6f}{sig}")

    print(f"  {'-'*10} {'-'*6} {'-'*11} {'-'*12} {'-'*10}")
    print(f"  {'Expected':<10} {'':>6} {'':>11} {'33.3%':>12}")


def print_results(results):
    print()
    print("=" * 62)
    print("  BLIND EXPERIMENT — DIGIT ROOT {3,6,9} DISTRIBUTION")
    print("=" * 62)

    print_table("System 1: Traditional Abjad (Kabir)", results["abjad"])
    print_table("System 2: Special-6 Encoding (K6)", results["k6"])

    print()
    print("  *** = statistically significant (p < 0.05)")
    print()

    # Verdict
    for sys_name, sys_results in results.items():
        sig_texts = [k for k, v in sys_results.items() if v["significant"]]
        if sig_texts:
            print(f"  [{sys_name.upper()}] {', '.join(sig_texts)} deviate significantly from random.")
        else:
            print(f"  [{sys_name.upper()}] No text shows significant deviation.")
    print()


if __name__ == "__main__":
    results = run_blind()
    print_results(results)
