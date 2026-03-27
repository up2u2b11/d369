"""
experiment_length_vs_shape.py — Is K6 fingerprint from LENGTH or SHAPE?
If we normalize K6 by letter count, does {3,6,9} survive?

IP: Emad Sulaiman Alwan
"""

import sys
import re
import json
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_special_6, digit_root, JUMMAL_MAP, SPECIAL_6_MAP, DATA_DIR
from scipy.stats import binomtest

KSA = timezone(timedelta(hours=3))
_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

IDENTITIES = {
    "text_a": "القرآن الكريم",
    "text_b": "صحيح البخاري",
    "text_c": "المعلقات السبع",
}

# ─── Calculation helpers ───

def calc_k6(text):
    return compute_special_6(text)

def calc_lettercount(text):
    t = _CLEAN.sub('', text)
    return sum(1 for ch in t if ch in JUMMAL_MAP)

# ─── Data loaders (same as before) ───

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

# ─── Core analysis ───

def compute_per_unit(units):
    """For each unit: compute K6 sum, letter count, K6/length ratio, residual digit root."""
    rows = []
    for unit_texts in units:
        k6_total = sum(calc_k6(t) for t in unit_texts)
        lc_total = sum(calc_lettercount(t) for t in unit_texts)
        ratio = k6_total / lc_total if lc_total > 0 else 0
        # Method 1: digit root of ratio (rounded to int)
        dr_k6 = digit_root(k6_total)
        dr_lc = digit_root(lc_total)
        # Method 2: ratio as integer → digit root
        ratio_int = round(ratio * 1000)  # scale to preserve precision
        dr_ratio = digit_root(ratio_int) if ratio_int > 0 else 0
        # Method 3: residual = K6 mod (lettercount * mean_k6_per_letter)
        # Simpler: just use K6 - mean*LC contribution via digit root
        rows.append({
            "k6": k6_total,
            "lc": lc_total,
            "ratio": ratio,
            "dr_k6": dr_k6,
            "dr_lc": dr_lc,
            "dr_ratio": dr_ratio,
        })
    return rows


def count_369(values):
    n = len(values)
    in_369 = sum(1 for v in values if v in {3, 6, 9})
    prop = in_369 / n
    result = binomtest(in_369, n, 1/3, alternative='greater')
    return {
        "units": n,
        "in_369": in_369,
        "proportion": round(prop, 4),
        "p_value": round(result.pvalue, 6),
        "significant": bool(result.pvalue < 0.05),
    }


def run_experiment():
    texts = {
        "text_a": load_text_a(),
        "text_b": load_text_b(),
        "text_c": load_text_c(),
    }

    results = {}
    for txt_id, units in texts.items():
        rows = compute_per_unit(units)

        results[txt_id] = {
            "k6_raw":   count_369([r["dr_k6"] for r in rows]),
            "lc_raw":   count_369([r["dr_lc"] for r in rows]),
            "k6_ratio": count_369([r["dr_ratio"] for r in rows]),
        }

        # Correlation: how many surahs share BOTH k6 and lc in {3,6,9}?
        both = sum(1 for r in rows if r["dr_k6"] in {3,6,9} and r["dr_lc"] in {3,6,9})
        k6_only = sum(1 for r in rows if r["dr_k6"] in {3,6,9} and r["dr_lc"] not in {3,6,9})
        lc_only = sum(1 for r in rows if r["dr_k6"] not in {3,6,9} and r["dr_lc"] in {3,6,9})
        neither = sum(1 for r in rows if r["dr_k6"] not in {3,6,9} and r["dr_lc"] not in {3,6,9})

        results[txt_id]["overlap"] = {
            "both_369": both,
            "k6_only": k6_only,
            "lc_only": lc_only,
            "neither": neither,
            "total": len(rows),
        }

    return results


def print_results(results):
    print()
    print("=" * 74)
    print("  LENGTH vs SHAPE — Decomposing the K6 fingerprint")
    print("=" * 74)

    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        name = IDENTITIES[txt_id]
        print()
        print(f"  {'─'*70}")
        print(f"  {name} ({txt_id})")
        print(f"  {'─'*70}")
        print(f"  {'Measure':<30} {'Units':>5} {'In {3,6,9}':>10} {'%':>7} {'p-value':>10}")
        print(f"  {'-'*30} {'-'*5} {'-'*10} {'-'*7} {'-'*10}")
        for key, label in [("k6_raw", "K6 raw"), ("lc_raw", "Letter Count raw"),
                           ("k6_ratio", "K6/Length (normalized)")]:
            v = r[key]
            sig = " ***" if v["significant"] else ""
            print(f"  {label:<30} {v['units']:>5} {v['in_369']:>10} {v['proportion']*100:>6.1f}% {v['p_value']:>10.6f}{sig}")

    # ─── Overlap analysis for Quran ───
    print()
    print("=" * 74)
    print("  OVERLAP ANALYSIS — K6 vs Letter Count in {3,6,9}")
    print("=" * 74)
    print()
    print(f"  {'Text':<20} {'Both':>6} {'K6 only':>8} {'LC only':>8} {'Neither':>8} {'Total':>6}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")
    for txt_id in ["text_a", "text_b", "text_c"]:
        o = results[txt_id]["overlap"]
        name = IDENTITIES[txt_id]
        print(f"  {name:<20} {o['both_369']:>6} {o['k6_only']:>8} {o['lc_only']:>8} {o['neither']:>8} {o['total']:>6}")

    # ─── Interpretation ───
    qa = results["text_a"]
    print()
    print("  " + "=" * 60)
    print("  التفسير:")
    print("  " + "=" * 60)
    print()

    k6_sig = qa["k6_raw"]["significant"]
    lc_sig = qa["lc_raw"]["significant"]
    ratio_sig = qa["k6_ratio"]["significant"]

    if k6_sig and ratio_sig:
        print("  K6 مُعدّل (بعد طرح تأثير الطول) لا يزال معنوياً.")
        print("  → البصمة ليست من الطول فقط — هناك تأثير الشكل مستقلاً.")
        print("  → الطبقتان (الطول + الشكل) مستقلتان.")
    elif k6_sig and not ratio_sig:
        print("  K6 مُعدّل (بعد طرح تأثير الطول) فقد المعنوية.")
        print("  → الطول هو المحرّك الرئيسي لبصمة K6.")
        print("  → K6 يلتقط الطول بطريقة مُكبّرة، لكن ليس شيئاً إضافياً مستقلاً.")
    else:
        print("  النتائج تحتاج تحليلاً أعمق.")

    o = qa["overlap"]
    print()
    print(f"  تفصيل القرآن: {o['both_369']} سورة مشتركة بين K6 و LC")
    print(f"  {o['k6_only']} حصرية لـ K6 | {o['lc_only']} حصرية لـ LC")
    if o['k6_only'] > 0:
        print(f"  → {o['k6_only']} سورة تحمل بصمة K6 لكن ليس LC = تأثير الشكل الصرف")
    print()


def save_results(results):
    out_dir = PROJ_ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "experiment_length_vs_shape.json"
    payload = {
        "experiment": "length_vs_shape_decomposition",
        "date": datetime.now(KSA).isoformat(),
        "results": {}
    }
    for txt_id in ["text_a", "text_b", "text_c"]:
        r = results[txt_id]
        payload["results"][txt_id] = {
            "identity": IDENTITIES[txt_id],
            "k6_raw": r["k6_raw"],
            "lc_raw": r["lc_raw"],
            "k6_ratio": r["k6_ratio"],
            "overlap": r["overlap"],
        }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    results = run_experiment()
    print_results(results)
    save_results(results)
