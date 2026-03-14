"""
d369 — عيون: محرك البحث والاستكشاف
يرى: القرآن + الجُمَّل + المعشّر + محاور ابن عربي
"""

import json
import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, compute_jummal, digit_root, JUMMAL_MAP

SYMBOLS = ['BTC', 'ETH', 'XRP', 'AVAX']


def get_db():
    return sqlite3.connect(DB_PATH)


# ─── البحث بالجُمَّل ───

def search_by_jummal(value: int, limit: int = 20) -> str:
    """البحث عن آيات بقيمة جُمَّل محددة"""
    conn = get_db()
    rows = conn.execute(
        "SELECT s.name_ar, a.ayah_number, a.text_clean, a.jummal_value, a.digit_root "
        "FROM ayahs a JOIN surahs s ON a.surah_id = s.surah_id "
        "WHERE a.jummal_value = ? LIMIT ?",
        (value, limit),
    ).fetchall()
    conn.close()

    if not rows:
        return f"لا توجد آيات بجُمَّل = {value}"

    lines = [f"🔢 آيات بجُمَّل = {value} (جذر = {digit_root(value)}):"]
    for name, ayah, text, j, dr in rows:
        lines.append(f"  {name}:{ayah} — {text[:80]}...")
    lines.append(f"\n  المجموع: {len(rows)} آية")
    return "\n".join(lines)


def search_by_digit_root(dr: int, limit: int = 30) -> str:
    """البحث عن آيات بجذر رقمي محدد"""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM ayahs WHERE digit_root = ?", (dr,)
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT s.name_ar, a.ayah_number, a.jummal_value, a.text_clean "
        "FROM ayahs a JOIN surahs s ON a.surah_id = s.surah_id "
        "WHERE a.digit_root = ? ORDER BY a.jummal_value DESC LIMIT ?",
        (dr, limit),
    ).fetchall()
    conn.close()

    lines = [f"🔢 آيات جذرها الرقمي = {dr} (المجموع: {count} آية):"]
    for name, ayah, j, text in rows:
        lines.append(f"  {name}:{ayah} [جُمَّل={j}] — {text[:60]}...")
    return "\n".join(lines)


def search_word_jummal(value: int, limit: int = 30) -> str:
    """البحث عن كلمات بقيمة جُمَّل محددة"""
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT w.text_clean, w.jummal_value, s.name_ar, w.ayah_number "
        "FROM words w JOIN surahs s ON w.surah_id = s.surah_id "
        "WHERE w.jummal_value = ? LIMIT ?",
        (value, limit),
    ).fetchall()
    conn.close()

    if not rows:
        return f"لا توجد كلمات بجُمَّل = {value}"

    lines = [f"📝 كلمات بجُمَّل = {value}:"]
    seen = set()
    for word, j, sname, ayah in rows:
        if word not in seen:
            lines.append(f"  «{word}» — {sname}:{ayah}")
            seen.add(word)
    lines.append(f"\n  المجموع: {len(rows)} موضع")
    return "\n".join(lines)


def compute_text_jummal(text: str) -> str:
    """حساب الجُمَّل لنص حر"""
    j = compute_jummal(text)
    dr = digit_root(j)
    letters = [(ch, JUMMAL_MAP[ch]) for ch in text if ch in JUMMAL_MAP]

    lines = [f"📐 جُمَّل «{text}»:"]
    lines.append(f"  القيمة: {j}")
    lines.append(f"  الجذر الرقمي: {dr}")
    if len(letters) <= 20:
        breakdown = " + ".join(f"{ch}({v})" for ch, v in letters)
        lines.append(f"  التفصيل: {breakdown}")
    lines.append(f"  عدد الحروف: {len(letters)}")
    return "\n".join(lines)


# ─── السور ───

