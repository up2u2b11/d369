"""
experiment_all_systems.py — Test ALL encoding systems
5 systems × 3 texts = 15 comparisons
Answer: Is the {3,6,9} fingerprint system-specific or universal?

IP: Emad Sulaiman Alwan
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_jummal, compute_special_6, digit_root, JUMMAL_MAP, DATA_DIR
from scipy.stats import binomtest

KSA = timezone(timedelta(hours=3))

# ─── Encoding systems ───

_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

# 1. Abjad Kabir (from config.py)
def calc_abjad(text):
    return compute_jummal(text)

# 2. K6 Special-6 (from config.py)
def calc_k6(text):
    return compute_special_6(text)

# 3. Abjad Saghir (digit root of each letter's kabir value)
SAGHIR_MAP = {ch: digit_root(v) for ch, v in JUMMAL_MAP.items()}
def calc_saghir(text):
    t = _CLEAN.sub('', text)
    return sum(SAGHIR_MAP.get(ch, 0) for ch in t)

# 4. Ordinal (position 1-28 in abjad order) — built manually, no DB needed
ORDINAL_MAP = {
    'ا': 1, 'أ': 1, 'إ': 1, 'آ': 1, 'ٱ': 1, 'ء': 1,
    'ب': 2,
    'ج': 3,
    'د': 4,
    'ه': 5, 'ة': 5,
    'و': 6, 'ؤ': 6,
    'ز': 7,
    'ح': 8,
    'ط': 9,
    'ي': 10, 'ئ': 10, 'ى': 10,
    'ك': 11,
    'ل': 12,
    'م': 13,
    'ن': 14,
    'س': 15,
    'ع': 16,
    'ف': 17,
    'ص': 18,
    'ق': 19,
    'ر': 20,
    'ش': 21,
    'ت': 22,
    'ث': 23,
    'خ': 24,
    'ذ': 25,
    'ض': 26,
    'ظ': 27,
    'غ': 28,
}
def calc_ordinal(text):
    t = _CLEAN.sub('', text)
    return sum(ORDINAL_MAP.get(ch, 0) for ch in t)

# 5. Letter count
def calc_lettercount(text):
    t = _CLEAN.sub('', text)
    return sum(1 for ch in t if ch in JUMMAL_MAP)

SYSTEMS = {
    "abjad":       ("Abjad Kabir (traditional)", calc_abjad),
    "k6":          ("K6 Special-6", calc_k6),
    "saghir":      ("Abjad Saghir (digit-root per letter)", calc_saghir),
    "ordinal":     ("Ordinal (position 1-28)", calc_ordinal),
    "lettercount": ("Letter Count", calc_lettercount),
}

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
    return [groups[s] for s in sorted(groups.keys())]

def load_text_b():
    lines = [l for l in (DATA_DIR / "bukhari_sample.txt").read_text("utf-8").splitlines() if l.strip()]
    k, m = divmod(len(lines), 114)
    chunks, idx = [], 0
    for i in range(114):
        size = k + (1 if i < m else 0)
        chunks.append(lines[idx:idx+size])
        idx += size
    return chunks

def load_text_c():
    lines = [l for l in (DATA_DIR / "muallaqat.txt").read_text("utf-8").splitlines() if l.strip()]
    return [[line] for line in lines]

# ─── Analysis ───

def analyze(units, calc_fn):
    totals = [sum(calc_fn(t) for t in unit) for unit in units]
    drs = [digit_root(v) for v in totals]
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
    }

# ─── Run ───

def run_all():
    texts = {
        "text_a": load_text_a(),
        "text_b": load_text_b(),
        "text_c": load_text_c(),
    }
    results = {}
    for sys_id, (sys_name, calc_fn) in SYSTEMS.items():
        results[sys_id] = {}
        for txt_id, units in texts.items():
            results[sys_id][txt_id] = analyze(units, calc_fn)
    return results

# ─── Output ───

def print_results(results):
    print()
    print("=" * 74)
    print("  ALL SYSTEMS — DIGIT ROOT {3,6,9} DISTRIBUTION")
    print("  5 encoding systems × 3 texts = 15 tests")
    print("=" * 74)

    for sys_id, (sys_name, _) in SYSTEMS.items():
        sr = results[sys_id]
        print()
        print(f"  {'─'*70}")
        print(f"  {sys_name}")
        print(f"  {'─'*70}")
        print(f"  {'Text':<10} {'Identity':<18} {'Units':>5} {'In {3,6,9}':>10} {'%':>7} {'p-value':>10}")
        print(f"  {'-'*10} {'-'*18} {'-'*5} {'-'*10} {'-'*7} {'-'*10}")
        for txt_id in ["text_a", "text_b", "text_c"]:
            r = sr[txt_id]
            sig = " ***" if r["significant"] else ""
            print(f"  {txt_id:<10} {IDENTITIES[txt_id]:<18} {r['units']:>5} {r['in_369']:>10} {r['proportion']*100:>6.1f}% {r['p_value']:>10.6f}{sig}")

    # ─── Summary matrix ───
    print()
    print("=" * 74)
    print("  SUMMARY MATRIX — p-values (*** = significant)")
    print("=" * 74)
    print()
    print(f"  {'System':<30} {'القرآن':>14} {'البخاري':>14} {'المعلقات':>14}")
    print(f"  {'-'*30} {'-'*14} {'-'*14} {'-'*14}")
    for sys_id, (sys_name, _) in SYSTEMS.items():
        vals = []
        for txt_id in ["text_a", "text_b", "text_c"]:
            r = results[sys_id][txt_id]
            s = f"{r['p_value']:.4f}"
            if r["significant"]:
                s += " ***"
            vals.append(s)
        print(f"  {sys_name:<30} {vals[0]:>14} {vals[1]:>14} {vals[2]:>14}")
    print()

    # ─── Verdict ───
    sig_count = sum(1 for sys_id in SYSTEMS for txt_id in ["text_a","text_b","text_c"]
                    if results[sys_id][txt_id]["significant"])
    quran_sig = [sys_id for sys_id in SYSTEMS if results[sys_id]["text_a"]["significant"]]
    control_sig = [f"{sys_id}/{txt_id}" for sys_id in SYSTEMS
                   for txt_id in ["text_b","text_c"]
                   if results[sys_id][txt_id]["significant"]]

    print("  VERDICT:")
    print(f"  - Total significant results: {sig_count} out of 15")
    if quran_sig:
        names = [SYSTEMS[s][0] for s in quran_sig]
        print(f"  - Quran significant in: {', '.join(names)}")
    else:
        print(f"  - Quran: no significant results in any system")
    if control_sig:
        print(f"  - Controls significant in: {', '.join(control_sig)}")
    else:
        print(f"  - Controls: no significant results (as expected)")
    print()

    if len(quran_sig) == 1 and not control_sig:
        print(f"  CONCLUSION:")
        print(f"  The {{3,6,9}} counting fingerprint is specific to ONE encoding")
        print(f"  ({SYSTEMS[quran_sig[0]][0]}) applied to ONE text (القرآن).")
        print(f"  It is not a general property of Arabic, nor of any encoding.")
        print(f"  This STRENGTHENS the claim — the fingerprint is precise, not noisy.")
    elif len(quran_sig) > 1 and not control_sig:
        print(f"  CONCLUSION:")
        print(f"  The {{3,6,9}} fingerprint appears in {len(quran_sig)} encoding systems")
        print(f"  for the Quran only. Multiple systems detect the pattern.")
    print()


def save_results(results):
    out_dir = PROJ_ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "experiment_all_systems.json"

    payload = {
        "experiment": "d369_all_systems_comparison",
        "date": datetime.now(KSA).isoformat(),
        "method": "digit_root_binomial_test_5_systems",
        "expected_proportion": round(1/3, 6),
        "alpha": 0.05,
        "systems": list(SYSTEMS.keys()),
        "results": {},
    }
    for sys_id in SYSTEMS:
        payload["results"][sys_id] = {
            "name": SYSTEMS[sys_id][0],
            "texts": {}
        }
        for txt_id in ["text_a", "text_b", "text_c"]:
            r = results[sys_id][txt_id]
            payload["results"][sys_id]["texts"][txt_id] = {
                "identity": IDENTITIES[txt_id],
                "units": r["units"],
                "in_369": r["in_369"],
                "proportion": r["proportion"],
                "p_value": r["p_value"],
                "significant": r["significant"],
            }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    results = run_all()
    print_results(results)
    save_results(results)
