"""
d369 — المحركات الخمسة
الملكية الفكرية: عماد سليمان علوان
١٤ مارس ٢٠٢٦

المحركات:
  1. engine_divisors   — /divisors
  2. engine_explore    — /explore
  3. engine_match      — /match
  4. engine_correlation — /correlation
  5. engine_sequence   — /sequence

إضافات:
  engine_overview     — /overview
  engine_compare      — /compare
"""

import math
import re
import sqlite3
from collections import Counter
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, digit_root, compute_jummal, JUMMAL_MAP


# ─── أدوات مشتركة ────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def digit_sum(n: int) -> int:
    return sum(int(d) for d in str(abs(n)))


def prime_factors(n: int) -> dict:
    """التحليل إلى عوامل أولية — يعمل حتى 10^12"""
    factors = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def all_divisors(n: int) -> list:
    """كل القواسم مرتبة"""
    divs = set()
    for i in range(1, int(math.isqrt(n)) + 1):
        if n % i == 0:
            divs.add(i)
            divs.add(n // i)
    return sorted(divs)


def pf_str(pf: dict) -> str:
    """تنسيق العوامل الأولية: 2² × 3 × 7"""
    parts = []
    for p, e in sorted(pf.items()):
        if e == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{e}")
    return " × ".join(parts)


def parse_group_spec(args: list) -> str:
    """
    تحويل الوسيطات إلى group_spec داخلي.
    أمثلة:
      ["9"]          → "root_9"
      ["جذر", "3"]  → "root_3"
      ["مكي"]       → "meccan"
      ["مدني"]      → "madani"
    """
    text = " ".join(args).strip()
    # رقم مجرد → جذر رقمي
    if re.fullmatch(r'\d', text):
        return f"root_{text}"
    # "جذر N" أو "root N" أو "جذر_N"
    m = re.search(r'(?:جذر|root)[_\s]*(\d)', text, re.I)
    if m:
        return f"root_{m.group(1)}"
    # مكي / مدني
    if any(w in text for w in ['مكي', 'مكية', 'meccan', 'makki']):
        return 'meccan'
    if any(w in text for w in ['مدني', 'مدنية', 'madani', 'medinan']):
        return 'madani'
    return text


def _get_group(spec: str, conn: sqlite3.Connection) -> dict | None:
    """استخراج بيانات مجموعة من قاعدة البيانات"""
    if spec.startswith("root_"):
        dr_val = int(spec.split("_")[1])
        rows = conn.execute(
            "SELECT surah_id, jummal_total, ayah_count FROM surahs WHERE digit_root=? ORDER BY surah_id",
            (dr_val,)
        ).fetchall()
        name = f"جذر {dr_val}"
        meta = {"digit_root": dr_val}
    elif spec in ("meccan", "makki"):
        rows = conn.execute(
            "SELECT surah_id, jummal_total, ayah_count FROM surahs WHERE revelation_type='meccan' ORDER BY surah_id"
        ).fetchall()
        name = "مكية"
        meta = {}
    elif spec in ("madani", "medinan"):
        rows = conn.execute(
            "SELECT surah_id, jummal_total, ayah_count FROM surahs WHERE revelation_type!='meccan' ORDER BY surah_id"
        ).fetchall()
        name = "مدنية"
        meta = {}
    else:
        return None

    if not rows:
        return None

    ids = [r[0] for r in rows]
    total_j = sum(r[1] for r in rows)
    total_v = sum(r[2] for r in rows)

    return {
        "name": name,
        "spec": spec,
        "count": len(rows),
        "ids": ids,
        "total_jummal": total_j,
        "total_jummal_root": digit_root(total_j),
        "total_verses": total_v,
        **meta,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  المحرك 1: /divisors
# ═══════════════════════════════════════════════════════════════════════════════

def engine_divisors(n: int) -> dict:
    """حساب عوامل القسمة الكاملة مع ربط بالقرآن"""
    pf = prime_factors(n)
    divs = all_divisors(n)
    dc = len(divs)
    dr = digit_root(n)
    ds = digit_sum(n)
    is_prime = (len(pf) == 1 and list(pf.values())[0] == 1)

    # ربط بالقرآن
    notes = []
    conn = get_db()

    # هل عدد القواسم = عدد سور بجذر معين؟
    for dr_val in range(1, 10):
        count = conn.execute(
            "SELECT COUNT(*) FROM surahs WHERE digit_root=?", (dr_val,)
        ).fetchone()[0]
        if count == dc:
            notes.append(f"عدد القواسم ({dc}) = عدد سور جذر {dr_val}")

    # هل العدد = جُمَّل سورة بعينها؟
    sm = conn.execute(
        "SELECT name_ar FROM surahs WHERE jummal_total=?", (n,)
    ).fetchone()
    if sm:
        notes.append(f"جُمَّل سورة {sm[0]} = {n:,}")

    # هل العدد = مجموع جُمَّل مجموعة جذر؟
    for dr_val in range(1, 10):
        total = conn.execute(
            "SELECT COALESCE(SUM(jummal_total), 0) FROM surahs WHERE digit_root=?", (dr_val,)
        ).fetchone()[0]
        if total == n:
            notes.append(f"مجموع جُمَّل سور جذر {dr_val} = {n:,}")

    # هل العدد = مجموع جُمَّل القرآن؟
    total_quran = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    if total_quran == n:
        notes.append("مجموع جُمَّل القرآن كله")

    # هل عدد القواسم = عدد آيات سورة؟
    am = conn.execute(
        "SELECT name_ar FROM surahs WHERE ayah_count=?", (dc,)
    ).fetchone()
    if am:
        notes.append(f"عدد القواسم ({dc}) = آيات سورة {am[0]}")

    conn.close()

    return {
        "number": n,
        "prime_factors": pf,
        "prime_factors_str": pf_str(pf),
        "all_divisors": divs,
        "divisor_count": dc,
        "is_prime": is_prime,
        "digit_root": dr,
        "digit_sum": ds,
        "notes": notes,
    }


def format_divisors(r: dict) -> str:
    n = r["number"]
    lines = [
        f"🔢 عوامل القسمة لـ {n:,}",
        f"  الجذر الرقمي: {r['digit_root']} | مجموع الأرقام: {r['digit_sum']}",
    ]

    if r["is_prime"]:
        lines.append("  العدد أولي — لا قواسم إلا 1 ونفسه")
    else:
        lines.append(f"  التحليل: {r['prime_factors_str']}")
        lines.append(f"  عدد القواسم: {r['divisor_count']}")

    divs = r["all_divisors"]
    if len(divs) <= 24:
        lines.append(f"  القواسم: {', '.join(str(d) for d in divs)}")
    else:
        first = ', '.join(str(d) for d in divs[:12])
        last = ', '.join(str(d) for d in divs[-6:])
        lines.append(f"  القواسم: {first} ... {last}")

    if r["notes"]:
        lines.append("")
        lines.append("  🔗 ربط بالقرآن:")
        for note in r["notes"]:
            lines.append(f"    • {note}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  المحرك 2: /explore
# ═══════════════════════════════════════════════════════════════════════════════

def engine_explore(dr_val: int) -> dict:
    """استكشاف مجموعة الجذر الرقمي الكامل"""
    conn = get_db()

    rows = conn.execute(
        "SELECT surah_id, name_ar, jummal_total, digit_root, ayah_count, revelation_type "
        "FROM surahs WHERE digit_root=? ORDER BY surah_id",
        (dr_val,)
    ).fetchall()

    total_surahs = conn.execute("SELECT COUNT(*) FROM surahs").fetchone()[0]
    total_jummal_all = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    total_verses_all = conn.execute("SELECT SUM(ayah_count) FROM surahs").fetchone()[0]
    conn.close()

    surahs = [
        {"id": r[0], "name": r[1], "jummal": r[2], "verses": r[4], "type": r[5]}
        for r in rows
    ]
    count = len(surahs)
    group_jummal = sum(s["jummal"] for s in surahs)
    group_verses = sum(s["verses"] for s in surahs)
    group_jummal_root = digit_root(group_jummal) if group_jummal > 0 else 0
    group_verses_root = digit_root(group_verses) if group_verses > 0 else 0
    makki = sum(1 for s in surahs if s["type"] == "meccan")
    madani = count - makki

    ids = [s["id"] for s in surahs]
    diffs = [ids[i + 1] - ids[i] for i in range(len(ids) - 1)] if len(ids) > 1 else []
    diffs_roots = [digit_root(d) for d in diffs]
    diffs_sum = sum(diffs) if diffs else 0

    # هل يحافظ على جذره؟
    preserves = group_jummal_root == dr_val

    # النجد المعاكس
    # 3↔6, 9↔9, 1↔8, 2↔7, 4↔5
    complement_map = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1, 9: 9}
    complement_root = complement_map.get(dr_val, 9)

    return {
        "digit_root": dr_val,
        "count": count,
        "surahs": surahs,
        "total_jummal": group_jummal,
        "total_jummal_root": group_jummal_root,
        "preserves_root": preserves,
        "total_verses": group_verses,
        "total_verses_root": group_verses_root,
        "makki_count": makki,
        "madani_count": madani,
        "ids_sequence": ids,
        "ids_diffs": diffs,
        "ids_diffs_roots": diffs_roots,
        "diffs_sum": diffs_sum,
        "diffs_sum_root": digit_root(diffs_sum) if diffs_sum > 0 else 0,
        "percentage_of_quran": round(count / total_surahs * 100, 2),
        "percentage_of_total_jummal": round(group_jummal / total_jummal_all * 100, 2),
        "complement_root": complement_root,
    }


def format_explore(r: dict) -> str:
    dr_val = r["digit_root"]
    preserve_mark = "✓" if r["preserves_root"] else f"✗ → {r['total_jummal_root']}"

    lines = [
        f"📊 مجموعة الجذر {dr_val} — {r['count']} سورة ({r['percentage_of_quran']:.1f}% من القرآن)",
        "",
        f"  مجموع الجُمَّل: {r['total_jummal']:,}",
        f"  جذر المجموع:   {r['total_jummal_root']}  {preserve_mark}",
        f"  نسبة الجُمَّل:  {r['percentage_of_total_jummal']:.2f}% من القرآن",
        f"  الآيات: {r['total_verses']:,} (جذر {r['total_verses_root']})",
        f"  مكية: {r['makki_count']} | مدنية: {r['madani_count']}",
        f"  النجد المعاكس: جذر {r['complement_root']}",
        "",
        "  السور:",
    ]
    for s in r["surahs"]:
        rev = "مكية" if s["type"] == "meccan" else "مدنية"
        lines.append(f"    [{s['id']:>3}] {s['name']}: {s['jummal']:,} ({s['verses']} آية) {rev}")

    if r["ids_diffs"]:
        lines.append("")
        lines.append(f"  تسلسل: {r['ids_sequence']}")
        lines.append(f"  الفروق: {r['ids_diffs']}")
        lines.append(f"  جذور الفروق: {r['ids_diffs_roots']}")
        lines.append(f"  مجموع الفروق: {r['diffs_sum']} (جذر {r['diffs_sum_root']})")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  المحرك 3: /match
# ═══════════════════════════════════════════════════════════════════════════════

def engine_match(word: str, scope: str = "all") -> dict:
    """البحث عن كلمة في القرآن مع فلترة وتوزيع"""
    conn = get_db()

    # هل يوجد عمود root_ar؟
    has_root_col = any(
        row[1] == "root_ar"
        for row in conn.execute("PRAGMA table_info(words)").fetchall()
    )

    # بناء شرط النطاق
    if scope == "all":
        scope_cond = ""
        scope_params = []
    elif scope.startswith("root_"):
        dr_val = int(scope.split("_")[1])
        ids = conn.execute(
            "SELECT surah_id FROM surahs WHERE digit_root=?", (dr_val,)
        ).fetchall()
        id_list = ",".join(str(r[0]) for r in ids) or "0"
        scope_cond = f" AND w.surah_id IN ({id_list})"
        scope_params = []
    elif scope == "meccan":
        scope_cond = " AND s.revelation_type='meccan'"
        scope_params = []
    elif scope in ("madani", "medinan"):
        scope_cond = " AND s.revelation_type!='meccan'"
        scope_params = []
    else:
        scope_cond = ""
        scope_params = []

    # التوزيع على السور
    rows = conn.execute(
        f"SELECT w.surah_id, s.name_ar, COUNT(*) as cnt "
        f"FROM words w JOIN surahs s ON w.surah_id=s.surah_id "
        f"WHERE (w.text_clean=? OR w.text_clean LIKE ?){scope_cond} "
        f"GROUP BY w.surah_id ORDER BY cnt DESC",
        [word, f"%{word}%"] + scope_params
    ).fetchall()

    total_count = sum(r[2] for r in rows)
    distribution = {r[1]: r[2] for r in rows}
    top5 = [{"surah": r[1], "count": r[2]} for r in rows[:5]]

    # التوزيع على مجموعات الجذر
    by_root_group = {}
    for dr_val in range(1, 10):
        dr_ids = conn.execute(
            "SELECT surah_id FROM surahs WHERE digit_root=?", (dr_val,)
        ).fetchall()
        id_list = ",".join(str(r[0]) for r in dr_ids) or "0"
        cnt = conn.execute(
            f"SELECT COUNT(*) FROM words w "
            f"WHERE (w.text_clean=? OR w.text_clean LIKE ?) AND w.surah_id IN ({id_list})",
            (word, f"%{word}%")
        ).fetchone()[0]
        by_root_group[dr_val] = cnt

    # السور الغائبة
    all_ids = set(
        r[0] for r in conn.execute("SELECT surah_id FROM surahs").fetchall()
    )
    present_ids = set(r[0] for r in rows)
    absent_ids = sorted(all_ids - present_ids)
    absent_sample = []
    for sid in absent_ids[:8]:
        name = conn.execute(
            "SELECT name_ar FROM surahs WHERE surah_id=?", (sid,)
        ).fetchone()
        if name:
            absent_sample.append({"id": sid, "name": name[0]})

    # ── البحث بالجذر اللغوي ──────────────────────────────────────────────────
    # إذا كانت الكلمة 2-4 أحرف (محتمل جذر) وعمود root_ar موجود → نبحث عنها كجذر
    root_derivatives = []
    root_total = 0
    if has_root_col and 2 <= len(word) <= 4:
        root_rows = conn.execute(
            "SELECT DISTINCT w.text_clean, COUNT(*) as cnt "
            "FROM words w "
            "WHERE w.root_ar=? "
            "GROUP BY w.text_clean ORDER BY cnt DESC LIMIT 12",
            (word,)
        ).fetchall()
        root_total = conn.execute(
            "SELECT COUNT(*) FROM words WHERE root_ar=?", (word,)
        ).fetchone()[0]
        root_derivatives = [{"word": r[0], "count": r[1]} for r in root_rows]

    conn.close()

    return {
        "word": word,
        "scope": scope,
        "total_count": total_count,
        "distribution": distribution,
        "by_root_group": by_root_group,
        "top_5_surahs": top5,
        "absent_count": len(absent_ids),
        "absent_sample": absent_sample,
        "root_total": root_total,
        "root_derivatives": root_derivatives,
    }


def format_match(r: dict) -> str:
    scope_label = ""
    if r["scope"] != "all":
        scope_label = f" [{r['scope']}]"

    lines = [
        f"🔍 «{r['word']}»{scope_label} في القرآن",
        f"  المجموع: {r['total_count']:,} مرة",
    ]

    if r["top_5_surahs"]:
        lines.append("")
        lines.append("  أكثر 5 سور:")
        for s in r["top_5_surahs"]:
            lines.append(f"    {s['surah']}: {s['count']}")

    lines.append("")
    lines.append("  التوزيع على مجموعات الجذر:")
    for dr_val, cnt in r["by_root_group"].items():
        bar = "▓" * min(cnt // max(max(r["by_root_group"].values()), 1) * 10, 10)
        lines.append(f"    جذر {dr_val}: {cnt:>5}  {bar}")

    if r["absent_count"] > 0:
        names = ", ".join(s["name"] for s in r["absent_sample"])
        more = f" و{r['absent_count'] - len(r['absent_sample'])} أخرى" if r["absent_count"] > len(r["absent_sample"]) else ""
        lines.append(f"\n  غائبة عن {r['absent_count']} سورة: {names}{more}")

    # مشتقات الجذر
    if r.get("root_total", 0) > 0:
        lines.append("")
        lines.append(f"  مشتقات الجذر «{r['word']}» — {r['root_total']:,} كلمة:")
        for d in r["root_derivatives"]:
            lines.append(f"    {d['word']}: {d['count']}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  المحرك 4: /correlation
# ═══════════════════════════════════════════════════════════════════════════════

def engine_correlation(spec_a: str, spec_b: str) -> dict:
    """العلاقات الرياضية بين مجموعتين"""
    conn = get_db()
    ga = _get_group(spec_a, conn)
    gb = _get_group(spec_b, conn)
    conn.close()

    if not ga:
        return {"error": f"مجموعة غير معروفة: {spec_a}"}
    if not gb:
        return {"error": f"مجموعة غير معروفة: {spec_b}"}

    ta, tb = ga["total_jummal"], gb["total_jummal"]
    s = ta + tb
    d = abs(ta - tb)
    gcd_val = math.gcd(ta, tb)
    ratio = round(ta / tb, 6) if tb != 0 else None

    # المضاعف المشترك — قد يكون كبيراً جداً
    lcm_val = (ta * tb) // gcd_val if gcd_val > 0 else 0

    # جذور
    s_root = digit_root(s)
    d_root = digit_root(d) if d > 0 else 0
    gcd_root = digit_root(gcd_val)

    # هل يوجد سور مشتركة؟ (يحدث إذا كانت المجموعتان متداخلتين — غير ممكن للجذور)
    shared = len(set(ga["ids"]) & set(gb["ids"]))

    # أنماط ملحوظة
    patterns = []
    if s_root == 9:
        patterns.append(f"مجموع الجُمَّل جذره 9")
    if d_root == s_root:
        patterns.append(f"جذر الفرق = جذر المجموع = {s_root}")
    if ga.get("digit_root") and gb.get("digit_root"):
        dr_sum = ga["digit_root"] + gb["digit_root"]
        if digit_root(dr_sum) == 9:
            patterns.append(f"جذرا المجموعتين ({ga['digit_root']}+{gb['digit_root']}) = {dr_sum} → جذره 9")

    return {
        "group_a": ga,
        "group_b": gb,
        "sum": {"value": s, "root": s_root},
        "difference": {"value": d, "root": d_root},
        "ratio": ratio,
        "gcd": {"value": gcd_val, "root": gcd_root},
        "lcm": lcm_val,
        "count_ratio": f"{ga['count']}:{gb['count']}",
        "count_sum": ga["count"] + gb["count"],
        "count_sum_root": digit_root(ga["count"] + gb["count"]),
        "shared_surahs": shared,
        "patterns": patterns,
    }


def format_correlation(r: dict) -> str:
    if "error" in r:
        return f"خطأ: {r['error']}"

    ga, gb = r["group_a"], r["group_b"]
    lines = [
        f"🔗 {ga['name']} ↔ {gb['name']}",
        "",
        f"  {ga['name']}: {ga['count']} سورة | جُمَّل={ga['total_jummal']:,} (جذر {ga['total_jummal_root']})",
        f"  {gb['name']}: {gb['count']} سورة | جُمَّل={gb['total_jummal']:,} (جذر {gb['total_jummal_root']})",
        "",
        f"  المجموع:   {r['sum']['value']:,}  (جذر {r['sum']['root']})",
        f"  الفرق:     {r['difference']['value']:,}  (جذر {r['difference']['root']})",
        f"  النسبة:    {r['ratio']}",
        f"  القاسم المشترك: {r['gcd']['value']:,}  (جذر {r['gcd']['root']})",
        "",
        f"  عدد السور: {r['count_ratio']} = {r['count_sum']} (جذر {r['count_sum_root']})",
    ]

    if r["patterns"]:
        lines.append("")
        lines.append("  أنماط ملحوظة:")
        for p in r["patterns"]:
            lines.append(f"    • {p}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  المحرك 5: /sequence
# ═══════════════════════════════════════════════════════════════════════════════

NINE_RATIOS = [0.18, 0.27, 0.45, 0.54, 0.72, 0.81]


def engine_sequence(spec: str) -> dict:
    """تحليل تسلسل ترتيب السور في مجموعة"""
    conn = get_db()
    g = _get_group(spec, conn)
    conn.close()

    if not g:
        return {"error": f"مجموعة غير معروفة: {spec}"}

    ids = g["ids"]
    if len(ids) < 2:
        return {"group": g["name"], "ids": ids, "note": "عدد السور قليل جداً"}

    diffs = [ids[i + 1] - ids[i] for i in range(len(ids) - 1)]
    diffs_roots = [digit_root(d) for d in diffs]
    diffs_sum = sum(diffs)

    diff_freq = Counter(diffs)
    root_freq = Counter(diffs_roots)
    most_common = diff_freq.most_common(4)

    # أنماط متكررة
    patterns = []
    for val, freq in most_common:
        if freq >= 2:
            patterns.append(f"الفرق {val} يتكرر {freq} مرات")

    # جذر الفروق الأكثر تكراراً
    most_common_root = root_freq.most_common(1)[0] if root_freq else (None, 0)
    if most_common_root[1] >= 2:
        patterns.append(f"جذر {most_common_root[0]} هو الأكثر في الفروق ({most_common_root[1]} مرات)")

    # نسب التسعة في الفروق
    nine_matches = []
    for d in sorted(set(diffs)):
        for nr in NINE_RATIOS:
            if abs(d / 114 - nr) < 0.015:
                nine_matches.append(f"فرق {d} ≈ {nr} × 114 = {round(nr*114, 1)}")

    return {
        "group": g["name"],
        "count": g["count"],
        "ids": ids,
        "diffs": diffs,
        "diffs_roots": diffs_roots,
        "diffs_sum": diffs_sum,
        "diffs_sum_root": digit_root(diffs_sum),
        "most_common_diffs": most_common,
        "root_distribution": dict(sorted(root_freq.items())),
        "patterns": patterns,
        "nine_ratio_matches": nine_matches,
        "gaps": {
            "min": min(diffs),
            "max": max(diffs),
            "avg": round(sum(diffs) / len(diffs), 2),
        },
    }


def format_sequence(r: dict) -> str:
    if "error" in r:
        return f"خطأ: {r['error']}"
    if "note" in r:
        return f"📈 {r['group']}: {r['note']}"

    lines = [
        f"📈 تسلسل مجموعة {r['group']} — {r['count']} سورة",
        "",
        f"  الأرقام: {r['ids']}",
        f"  الفروق:  {r['diffs']}",
        f"  الجذور:  {r['diffs_roots']}",
        "",
        f"  مجموع الفروق: {r['diffs_sum']} (جذر {r['diffs_sum_root']})",
        f"  الفجوة: صغرى={r['gaps']['min']} | كبرى={r['gaps']['max']} | متوسط={r['gaps']['avg']}",
        "",
        f"  توزيع جذور الفروق: {r['root_distribution']}",
    ]

    if r["patterns"]:
        lines.append("")
        lines.append("  أنماط:")
        for p in r["patterns"]:
            lines.append(f"    • {p}")

    if r["nine_ratio_matches"]:
        lines.append("")
        lines.append("  نسب التسعة:")
        for m in r["nine_ratio_matches"]:
            lines.append(f"    • {m}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  /overview — نظرة شاملة
# ═══════════════════════════════════════════════════════════════════════════════

def engine_overview() -> str:
    """ملخص القرآن كله بالجذور الرقمية"""
    conn = get_db()
    total_jummal = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    total_surahs = conn.execute("SELECT COUNT(*) FROM surahs").fetchone()[0]
    total_verses = conn.execute("SELECT SUM(ayah_count) FROM surahs").fetchone()[0]

    lines = [
        "📊 القرآن الكريم — النظرة الشاملة",
        f"  {total_surahs} سورة | {total_verses:,} آية",
        f"  الجُمَّل الكلي: {total_jummal:,}",
        f"  جذر الكلي: {digit_root(total_jummal)}",
        "",
        "  جذر | سور  |    مجموع الجُمَّل    | جذر | يحافظ؟",
        "  " + "─" * 50,
    ]

    preserving = []
    for dr_val in range(1, 10):
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(jummal_total), 0), COALESCE(SUM(ayah_count), 0) "
            "FROM surahs WHERE digit_root=?",
            (dr_val,)
        ).fetchone()
        count, total, verses = row
        total_root = digit_root(total) if total > 0 else 0
        preserves = total_root == dr_val
        mark = "✓" if preserves else f"✗→{total_root}"
        pct = round(count / total_surahs * 100, 1)

        if preserves:
            preserving.append(dr_val)

        lines.append(
            f"    {dr_val}  | {count:>2} ({pct:>4.1f}%) | {total:>14,} |  {total_root}  |  {mark}"
        )

    conn.close()

    lines.append("")
    lines.append(f"  المجموعات التي تحافظ على جذرها: {preserving}")
    if sorted(preserving) == [3, 6, 9]:
        lines.append("  ← 3 و 6 و 9 فقط ← أرقام تيسلا!")
    elif 9 in preserving and 3 in preserving:
        lines.append("  ← تضم 3 و 9 (النجدان المؤكدان)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  /compare — مقارنة سورتين
# ═══════════════════════════════════════════════════════════════════════════════

def engine_compare(sid_a: int, sid_b: int) -> str:
    """مقارنة رياضية بين سورتين"""
    conn = get_db()

    def get_surah(sid):
        return conn.execute(
            "SELECT surah_id, name_ar, jummal_total, digit_root, ayah_count, revelation_type "
            "FROM surahs WHERE surah_id=?",
            (sid,)
        ).fetchone()

    a = get_surah(sid_a)
    b = get_surah(sid_b)
    conn.close()

    if not a:
        return f"سورة {sid_a} غير موجودة"
    if not b:
        return f"سورة {sid_b} غير موجودة"

    sa, na, ja, dra, aca, reva = a
    sb, nb, jb, drb, acb, revb = b

    diff_j = abs(ja - jb)
    sum_j = ja + jb
    diff_id = abs(sa - sb)
    diff_v = abs(aca - acb)
    gcd_j = math.gcd(ja, jb)
    ratio = round(ja / jb, 4) if jb else None

    notes = []
    if dra == drb:
        notes.append(f"كلاهما جذر {dra}")
    if dra + drb == 9:
        notes.append(f"جذراهما يكملان بعضهما ({dra}+{drb}=9)")
    if digit_root(sum_j) == 9:
        notes.append("مجموع جُمَّلهما جذره 9")
    if digit_root(diff_j) == digit_root(sum_j):
        notes.append(f"جذر الفرق = جذر المجموع = {digit_root(sum_j)}")

    rev_a = "مكية" if reva == "meccan" else "مدنية"
    rev_b = "مكية" if revb == "meccan" else "مدنية"

    lines = [
        f"⚖️ {na} [{sa}] ↔ {nb} [{sb}]",
        "",
        f"  {na}: جُمَّل={ja:,} | جذر={dra} | آيات={aca} | {rev_a}",
        f"  {nb}: جُمَّل={jb:,} | جذر={drb} | آيات={acb} | {rev_b}",
        "",
        f"  المجموع:   {sum_j:,}  (جذر {digit_root(sum_j)})",
        f"  الفرق:     {diff_j:,}  (جذر {digit_root(diff_j) if diff_j > 0 else 0})",
        f"  النسبة:    {ratio}",
        f"  القاسم المشترك: {gcd_j:,}  (جذر {digit_root(gcd_j)})",
        f"  فرق الترتيب: {diff_id}  (جذر {digit_root(diff_id) if diff_id > 0 else 0})",
        f"  فرق الآيات:  {diff_v}  (جذر {digit_root(diff_v) if diff_v > 0 else 0})",
    ]

    if notes:
        lines.append("")
        lines.append("  ملاحظات:")
        for note in notes:
            lines.append(f"    • {note}")

    return "\n".join(lines)
