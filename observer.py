"""
observer.py — المراقب التلقائي لأنماط الحساب متعدد الأنظمة
يفحص 4 أنواع أنماط ويحفظها في جدول discoveries

الملكية الفكرية: عماد سليمان علوان
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from config import DB_PATH, KSA, digit_root

# ─── الحد الأدنى لعدد الأنظمة المتطابقة كي يُعدّ نمطاً ───
MIN_SYSTEMS_CONSENSUS = 3
MIN_SYSTEMS_TESLA = 4
MIN_CONFIDENCE = 0.40  # 40%


def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def _now():
    return datetime.now(KSA).strftime('%Y-%m-%d %H:%M:%S')


def _save_discovery(conn, category: str, title: str, body: dict, confidence: float,
                    surah_ref: int = None, dr: int = None):
    conn.execute("""
        INSERT INTO discoveries (category, claim, evidence, confidence,
                                 digit_root_involved, surah_ref, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'auto', ?)
    """, (category, title, json.dumps(body, ensure_ascii=False),
          confidence, dr, surah_ref, _now()))


# ════════════════════════════════════════════════
# نمط 1: إجماع الأنظمة على آية (قيمة متطابقة)
# ════════════════════════════════════════════════

def pattern_cross_system_consensus(conn, limit=20):
    """آيات قيمتها متطابقة في 3+ أنظمة"""
    print("  [1] إجماع الأنظمة على آية...")
    # نجلب الآيات التي نفس القيمة في عدة أنظمة
    rows = conn.execute("""
        SELECT surah, aya, value, COUNT(DISTINCT system_id) as sys_count,
               GROUP_CONCAT(system_id) as systems
        FROM ayah_calcs
        WHERE system_id <= 5
        GROUP BY surah, aya, value
        HAVING sys_count >= ?
        ORDER BY sys_count DESC, surah, aya
        LIMIT ?
    """, (MIN_SYSTEMS_CONSENSUS, limit * 2)).fetchall()

    saved = 0
    for r in rows:
        surah, aya, value, sys_count = r['surah'], r['aya'], r['value'], r['sys_count']
        systems_ids = [int(x) for x in r['systems'].split(',')]
        confidence = min(0.95, sys_count / 5)

        # جلب أسماء الأنظمة
        placeholders = ','.join('?' * len(systems_ids))
        sys_names = conn.execute(
            f'SELECT name_ar FROM calc_systems WHERE system_id IN ({placeholders})',
            systems_ids
        ).fetchall()
        sys_names = [s[0] for s in sys_names]

        title = f'إجماع {sys_count} أنظمة — سورة {surah} آية {aya} = {value}'
        body = {
            'surah': surah, 'aya': aya, 'value': value,
            'systems_count': sys_count, 'systems': sys_names,
            'digit_root': digit_root(value),
        }
        _save_discovery(conn, 'cross_system_consensus', title, body, confidence,
                        surah_ref=surah, dr=digit_root(value))
        saved += 1
        if saved >= limit:
            break
    print(f"    → {saved} اكتشاف")
    return saved


# ════════════════════════════════════════════════
# نمط 2: نمط تيسلا (جذر 3/6/9) في أنظمة متعددة
# ════════════════════════════════════════════════

def pattern_tesla_ayah(conn, limit=20):
    """آيات جذرها 3 أو 6 أو 9 في 4+ أنظمة"""
    print("  [2] نمط تيسلا في الآيات...")
    rows = conn.execute("""
        SELECT surah, aya, digit_root as dr,
               COUNT(DISTINCT system_id) as sys_count
        FROM ayah_calcs
        WHERE system_id <= 5 AND digit_root IN (3, 6, 9)
        GROUP BY surah, aya, digit_root
        HAVING sys_count >= ?
        ORDER BY sys_count DESC, surah, aya
        LIMIT ?
    """, (MIN_SYSTEMS_TESLA, limit)).fetchall()

    saved = 0
    for r in rows:
        surah, aya, dr, sys_count = r['surah'], r['aya'], r['dr'], r['sys_count']
        confidence = min(0.92, sys_count / 5 * 0.95)
        title = f'تيسلا {dr} — سورة {surah} آية {aya} ({sys_count} أنظمة)'
        body = {
            'surah': surah, 'aya': aya,
            'digit_root': dr, 'systems_count': sys_count,
        }
        _save_discovery(conn, 'tesla_pattern', title, body, confidence,
                        surah_ref=surah, dr=dr)
        saved += 1
    print(f"    → {saved} اكتشاف")
    return saved


# ════════════════════════════════════════════════
# نمط 3: قواسم الجُمَّل = عدد آيات السورة
# ════════════════════════════════════════════════

def _count_divisors(n: int) -> int:
    if n <= 0:
        return 0
    count = 0
    i = 1
    while i * i <= n:
        if n % i == 0:
            count += 2 if i != n // i else 1
        i += 1
    return count


def pattern_divisor_match(conn, limit=20):
    """سور يساوي عدد قواسم جُمَّلها عدد آياتها"""
    print("  [3] نمط القواسم = عدد الآيات...")
    # نجلب من ayah_calcs مجاميع الجُمَّل الكبير لكل سورة
    rows = conn.execute("""
        SELECT ac.surah, SUM(ac.value) as total_jummal,
               COUNT(DISTINCT ac.aya) as aya_count
        FROM ayah_calcs ac
        WHERE ac.system_id = 1
        GROUP BY ac.surah
    """).fetchall()

    saved = 0
    matches = []
    for r in rows:
        surah, total_j, aya_count = r['surah'], r['total_jummal'], r['aya_count']
        if not total_j:
            continue
        divs = _count_divisors(total_j)
        if divs == aya_count:
            matches.append((surah, total_j, aya_count, divs))

    for surah, total_j, aya_count, divs in matches[:limit]:
        confidence = 0.88
        title = f'قواسم السورة {surah} = {divs} = عدد آياتها {aya_count}'
        body = {
            'surah': surah, 'total_jummal': total_j,
            'divisors': divs, 'aya_count': aya_count,
        }
        _save_discovery(conn, 'divisor_pattern', title, body, confidence, surah_ref=surah)
        saved += 1
    print(f"    → {saved} اكتشاف")
    return saved


# ════════════════════════════════════════════════
# نمط 4: كلمات قيمتها متطابقة في 3+ أنظمة
# ════════════════════════════════════════════════

def pattern_word_consensus(conn, limit=20):
    """كلمات قيمتها متطابقة في 3+ أنظمة"""
    print("  [4] إجماع الأنظمة على كلمة...")
    rows = conn.execute("""
        SELECT word_text, value,
               COUNT(DISTINCT system_id) as sys_count,
               GROUP_CONCAT(system_id) as systems
        FROM word_calcs
        WHERE system_id <= 5
        GROUP BY word_text, value
        HAVING sys_count >= ?
        ORDER BY sys_count DESC, value DESC
        LIMIT ?
    """, (MIN_SYSTEMS_CONSENSUS, limit)).fetchall()

    saved = 0
    for r in rows:
        word, value, sys_count = r['word_text'], r['value'], r['sys_count']
        confidence = min(0.90, sys_count / 5)
        title = f'إجماع {sys_count} أنظمة على كلمة "{word}" = {value}'
        body = {
            'word': word, 'value': value,
            'digit_root': digit_root(value),
            'systems_count': sys_count,
        }
        _save_discovery(conn, 'word_pattern', title, body, confidence,
                        dr=digit_root(value))
        saved += 1
    print(f"    → {saved} اكتشاف")
    return saved


# ════════════════════════════════════════════════
# نمط 5: سور ذات جُمَّل رقمي محافظ عبر الأنظمة
# ════════════════════════════════════════════════

def pattern_surah_consistent_dr(conn, limit=10):
    """سور جذرها الرقمي ثابت في كل الأنظمة الخمسة"""
    print("  [5] ثبات جذر السورة عبر الأنظمة...")
    # مجموع كل آيات السورة لكل نظام
    rows = conn.execute("""
        SELECT surah, system_id, SUM(value) as total_val
        FROM ayah_calcs
        WHERE system_id <= 5
        GROUP BY surah, system_id
    """).fetchall()

    # نجمّع: surah → {system_id → dr}
    from collections import defaultdict
    surah_dr = defaultdict(dict)
    for r in rows:
        surah_dr[r['surah']][r['system_id']] = digit_root(r['total_val'] or 0)

    saved = 0
    for surah, sys_map in sorted(surah_dr.items()):
        if len(sys_map) < 5:
            continue
        drs = list(sys_map.values())
        if len(set(drs)) == 1:  # كل الأنظمة نفس الجذر
            dr = drs[0]
            confidence = 0.95
            title = f'السورة {surah} — جذر {dr} في كل الأنظمة الخمسة'
            body = {'surah': surah, 'digit_root': dr, 'systems_checked': 5}
            _save_discovery(conn, 'surah_consistent_dr', title, body, confidence,
                            surah_ref=surah, dr=dr)
            saved += 1
            if saved >= limit:
                break
    print(f"    → {saved} اكتشاف")
    return saved


# ════════════════════════════════════════════════
# المراقب الرئيسي
# ════════════════════════════════════════════════

def run_observer(mode='full', limit_each=20):
    """
    mode='full'  → كل الأنماط
    mode='quick' → أسرع 3 أنماط فقط
    """
    print(f"═══ observer.py — المراقب التلقائي ({mode}) ═══")
    print(f"    {_now()}")

    conn = _conn()

    # نتحقق من وجود الجداول
    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ayah_calcs'"
    ).fetchone()
    if not tbl:
        print("  ✗ جداول ayah_calcs غير موجودة — شغّل upgrade_v3.py أولاً")
        conn.close()
        return

    total = 0
    total += pattern_cross_system_consensus(conn, limit_each)
    total += pattern_tesla_ayah(conn, limit_each)
    total += pattern_word_consensus(conn, limit_each)

    if mode == 'full':
        total += pattern_divisor_match(conn, limit_each)
        total += pattern_surah_consistent_dr(conn, limit_each)

    conn.commit()
    conn.close()
    print(f"\n✓ مجموع الاكتشافات: {total}")
    return total


def get_latest_discoveries(category: str = None, limit: int = 10) -> list:
    """يجلب آخر الاكتشافات من قاعدة البيانات"""
    conn = _conn()
    if category:
        rows = conn.execute("""
            SELECT claim, evidence, confidence, created_at
            FROM discoveries WHERE category=?
            ORDER BY created_at DESC LIMIT ?
        """, (category, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT category, claim, evidence, confidence, created_at
            FROM discoveries
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', default='full', choices=['full', 'quick'])
    parser.add_argument('--limit', type=int, default=20)
    args = parser.parse_args()
    run_observer(mode=args.mode, limit_each=args.limit)