def surah_info(surah_id: int) -> str:
    """معلومات سورة بالتفصيل"""
    conn = get_db()
    row = conn.execute(
        "SELECT surah_id, name_ar, name_en, revelation_type, ayah_count, "
        "jummal_total, digit_root, word_count, letter_count "
        "FROM surahs WHERE surah_id = ?",
        (surah_id,),
    ).fetchone()
    if not row:
        conn.close()
        return f"سورة {surah_id} غير موجودة"

    sid, name_ar, name_en, rev, ac, jt, dr, wc, lc = row

    # أعلى وأقل آية
    highest = conn.execute(
        "SELECT ayah_number, jummal_value, text_clean FROM ayahs "
        "WHERE surah_id=? ORDER BY jummal_value DESC LIMIT 1",
        (surah_id,),
    ).fetchone()
    lowest = conn.execute(
        "SELECT ayah_number, jummal_value, text_clean FROM ayahs "
        "WHERE surah_id=? ORDER BY jummal_value ASC LIMIT 1",
        (surah_id,),
    ).fetchone()

    # آيات جذرها 9
    nines = conn.execute(
        "SELECT COUNT(*) FROM ayahs WHERE surah_id=? AND digit_root=9",
        (surah_id,),
    ).fetchone()[0]

    # جُمَّل اسم السورة
    name_jummal = compute_jummal(name_ar)

    conn.close()

    lines = [
        f"📖 سورة {name_ar} ({name_en}) — رقم {sid}",
        f"  النزول: {'مكية' if rev == 'meccan' else 'مدنية'}",
        f"  الآيات: {ac} | الكلمات: {wc:,} | الحروف: {lc:,}",
        f"  جُمَّل السورة: {jt:,} | الجذر: {dr}",
        f"  جُمَّل الاسم: {name_jummal} | جذر الاسم: {digit_root(name_jummal)}",
        f"  آيات جذرها 9: {nines} من {ac}",
    ]
    if highest:
        lines.append(f"  أعلى آية: {highest[0]} [جُمَّل={highest[1]}] — {highest[2][:50]}...")
    if lowest:
        lines.append(f"  أقل آية: {lowest[0]} [جُمَّل={lowest[1]}] — {lowest[2][:50]}...")

    return "\n".join(lines)


def surah_by_name(name: str) -> str:
    """البحث عن سورة بالاسم"""
    conn = get_db()
    row = conn.execute(
        "SELECT surah_id FROM surahs WHERE name_ar LIKE ? OR name_en LIKE ?",
        (f"%{name}%", f"%{name}%"),
    ).fetchone()
    conn.close()
    if row:
        return surah_info(row[0])
    return f"لم أجد سورة باسم «{name}»"


# ─── الأسماء الحسنى ───

def name_info(name: str) -> str:
    """معلومات اسم من أسماء الله الحسنى"""
    conn = get_db()
    row = conn.execute(
        "SELECT name_id, arabic, transliteration, meaning_ar, meaning_en, jummal_value, digit_root "
        "FROM names_99 WHERE arabic LIKE ?",
        (f"%{name}%",),
    ).fetchone()
    if not row:
        conn.close()
        return f"لم أجد اسم «{name}»"

    nid, ar, tr, mar, men, j, dr = row

    # البحث في المعشّر
    sq = conn.execute("SELECT grid_json FROM magic_squares WHERE square_id=1").fetchone()
    position = None
    if sq:
        grid = json.loads(sq[0])
        for r, row_data in enumerate(grid):
            for c, cell in enumerate(row_data):
                if cell['name'] == ar:
                    position = (r + 1, c + 1)
                    break

    # البحث في المحاور
    axis = conn.execute(
        "SELECT axis_id, letter, prophet, surah, cosmic_element, spiritual_energy, zodiac_sign "
        "FROM axes_28 WHERE divine_name = ?",
        (ar,),
    ).fetchone()

    conn.close()

    lines = [
        f"✨ {ar} ({tr})",
        f"  المعنى: {mar} — {men}",
        f"  الترتيب: {nid} | الجُمَّل: {j} | الجذر: {dr}",
    ]
    if position:
        lines.append(f"  المعشّر: صف {position[0]} × عمود {position[1]}")
    if axis:
        aid, letter, prophet, surah, element, energy, zodiac = axis
        lines.append(f"  محور ابن عربي #{aid}: حرف {letter} | نبي: {prophet}")
        lines.append(f"  السورة: {surah} | العنصر: {element}")
        lines.append(f"  الطاقة: {energy} | البرج: {zodiac}")

    return "\n".join(lines)


# ─── المعشّر السحري ───

