"""
d369 — محرك البحث القرآني
10 أنظمة حساب + 7 وظائف بحث

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_PATH, compute_jummal, compute_special_6, digit_root, JUMMAL_MAP


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════
#  وظيفة 1: حساب جُمَّل نص
# ═══════════════════════════════════════════════════════

def compute_all(text: str) -> dict:
    """حساب قيمة النص في جميع الأنظمة المتاحة"""
    trad = compute_jummal(text)
    s6 = compute_special_6(text)
    dr = digit_root(trad)
    letters = [(ch, JUMMAL_MAP.get(ch, 0)) for ch in text if ch in JUMMAL_MAP]

    return {
        'text': text,
        'traditional': trad,
        'special_6': s6,
        'digit_root': dr,
        'letter_count': len(letters),
        'breakdown': [{'letter': ch, 'traditional': v} for ch, v in letters],
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 2: بحث بالعدد
# ═══════════════════════════════════════════════════════

def search_by_number(number: int, system: str = 'traditional',
                     scope: str = 'words', limit: int = 100) -> dict:
    """البحث عن كل الكلمات/الآيات بقيمة محددة"""
    conn = get_db()

    if scope == 'words':
        col = 'jummal_value' if system == 'traditional' else 'jummal_special_6'
        val = number if system == 'traditional' else str(number)
        rows = conn.execute(f"""
            SELECT w.text_clean, w.jummal_value, w.jummal_special_6,
                   w.word_position, w.word_pos_in_surah, w.word_pos_in_quran,
                   w.letter_count, w.digit_root,
                   s.surah_id, s.name_ar, w.ayah_number,
                   a.text_clean as ayah_text, a.jummal_value as ayah_jummal,
                   a.word_count as ayah_word_count, a.letter_count as ayah_letter_count,
                   a.ayah_num_quran,
                   s.jummal_total as surah_jummal, s.ayah_count as surah_ayah_count,
                   s.word_count as surah_word_count, s.letter_count as surah_letter_count
            FROM words w
            JOIN surahs s ON w.surah_id = s.surah_id
            JOIN ayahs a ON w.ayah_id = a.ayah_id
            WHERE w.{col} = ?
            ORDER BY w.word_pos_in_quran
            LIMIT ?
        """, (val, limit)).fetchall()

        total = conn.execute(f"SELECT COUNT(*) FROM words WHERE {col}=?", (val,)).fetchone()[0]

    elif scope == 'ayahs':
        col = 'jummal_value' if system == 'traditional' else 'jummal_special_6'
        val = number if system == 'traditional' else str(number)
        rows = conn.execute(f"""
            SELECT a.text_clean, a.jummal_value, a.jummal_special_6,
                   a.ayah_number, a.ayah_num_quran, a.word_count, a.letter_count,
                   a.digit_root,
                   s.surah_id, s.name_ar
            FROM ayahs a
            JOIN surahs s ON a.surah_id = s.surah_id
            WHERE a.{col} = ?
            ORDER BY a.ayah_num_quran
            LIMIT ?
        """, (val, limit)).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM ayahs WHERE {col}=?", (val,)).fetchone()[0]

    conn.close()

    return {
        'number': number,
        'system': system,
        'scope': scope,
        'total_matches': total,
        'matches': [dict(r) for r in rows],
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 3: قواسم العدد
# ═══════════════════════════════════════════════════════

def get_divisors(number: int) -> dict:
    """قواسم العدد مع الجذور الرقمية والتوافقات"""
    if number <= 0:
        return {'number': number, 'divisors': []}

    divisors = []
    for i in range(1, int(number**0.5) + 1):
        if number % i == 0:
            q = number // i
            divisors.append({
                'divisor': i,
                'quotient': q,
                'divisor_dr': digit_root(i),
                'quotient_dr': digit_root(q),
            })
            if i != q:
                divisors.append({
                    'divisor': q,
                    'quotient': i,
                    'divisor_dr': digit_root(q),
                    'quotient_dr': digit_root(i),
                })

    divisors.sort(key=lambda x: x['divisor'])

    # البحث عن أسماء بنفس القيمة
    conn = get_db()
    name_matches = []
    for d in divisors:
        for val in [d['divisor'], d['quotient']]:
            names = conn.execute(
                "SELECT arabic, jummal_value FROM names_99 WHERE jummal_value=?",
                (val,),
            ).fetchall()
            for n in names:
                name_matches.append({
                    'name': n['arabic'],
                    'value': n['jummal_value'],
                    'from_divisor': d['divisor'],
                })
    conn.close()

    return {
        'number': number,
        'digit_root': digit_root(number),
        'divisor_count': len(divisors),
        'divisors': divisors,
        'name_matches': name_matches,
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 4: تفاصيل آية كاملة
# ═══════════════════════════════════════════════════════

def get_ayah_detail(surah_id: int, ayah_num: int) -> dict:
    """كل المعلومات عن آية — مثل تطبيق جُمَّل"""
    conn = get_db()

    ayah = conn.execute("""
        SELECT a.*, s.name_ar, s.name_en, s.jummal_total as surah_jummal,
               s.ayah_count as surah_ayah_count, s.word_count as surah_word_count,
               s.letter_count as surah_letter_count, s.jummal_special_6 as surah_s6
        FROM ayahs a JOIN surahs s ON a.surah_id = s.surah_id
        WHERE a.surah_id=? AND a.ayah_number=?
    """, (surah_id, ayah_num)).fetchone()

    if not ayah:
        conn.close()
        return None

    words = conn.execute("""
        SELECT * FROM words
        WHERE surah_id=? AND ayah_number=?
        ORDER BY word_position
    """, (surah_id, ayah_num)).fetchall()

    conn.close()

    return {
        'position': {
            'surah_id': ayah['surah_id'],
            'surah_name': ayah['name_ar'],
            'ayah_in_surah': ayah['ayah_number'],
            'ayah_in_quran': ayah['ayah_num_quran'],
        },
        'counts': {
            'surah_ayah_count': ayah['surah_ayah_count'],
            'surah_word_count': ayah['surah_word_count'],
            'surah_letter_count': ayah['surah_letter_count'],
            'ayah_word_count': ayah['word_count'],
            'ayah_letter_count': ayah['letter_count'],
        },
        'jummal': {
            'traditional': {
                'surah': ayah['surah_jummal'],
                'ayah': ayah['jummal_value'],
            },
            'special_6': {
                'surah': ayah['surah_s6'],
                'ayah': ayah['jummal_special_6'],
            },
        },
        'text': ayah['text_clean'],
        'digit_root': ayah['digit_root'],
        'words': [{
            'text': w['text_clean'],
            'position': w['word_position'],
            'pos_in_surah': w['word_pos_in_surah'],
            'pos_in_quran': w['word_pos_in_quran'],
            'jummal': w['jummal_value'],
            'special_6': w['jummal_special_6'],
            'digit_root': w['digit_root'],
            'letter_count': w['letter_count'],
        } for w in words],
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 5: بحث بالجذر الرقمي
# ═══════════════════════════════════════════════════════

def search_by_digit_root(root: int, scope: str = 'surahs') -> dict:
    """البحث بالجذر الرقمي"""
    conn = get_db()

    if scope == 'surahs':
        rows = conn.execute("""
            SELECT surah_id, name_ar, jummal_total, ayah_count,
                   word_count, letter_count, revelation_type, revelation_order
            FROM surahs WHERE digit_root=? ORDER BY surah_id
        """, (root,)).fetchall()
        total_jummal = sum(r['jummal_total'] for r in rows)
    elif scope == 'ayahs':
        rows = conn.execute("""
            SELECT a.surah_id, s.name_ar, a.ayah_number, a.jummal_value,
                   a.word_count, a.ayah_num_quran
            FROM ayahs a JOIN surahs s ON a.surah_id = s.surah_id
            WHERE a.digit_root=? ORDER BY a.ayah_num_quran LIMIT 200
        """, (root,)).fetchall()
        total_jummal = conn.execute(
            "SELECT COALESCE(SUM(jummal_value),0) FROM ayahs WHERE digit_root=?",
            (root,),
        ).fetchone()[0]
    elif scope == 'names':
        rows = conn.execute("""
            SELECT name_id, arabic, jummal_value, name_without_al, jummal_without_al
            FROM names_99 WHERE digit_root=? ORDER BY name_id
        """, (root,)).fetchall()
        total_jummal = sum(r['jummal_value'] for r in rows)

    total_count = len(rows)
    conn.close()

    return {
        'digit_root': root,
        'scope': scope,
        'total_count': total_count,
        'total_jummal': total_jummal,
        'total_jummal_dr': digit_root(total_jummal) if total_jummal > 0 else 0,
        'matches': [dict(r) for r in rows],
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 6: بحث التوافقات
# ═══════════════════════════════════════════════════════

def find_matches(text: str) -> dict:
    """البحث عن كل التوافقات لنص معين"""
    j = compute_jummal(text)
    s6 = compute_special_6(text)
    dr = digit_root(j)

    conn = get_db()

    # أسماء بنفس القيمة
    names_match = conn.execute(
        "SELECT arabic, jummal_value, name_without_al, jummal_without_al "
        "FROM names_99 WHERE jummal_value=? OR jummal_without_al=?",
        (j, j),
    ).fetchall()

    # أسماء بنفس الجذر
    names_dr = conn.execute(
        "SELECT arabic, jummal_value FROM names_99 WHERE digit_root=?",
        (dr,),
    ).fetchall()

    # كلمات قرآنية بنفس القيمة
    word_count = conn.execute(
        "SELECT COUNT(*) FROM words WHERE jummal_value=?", (j,)
    ).fetchone()[0]

    # آيات بنفس القيمة
    ayah_count = conn.execute(
        "SELECT COUNT(*) FROM ayahs WHERE jummal_value=?", (j,)
    ).fetchone()[0]

    # محاور ابن عربي
    axes = conn.execute(
        "SELECT axis_id, letter, divine_name, prophet, zodiac_sign "
        "FROM axes_28 WHERE divine_name_jummal=?",
        (j,),
    ).fetchall()

    conn.close()

    return {
        'text': text,
        'traditional': j,
        'special_6': s6,
        'digit_root': dr,
        'names_exact': [dict(n) for n in names_match],
        'names_same_root': [dict(n) for n in names_dr],
        'quran_words_count': word_count,
        'quran_ayahs_count': ayah_count,
        'axes_match': [dict(a) for a in axes],
    }


# ═══════════════════════════════════════════════════════
#  وظيفة 7: اكتشاف الأنماط
# ═══════════════════════════════════════════════════════

def discover_patterns() -> dict:
    """البحث التلقائي عن أنماط في البيانات"""
    conn = get_db()
    patterns = []

    # 1. توزيع الجذور
    dr_dist = {}
    for dr in range(1, 10):
        count = conn.execute(
            "SELECT COUNT(*) FROM surahs WHERE digit_root=?", (dr,)
        ).fetchone()[0]
        total = conn.execute(
            "SELECT COALESCE(SUM(jummal_total),0) FROM surahs WHERE digit_root=?", (dr,)
        ).fetchone()[0]
        dr_dist[dr] = {'count': count, 'total': total, 'total_dr': digit_root(total) if total > 0 else 0}

    # 2. التناظرات (مجموعها 10)
    symmetries = []
    for a in range(9, 4, -1):
        b = 10 - a
        da, db = dr_dist[a], dr_dist[b]
        combined = da['total'] + db['total']
        diff = abs(da['total'] - db['total'])
        symmetries.append({
            'pair': f"{a}↔{b}",
            'counts': f"{da['count']}+{db['count']}={da['count']+db['count']}",
            'combined_total': combined,
            'combined_dr': digit_root(combined),
            'difference': diff,
            'difference_dr': digit_root(diff) if diff > 0 else 0,
        })

    # 3. سور بجُمَّل متطابق مع أسماء
    surah_name_matches = conn.execute("""
        SELECT s.surah_id, s.name_ar, s.name_jummal, n.arabic, n.jummal_value
        FROM surahs s
        JOIN names_99 n ON s.name_jummal = n.jummal_value
        ORDER BY s.surah_id
    """).fetchall()

    # 4. كلمات تتكرر بعدد = جذرها الرقمي
    freq_patterns = conn.execute("""
        SELECT text_clean, jummal_value, digit_root, COUNT(*) as freq
        FROM words
        GROUP BY text_clean
        HAVING COUNT(*) = digit_root AND digit_root > 1
        ORDER BY freq DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return {
        'digit_root_distribution': dr_dist,
        'symmetries': symmetries,
        'surah_name_matches': [dict(r) for r in surah_name_matches],
        'frequency_patterns': [dict(r) for r in freq_patterns],
    }
