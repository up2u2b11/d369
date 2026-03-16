"""
upgrade_v3.py — ترقية d369.db إلى الإصدار 3
يُنشئ: calc_systems + ayah_calcs + word_calcs
يملأ: 5 أنظمة مدمجة + حسابات كاملة

الملكية الفكرية: عماد سليمان علوان
"""

import sys
import json
import sqlite3
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, JUMMAL_MAP, SPECIAL_6_MAP, digit_root
from calc_engine import (
    calc_kabir, calc_saghir, calc_ordinal,
    calc_lettercount, calc_special6, _load_ordinal
)

_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

# ─── الأنظمة الثمانية ───
SYSTEMS = [
    {
        'system_id': 1,
        'name': 'kabir',
        'name_ar': 'الجُمَّل الكبير',
        'description': 'الأبجد الكلاسيكي — ا=1 ب=2 ... غ=1000',
        'mapping_json': json.dumps(JUMMAL_MAP, ensure_ascii=False),
        'apply_digit_reduction': 0,
        'is_builtin': 1,
        'is_active': 1,
    },
    {
        'system_id': 2,
        'name': 'saghir',
        'name_ar': 'الجُمَّل الصغير',
        'description': 'جذر رقمي لكل حرف من الكبير — ا=1 ي=1 ك=2...',
        'mapping_json': None,
        'apply_digit_reduction': 1,
        'is_builtin': 1,
        'is_active': 1,
    },
    {
        'system_id': 3,
        'name': 'ordinal',
        'name_ar': 'الترتيب الأبجدي',
        'description': 'ترتيب الحرف في الأبجدية — ا=1 ب=2 ... غ=28',
        'mapping_json': None,
        'apply_digit_reduction': 0,
        'is_builtin': 1,
        'is_active': 1,
    },
    {
        'system_id': 4,
        'name': 'lettercount',
        'name_ar': 'عدد الحروف',
        'description': 'كل حرف = 1 — مجموع الحروف فقط',
        'mapping_json': None,
        'apply_digit_reduction': 0,
        'is_builtin': 1,
        'is_active': 1,
    },
    {
        'system_id': 5,
        'name': 'special6',
        'name_ar': 'الخاص-6',
        'description': 'تشفير شبه ثنائي — ا=1 ب=10 ج=111...',
        'mapping_json': json.dumps(
            {k: v for k, v in SPECIAL_6_MAP.items()}, ensure_ascii=False
        ),
        'apply_digit_reduction': 0,
        'is_builtin': 1,
        'is_active': 1,
    },
    {
        'system_id': 6,
        'name': 'cust_1',
        'name_ar': 'مخصص-1',
        'description': 'نظام مخصص للمستخدم رقم 1',
        'mapping_json': None,
        'apply_digit_reduction': 0,
        'is_builtin': 0,
        'is_active': 0,
    },
    {
        'system_id': 7,
        'name': 'cust_2',
        'name_ar': 'مخصص-2',
        'description': 'نظام مخصص للمستخدم رقم 2',
        'mapping_json': None,
        'apply_digit_reduction': 0,
        'is_builtin': 0,
        'is_active': 0,
    },
    {
        'system_id': 8,
        'name': 'cust_3',
        'name_ar': 'مخصص-3',
        'description': 'نظام مخصص للمستخدم رقم 3',
        'mapping_json': None,
        'apply_digit_reduction': 0,
        'is_builtin': 0,
        'is_active': 0,
    },
]

CALC_FUNCS = {
    1: calc_kabir,
    2: calc_saghir,
    3: calc_ordinal,
    4: calc_lettercount,
    5: calc_special6,
}