def magic_square_overview() -> str:
    """نظرة عامة على المعشّر"""
    conn = get_db()
    sq = conn.execute(
        "SELECT name, size, expected_sum, grid_json, is_valid FROM magic_squares WHERE square_id=1"
    ).fetchone()
    conn.close()
    if not sq:
        return "المعشّر غير موجود"

    name, size, expected, grid_json, valid = sq
    grid = json.loads(grid_json)

    lines = [
        f"🔲 {name}",
        f"  الحجم: {size}×{size} | المجموع: {expected}",
        f"  3394 → 19 → 10 → 1",
        f"  التحقق: {'صحيح ✓' if valid else 'يحتاج مراجعة'}",
        "",
        "  القطر الرئيسي ↘:",
    ]
    diag = [grid[i][i] for i in range(size)]
    lines.append("  " + " → ".join(f"{c['name']}({c['value']})" for c in diag))

    return "\n".join(lines)


def magic_square_row(row_num: int) -> str:
    """عرض صف من المعشّر"""
    conn = get_db()
    sq = conn.execute("SELECT grid_json FROM magic_squares WHERE square_id=1").fetchone()
    conn.close()
    if not sq:
        return "المعشّر غير موجود"

    grid = json.loads(sq[0])
    if row_num < 1 or row_num > len(grid):
        return f"الصف {row_num} غير موجود (1-10)"

    row = grid[row_num - 1]
    total = sum(c['value'] for c in row)
    lines = [f"🔲 الصف {row_num} من المعشّر:"]
    for c in row:
        lines.append(f"  {c['name']} = {c['value']} (جذر {digit_root(c['value'])})")
    lines.append(f"  المجموع: {total}")
    return "\n".join(lines)


# ─── محاور ابن عربي ───

def axis_info(axis_id: int) -> str:
    """معلومات محور"""
    conn = get_db()
    row = conn.execute(
        "SELECT axis_id, letter, letter_jummal, divine_name, divine_name_jummal, "
        "prophet, surah, cosmic_element, spiritual_energy, lunar_mansion, zodiac_sign "
        "FROM axes_28 WHERE axis_id = ?",
        (axis_id,),
    ).fetchone()
    conn.close()
    if not row:
        return f"المحور {axis_id} غير موجود"

    aid, letter, lj, dname, dnj, prophet, surah, element, energy, mansion, zodiac = row

    lines = [
        f"🌀 المحور {aid}: حرف «{letter}» (جُمَّل={lj})",
        f"  الاسم الإلهي: {dname} (جُمَّل={dnj}, جذر={digit_root(dnj)})",
        f"  النبي: {prophet}",
        f"  السورة: {surah}",
        f"  العنصر الكوني: {element}",
        f"  الطاقة الروحية: {energy}",
        f"  المنزل القمري: {mansion}",
        f"  البرج: {zodiac}",
    ]
    return "\n".join(lines)


def axis_by_letter(letter: str) -> str:
    """البحث عن محور بالحرف"""
    conn = get_db()
    row = conn.execute(
        "SELECT axis_id FROM axes_28 WHERE letter = ?", (letter,)
    ).fetchone()
    conn.close()
    if row:
        return axis_info(row[0])
    return f"لم أجد محوراً للحرف «{letter}»"


def axes_by_zodiac(zodiac: str) -> str:
    """المحاور المرتبطة ببرج"""
    conn = get_db()
    rows = conn.execute(
        "SELECT axis_id, letter, divine_name, prophet "
        "FROM axes_28 WHERE zodiac_sign LIKE ?",
        (f"%{zodiac}%",),
    ).fetchall()
    conn.close()
    if not rows:
        return f"لم أجد محاور لبرج «{zodiac}»"

    lines = [f"♈ محاور برج {zodiac}:"]
    for aid, letter, dname, prophet in rows:
        lines.append(f"  محور {aid}: {letter} → {dname} → {prophet}")
    return "\n".join(lines)


# ─── النظرة الشاملة ───

