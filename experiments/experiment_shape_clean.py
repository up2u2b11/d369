"""
experiment_shape_clean.py — Clean test: Is K6 fingerprint from LENGTH or SHAPE?

Two methods:
  1. Residual: subtract length effect via modular arithmetic (no decimals)
  2. Stratified: test K6 within surahs of SIMILAR length only

IP: Emad Sulaiman Alwan
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime, timezone, timedelta

PROJ_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ_ROOT))

from config import compute_special_6, digit_root, JUMMAL_MAP, DATA_DIR
from scipy.stats import binomtest

KSA = timezone(timedelta(hours=3))
_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')


def calc_k6(text):
    return compute_special_6(text)

def calc_lettercount(text):
    t = _CLEAN.sub('', text)
    return sum(1 for ch in t if ch in JUMMAL_MAP)


def load_quran():
    groups = defaultdict(list)
    for line in (DATA_DIR / "quran_simple_clean.txt").read_text("utf-8").splitlines():
        if not line or line.startswith("#"): continue
        parts = line.split("|", 2)
        if len(parts) < 3: continue
        groups[int(parts[0])].append(parts[2])
    return [groups[s] for s in sorted(groups.keys())]


def count_369(values):
    n = len(values)
    if n == 0:
        return {"units": 0, "in_369": 0, "proportion": 0, "p_value": 1.0, "significant": False}
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


def run():
    surahs = load_quran()  # list of 114, each is list of ayah texts

    # ─── Compute per surah ───
    data = []
    for i, ayahs in enumerate(surahs):
        k6 = sum(calc_k6(t) for t in ayahs)
        lc = sum(calc_lettercount(t) for t in ayahs)
        data.append({
            "surah": i + 1,
            "k6": k6,
            "lc": lc,
            "dr_k6": digit_root(k6),
            "dr_lc": digit_root(lc),
        })

    # ═══════════════════════════════════════════
    # METHOD 1: Modular residual (no decimals)
    # ═══════════════════════════════════════════
    # Key insight: digit_root(a) depends only on a mod 9
    # If K6 = length_effect + shape_effect, then:
    #   dr(K6) is determined by (K6 mod 9)
    #   dr(LC) is determined by (LC mod 9)
    # Residual in mod 9: (K6 mod 9 - LC mod 9) mod 9
    # This isolates what K6 adds BEYOND letter count, in modular space
    # No decimals, no rounding, mathematically clean

    residuals = []
    for d in data:
        r = (d["k6"] % 9 - d["lc"] % 9) % 9
        if r == 0: r = 9  # digit root convention: 0 → 9
        residuals.append(r)

    # ═══════════════════════════════════════════
    # METHOD 2: Stratified by length bands
    # ═══════════════════════════════════════════
    # Group surahs into length bands, test K6 within each band

    sorted_data = sorted(data, key=lambda d: d["lc"])

    # Define bands by quartiles
    n = len(sorted_data)
    q1 = sorted_data[n // 4]["lc"]
    q2 = sorted_data[n // 2]["lc"]
    q3 = sorted_data[3 * n // 4]["lc"]

    bands = {
        f"short (≤{q1} letters)": [d for d in data if d["lc"] <= q1],
        f"medium ({q1+1}-{q2} letters)": [d for d in data if q1 < d["lc"] <= q2],
        f"long ({q2+1}-{q3} letters)": [d for d in data if q2 < d["lc"] <= q3],
        f"very long (>{q3} letters)": [d for d in data if d["lc"] > q3],
    }

    # Also: a tight band of similar-length surahs (middle 50%)
    mid_surahs = sorted_data[n//4 : 3*n//4]
    tight_range = f"middle 50% ({mid_surahs[0]['lc']}-{mid_surahs[-1]['lc']} letters)"

    return data, residuals, bands, mid_surahs, tight_range


def print_results(data, residuals, bands, mid_surahs, tight_range):
    print()
    print("=" * 74)
    print("  CLEAN TEST — LENGTH vs SHAPE decomposition")
    print("  No decimals. No rounding. Modular arithmetic + stratification.")
    print("=" * 74)

    # ─── Baseline ───
    print()
    print("  ─── Baseline (all 114 surahs) ───")
    r_k6 = count_369([d["dr_k6"] for d in data])
    r_lc = count_369([d["dr_lc"] for d in data])
    print(f"  K6 raw:          {r_k6['in_369']}/{r_k6['units']} = {r_k6['proportion']*100:.1f}%  p={r_k6['p_value']:.6f} {'***' if r_k6['significant'] else ''}")
    print(f"  Letter Count:    {r_lc['in_369']}/{r_lc['units']} = {r_lc['proportion']*100:.1f}%  p={r_lc['p_value']:.6f} {'***' if r_lc['significant'] else ''}")

    # ─── Method 1: Modular residual ───
    print()
    print("  ─── Method 1: Modular Residual (K6 mod 9 − LC mod 9) mod 9 ───")
    print("  This isolates what K6 adds BEYOND letter count, in Z/9Z.")
    print("  No decimals, no rounding — pure modular arithmetic.")
    r_res = count_369(residuals)
    print(f"  Residual:        {r_res['in_369']}/{r_res['units']} = {r_res['proportion']*100:.1f}%  p={r_res['p_value']:.6f} {'***' if r_res['significant'] else ''}")
    if r_res["significant"]:
        print("  → الشكل (shape) معنوي مستقلاً عن الطول!")
    else:
        print("  → الشكل وحده غير معنوي بعد طرح الطول.")

    # ─── Method 2: Stratified ───
    print()
    print("  ─── Method 2: Stratified by length bands ───")
    print("  K6 tested within surahs of SIMILAR length only.")
    print()
    print(f"  {'Band':<35} {'n':>4} {'In {3,6,9}':>10} {'%':>7} {'p-value':>10}")
    print(f"  {'-'*35} {'-'*4} {'-'*10} {'-'*7} {'-'*10}")

    for band_name, band_data in bands.items():
        r = count_369([d["dr_k6"] for d in band_data])
        sig = " ***" if r["significant"] else ""
        print(f"  {band_name:<35} {r['units']:>4} {r['in_369']:>10} {r['proportion']*100:>6.1f}% {r['p_value']:>10.6f}{sig}")

    # Middle 50%
    r_mid = count_369([d["dr_k6"] for d in mid_surahs])
    sig = " ***" if r_mid["significant"] else ""
    print(f"  {'-'*35} {'-'*4} {'-'*10} {'-'*7} {'-'*10}")
    print(f"  {tight_range:<35} {r_mid['units']:>4} {r_mid['in_369']:>10} {r_mid['proportion']*100:>6.1f}% {r_mid['p_value']:>10.6f}{sig}")

    # ─── Also test LC within bands (control) ───
    print()
    print("  ─── Letter Count within same bands (control) ───")
    print()
    print(f"  {'Band':<35} {'n':>4} {'In {3,6,9}':>10} {'%':>7} {'p-value':>10}")
    print(f"  {'-'*35} {'-'*4} {'-'*10} {'-'*7} {'-'*10}")
    for band_name, band_data in bands.items():
        r = count_369([d["dr_lc"] for d in band_data])
        sig = " ***" if r["significant"] else ""
        print(f"  {band_name:<35} {r['units']:>4} {r['in_369']:>10} {r['proportion']*100:>6.1f}% {r['p_value']:>10.6f}{sig}")

    # ─── Interpretation ───
    print()
    print("  " + "=" * 60)
    print("  الحكم النهائي:")
    print("  " + "=" * 60)
    print()

    any_band_sig = any(count_369([d["dr_k6"] for d in bd])["significant"] for bd in bands.values())

    if r_res["significant"]:
        print("  ✓ المقياس المعياري (modular residual) معنوي.")
        print("  → الشكل يحمل بصمة مستقلة عن الطول.")
    elif any_band_sig:
        print("  ⚠ المقياس المعياري غير معنوي — لكن بعض الشرائح معنوية.")
        print("  → الشكل قد يكون فعّالاً في أطوال معينة فقط.")
    else:
        print("  ✗ لا المقياس المعياري ولا الشرائح معنوية.")
        print("  → الطول هو المحرّك الأساسي لبصمة K6 في العدّ المباشر.")
        print()
        print("  لكن هذا لا يُضعف G14 — بل يُوضّح الصورة:")
        print("  • العدّ المباشر: البصمة من أطوال السور (p=0.031)")
        print("  • G14: بنية ذاتية الحفظ مستقلة عن الطول (p<0.00001)")
        print("  • السؤال ينتقل: لماذا أطوال سور القرآن بالذات تحمل هذه الخاصية؟")
    print()


def save_results(data, residuals, bands, mid_surahs, tight_range):
    out_dir = PROJ_ROOT / "results"
    out_path = out_dir / "experiment_shape_clean.json"

    r_k6 = count_369([d["dr_k6"] for d in data])
    r_lc = count_369([d["dr_lc"] for d in data])
    r_res = count_369(residuals)
    r_mid = count_369([d["dr_k6"] for d in mid_surahs])

    band_results = {}
    for band_name, band_data in bands.items():
        band_results[band_name] = {
            "k6": count_369([d["dr_k6"] for d in band_data]),
            "lc": count_369([d["dr_lc"] for d in band_data]),
        }

    payload = {
        "experiment": "shape_clean_decomposition",
        "date": datetime.now(KSA).isoformat(),
        "baseline": {"k6": r_k6, "lc": r_lc},
        "modular_residual": r_res,
        "middle_50_pct": {"range": tight_range, "k6": r_mid},
        "bands": band_results,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {out_path}")


if __name__ == "__main__":
    data, residuals, bands, mid_surahs, tight_range = run()
    print_results(data, residuals, bands, mid_surahs, tight_range)
    save_results(data, residuals, bands, mid_surahs, tight_range)