def create_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS calc_systems (
        system_id   INTEGER PRIMARY KEY,
        name        TEXT NOT NULL UNIQUE,
        name_ar     TEXT NOT NULL,
        description TEXT,
        mapping_json TEXT,
        apply_digit_reduction INTEGER DEFAULT 0,
        is_builtin  INTEGER DEFAULT 1,
        is_active   INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ayah_calcs (
        calc_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        surah       INTEGER NOT NULL,
        aya         INTEGER NOT NULL,
        system_id   INTEGER NOT NULL,
        value       INTEGER,
        digit_root  INTEGER,
        UNIQUE(surah, aya, system_id),
        FOREIGN KEY(system_id) REFERENCES calc_systems(system_id)
    );
    CREATE INDEX IF NOT EXISTS idx_ayah_calcs_surah
        ON ayah_calcs(surah, aya);
    CREATE INDEX IF NOT EXISTS idx_ayah_calcs_value
        ON ayah_calcs(system_id, value);

    CREATE TABLE IF NOT EXISTS word_calcs (
        calc_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        word_text   TEXT NOT NULL,
        system_id   INTEGER NOT NULL,
        value       INTEGER,
        digit_root  INTEGER,
        UNIQUE(word_text, system_id),
        FOREIGN KEY(system_id) REFERENCES calc_systems(system_id)
    );
    CREATE INDEX IF NOT EXISTS idx_word_calcs_text
        ON word_calcs(word_text);
    CREATE INDEX IF NOT EXISTS idx_word_calcs_value
        ON word_calcs(system_id, value);
    """)
    conn.commit()
    print("✓ الجداول جاهزة")


def fill_systems(conn):
    for s in SYSTEMS:
        conn.execute("""
            INSERT OR IGNORE INTO calc_systems
            (system_id, name, name_ar, description, mapping_json,
             apply_digit_reduction, is_builtin, is_active)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            s['system_id'], s['name'], s['name_ar'], s['description'],
            s['mapping_json'], s['apply_digit_reduction'],
            s['is_builtin'], s['is_active']
        ))
    conn.commit()
    print(f"✓ الأنظمة: {len(SYSTEMS)} نظام")


def fill_ayah_calcs(conn):
    # تحميل كل الآيات من ref_ayat
    ayahs = conn.execute(
        'SELECT surah, aya, text_clean FROM ref_ayat ORDER BY surah, aya'
    ).fetchall()
    print(f"  آيات: {len(ayahs)} — يحسب 5 أنظمة × كل آية...")

    batch = []
    for i, (surah, aya, text) in enumerate(ayahs):
        t = text or ''
        for sid, fn in CALC_FUNCS.items():
            v = fn(t)
            dr = digit_root(v)
            batch.append((surah, aya, sid, v, dr))
        if (i + 1) % 500 == 0:
            print(f"    {i+1}/{len(ayahs)}...")

    conn.executemany("""
        INSERT OR REPLACE INTO ayah_calcs (surah, aya, system_id, value, digit_root)
        VALUES (?,?,?,?,?)
    """, batch)
    conn.commit()
    print(f"✓ ayah_calcs: {len(batch)} صف")


def fill_word_calcs(conn):
    # كلمات فريدة من ref_words
    words = conn.execute(
        'SELECT DISTINCT word_text FROM ref_words WHERE word_text IS NOT NULL'
    ).fetchall()
    unique_words = [r[0] for r in words if r[0]]
    print(f"  كلمات فريدة: {len(unique_words)} — يحسب 5 أنظمة × كل كلمة...")

    batch = []
    for i, word in enumerate(unique_words):
        for sid, fn in CALC_FUNCS.items():
            v = fn(word)
            dr = digit_root(v)
            batch.append((word, sid, v, dr))
        if (i + 1) % 2000 == 0:
            print(f"    {i+1}/{len(unique_words)}...")

    conn.executemany("""
        INSERT OR REPLACE INTO word_calcs (word_text, system_id, value, digit_root)
        VALUES (?,?,?,?)
    """, batch)
    conn.commit()
    print(f"✓ word_calcs: {len(batch)} صف")


def verify(conn):
    counts = {
        'calc_systems': conn.execute('SELECT COUNT(*) FROM calc_systems').fetchone()[0],
        'ayah_calcs':   conn.execute('SELECT COUNT(*) FROM ayah_calcs').fetchone()[0],
        'word_calcs':   conn.execute('SELECT COUNT(*) FROM word_calcs').fetchone()[0],
    }
    print("\n═══ التحقق ═══")
    for k, v in counts.items():
        print(f"  {k}: {v:,}")
    # عينة — الفاتحة آية 1 بكل الأنظمة
    rows = conn.execute("""
        SELECT cs.name_ar, ac.value, ac.digit_root
        FROM ayah_calcs ac JOIN calc_systems cs ON ac.system_id=cs.system_id
        WHERE ac.surah=1 AND ac.aya=1
        ORDER BY ac.system_id
    """).fetchall()
    print("\n  الفاتحة آية 1:")
    for r in rows:
        print(f"    {r[0]}: {r[1]} (ج={r[2]})")


def main():
    print("═══ upgrade_v3.py — ترقية d369.db ═══")
    _load_ordinal()  # تحميل خريطة الترتيب
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('PRAGMA journal_mode=WAL')
    create_tables(conn)
    fill_systems(conn)
    fill_ayah_calcs(conn)
    fill_word_calcs(conn)
    verify(conn)
    conn.close()
    print("\n✓ الترقية مكتملة")


if __name__ == '__main__':
    main()