def see_now() -> str:
    """نظرة شاملة على القاعدة"""
    conn = get_db()

    stats = {
        'سور': conn.execute("SELECT COUNT(*) FROM surahs").fetchone()[0],
        'آيات': conn.execute("SELECT COUNT(*) FROM ayahs").fetchone()[0],
        'كلمات': conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        'أسماء': conn.execute("SELECT COUNT(*) FROM names_99").fetchone()[0],
        'محاور': conn.execute("SELECT COUNT(*) FROM axes_28").fetchone()[0],
    }

    quran_total = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    nines_surahs = conn.execute("SELECT COUNT(*) FROM surahs WHERE digit_root=9").fetchone()[0]

    # أعلى 3 سور
    top3 = conn.execute(
        "SELECT name_ar, jummal_total FROM surahs ORDER BY jummal_total DESC LIMIT 3"
    ).fetchall()

    # سور جذرها 9
    nine_surahs = conn.execute(
        "SELECT name_ar, jummal_total FROM surahs WHERE digit_root=9 ORDER BY surah_id LIMIT 5"
    ).fetchall()

    conn.close()

    lines = [
        "📊 d369 — النظرة الشاملة",
        "",
        "  الإحصائيات:",
    ]
    for k, v in stats.items():
        lines.append(f"    {k}: {v:,}")

    lines.append(f"\n  مجموع جُمَّل القرآن: {quran_total:,}")
    lines.append(f"  الجذر الرقمي: {digit_root(quran_total)}")
    lines.append(f"  سور جذرها 9: {nines_surahs} من 114")

    lines.append("\n  أعلى 3 سور:")
    for name, total in top3:
        lines.append(f"    {name}: {total:,} (جذر {digit_root(total)})")

    lines.append("\n  سور جذرها 9:")
    for name, total in nine_surahs:
        lines.append(f"    {name}: {total:,}")

    return "\n".join(lines)


# ─── البحث في الآية ───

def ayah_info(surah_id: int, ayah_num: int) -> str:
    """معلومات آية محددة"""
    conn = get_db()
    row = conn.execute(
        "SELECT a.text_clean, a.jummal_value, a.digit_root, a.word_count, a.letter_count, "
        "s.name_ar "
        "FROM ayahs a JOIN surahs s ON a.surah_id = s.surah_id "
        "WHERE a.surah_id=? AND a.ayah_number=?",
        (surah_id, ayah_num),
    ).fetchone()
    if not row:
        conn.close()
        return f"الآية {surah_id}:{ayah_num} غير موجودة"

    text, j, dr, wc, lc, sname = row

    # كلمات الآية
    words = conn.execute(
        "SELECT text_clean, jummal_value, digit_root "
        "FROM words WHERE surah_id=? AND ayah_number=? ORDER BY word_position",
        (surah_id, ayah_num),
    ).fetchall()
    conn.close()

    lines = [
        f"📖 {sname} — الآية {ayah_num}:",
        f"  {text}",
        f"  جُمَّل: {j} | جذر: {dr} | كلمات: {wc} | حروف: {lc}",
        "",
        "  تفصيل الكلمات:",
    ]
    for word, wj, wdr in words:
        lines.append(f"    «{word}» = {wj} (جذر {wdr})")

    return "\n".join(lines)


# ─── مطابقة الأسماء بالقيمة ───

def explore_digit_roots() -> str:
    """تحليل النجدين — توزيع الجذور الرقمية"""
    conn = get_db()

    lines = ["🔬 تحليل النجدين — الجذور الرقمية لـ 114 سورة", ""]

    # التوزيع
    distribution = {}
    for dr in range(1, 10):
        rows = conn.execute(
            "SELECT name_ar, jummal_total FROM surahs WHERE digit_root=? ORDER BY surah_id",
            (dr,),
        ).fetchall()
        total = sum(r[1] for r in rows)
        distribution[dr] = {'count': len(rows), 'total': total, 'surahs': rows}
        lines.append(f"  جذر {dr}: {len(rows)} سورة | جُمَّل = {total:,} (جذر المجموع = {digit_root(total)})")

    # التناظرات
    lines.append("")
    lines.append("═══ النجدان — الأزواج المتممة ═══")
    for a, b in [(9, 1), (8, 2), (7, 3), (6, 4), (5, 5)]:
        da, db = distribution[a], distribution[b]
        total = da['total'] + db['total']
        diff = abs(da['total'] - db['total'])
        lines.append(f"\n  {a}↔{b}: ({da['count']}+{db['count']}={da['count']+db['count']} سورة)")
        lines.append(f"    المجموع: {total:,} (جذر {digit_root(total)})")
        lines.append(f"    الفرق: {diff:,} (جذر {digit_root(diff) if diff > 0 else 0})")

    conn.close()
    return "\n".join(lines)


def explore_surah_group(dr: int) -> str:
    """تفصيل سور بجذر رقمي محدد"""
    conn = get_db()
    rows = conn.execute(
        "SELECT surah_id, name_ar, ayah_count, jummal_total, revelation_type "
        "FROM surahs WHERE digit_root=? ORDER BY surah_id",
        (dr,),
    ).fetchall()
    conn.close()

    if not rows:
        return f"لا توجد سور بجذر {dr}"

    total_j = sum(r[3] for r in rows)
    total_a = sum(r[2] for r in rows)
    meccan = sum(1 for r in rows if r[4] == 'meccan')

    lines = [
        f"📖 سور الجذر {dr} — {len(rows)} سورة:",
        f"  مجموع الجُمَّل: {total_j:,} | الآيات: {total_a:,}",
        f"  مكية: {meccan} | مدنية: {len(rows) - meccan}",
        "",
    ]
    for sid, name, ac, jt, rev in rows:
        lines.append(f"  [{sid}] {name}: {jt:,} ({ac} آية) {'مكية' if rev=='meccan' else 'مدنية'}")

    return "\n".join(lines)


def explore_top_surahs(limit: int = 10) -> str:
    """أكبر السور وجذورها"""
    conn = get_db()
    rows = conn.execute(
        "SELECT surah_id, name_ar, jummal_total, digit_root, ayah_count "
        "FROM surahs ORDER BY jummal_total DESC LIMIT ?",
        (limit,),
    ).fetchall()

    total = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    conn.close()

    lines = [f"📊 أكبر {limit} سور بالجُمَّل:"]
    for sid, name, jt, dr, ac in rows:
        pct = (jt / total) * 100
        lines.append(f"  [{sid}] {name}: {jt:,} (جذر {dr}) — {pct:.1f}% من القرآن ({ac} آية)")

    # توزيع الجذور في الأكبر
    dr_counts = {}
    for _, _, _, dr, _ in rows:
        dr_counts[dr] = dr_counts.get(dr, 0) + 1
    lines.append(f"\n  توزيع الجذور في الأكبر {limit}:")
    for dr in sorted(dr_counts):
        lines.append(f"    جذر {dr}: {dr_counts[dr]} سورة")

    return "\n".join(lines)


def count_word(word: str) -> str:
    """عدّ تكرار كلمة في القرآن"""
    conn = get_db()
    exact = conn.execute(
        "SELECT COUNT(*) FROM words WHERE text_clean=?", (word,)
    ).fetchone()[0]
    contains = conn.execute(
        "SELECT COUNT(*) FROM words WHERE text_clean LIKE ?", (f"%{word}%",)
    ).fetchone()[0]

    # توزيع على السور
    by_surah = conn.execute("""
        SELECT s.name_ar, COUNT(*) as cnt
        FROM words w JOIN surahs s ON w.surah_id = s.surah_id
        WHERE w.text_clean = ?
        GROUP BY w.surah_id ORDER BY cnt DESC LIMIT 10
    """, (word,)).fetchall()

    # في كم سورة
    surah_count = conn.execute("""
        SELECT COUNT(DISTINCT surah_id) FROM words WHERE text_clean=?
    """, (word,)).fetchone()[0]

    j = compute_jummal(word)
    conn.close()

    lines = [
        f"📊 تكرار «{word}» في القرآن:",
        f"  بالضبط: {exact} مرة (في {surah_count} سورة)",
        f"  يحتوي عليها: {contains} كلمة",
        f"  جُمَّل: {j} | جذر: {digit_root(j)}",
        f"  جذر التكرار: {digit_root(exact)}",
    ]
    if by_surah:
        lines.append("\n  أكثر 10 سور:")
        for name, cnt in by_surah:
            lines.append(f"    {name}: {cnt}")
    return "\n".join(lines)


def names_by_jummal(value: int) -> str:
    """البحث عن أسماء بقيمة جُمَّل"""
    conn = get_db()
    rows = conn.execute(
        "SELECT arabic, transliteration, jummal_value, digit_root "
        "FROM names_99 WHERE jummal_value = ?",
        (value,),
    ).fetchall()
    conn.close()
    if not rows:
        return f"لا توجد أسماء بجُمَّل = {value}"

    lines = [f"✨ أسماء بجُمَّل = {value}:"]
    for ar, tr, j, dr in rows:
        lines.append(f"  {ar} ({tr}) — جذر {dr}")
    return "\n".join(lines)
