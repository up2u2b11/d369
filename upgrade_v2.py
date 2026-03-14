#!/usr/bin/env python3
"""
d369 — ترقية قاعدة البيانات v2
يضيف: الحساب الخاص-6 + المواقع الدقيقة + اسم بدون أل + بيانات الحروف

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (DB_PATH, compute_jummal, compute_special_6, digit_root,
                    JUMMAL_MAP, SPECIAL_6_MAP)

# ─── بيانات الحروف الإضافية ───
# (letter, special_6, alphabet_order, is_solar, is_lunar, dots)
LETTER_EXTRA = {
    'ا': ('1', 1, 0, 1, 0),
    'ب': ('10', 2, 0, 1, 1),
    'ج': ('111', 5, 0, 1, 1),
    'د': ('1001', 8, 0, 1, 0),
    'ه': ('111111', 28, 0, 1, 0),
    'و': ('111110', 27, 0, 1, 0),
    'ز': ('1100', 11, 0, 1, 1),
    'ح': ('110', 6, 0, 1, 0),
    'ط': ('10111', 16, 1, 0, 0),
    'ي': ('111000', 28, 0, 1, 2),
    'ك': ('100001', 22, 0, 1, 0),
    'ل': ('100011', 23, 1, 0, 0),
    'م': ('100111', 24, 0, 1, 0),
    'ن': ('101111', 25, 1, 0, 1),
    'س': ('1110', 12, 1, 0, 0),
    'ع': ('11110', 18, 0, 1, 0),
    'ف': ('11000', 20, 0, 1, 1),
    'ص': ('10001', 14, 1, 0, 0),
    'ق': ('100000', 21, 0, 1, 2),
    'ر': ('1111', 10, 1, 0, 0),
    'ش': ('10000', 13, 1, 0, 3),
    'ت': ('100', 3, 1, 0, 2),
    'ث': ('101', 4, 1, 0, 3),
    'خ': ('1000', 7, 0, 1, 1),
    'ذ': ('1011', 9, 1, 0, 1),
    'ض': ('10011', 15, 1, 0, 1),
    'ظ': ('11111', 17, 1, 0, 1),
    'غ': ('11100', 19, 0, 1, 1),
}

# ─── ترتيب النزول ───
REVELATION_ORDER = {
    96:1, 68:2, 73:3, 74:4, 1:5, 111:6, 81:7, 87:8, 92:9, 89:10,
    93:11, 94:12, 103:13, 100:14, 108:15, 102:16, 107:17, 109:18, 105:19, 113:20,
    114:21, 112:22, 53:23, 80:24, 97:25, 91:26, 85:27, 95:28, 106:29, 101:30,
    75:31, 104:32, 77:33, 50:34, 90:35, 86:36, 54:37, 38:38, 7:39, 72:40,
    36:41, 25:42, 35:43, 19:44, 20:45, 56:46, 26:47, 27:48, 28:49, 17:50,
    10:51, 11:52, 12:53, 15:54, 6:55, 37:56, 31:57, 34:58, 39:59, 40:60,
    41:61, 42:62, 43:63, 44:64, 45:65, 46:66, 51:67, 88:68, 18:69, 16:70,
    71:71, 14:72, 21:73, 23:74, 32:75, 52:76, 67:77, 69:78, 70:79, 78:80,
    79:81, 82:82, 84:83, 30:84, 29:85, 83:86, 2:87, 8:88, 3:89, 33:90,
    60:91, 4:92, 99:93, 57:94, 47:95, 13:96, 55:97, 76:98, 65:99, 98:100,
    59:101, 24:102, 22:103, 63:104, 58:105, 49:106, 66:107, 64:108, 61:109, 62:110,
    48:111, 5:112, 9:113, 110:114,
}


def upgrade():
    conn = sqlite3.connect(DB_PATH)

    print("=" * 55)
    print("  d369 — ترقية v2")
    print("=" * 55)

    # 1. ترقية المخطط
    print("\n[1/7] ترقية المخطط...")
    alterations = [
        "ALTER TABLE letters ADD COLUMN special_6 TEXT DEFAULT ''",
        "ALTER TABLE letters ADD COLUMN position_alphabet INTEGER DEFAULT 0",
        "ALTER TABLE letters ADD COLUMN is_solar INTEGER DEFAULT 0",
        "ALTER TABLE letters ADD COLUMN is_lunar INTEGER DEFAULT 0",
        "ALTER TABLE letters ADD COLUMN dots_count INTEGER DEFAULT 0",
        "ALTER TABLE surahs ADD COLUMN name_jummal INTEGER DEFAULT 0",
        "ALTER TABLE surahs ADD COLUMN name_digit_root INTEGER DEFAULT 0",
        "ALTER TABLE surahs ADD COLUMN revelation_order INTEGER DEFAULT 0",
        "ALTER TABLE surahs ADD COLUMN jummal_special_6 TEXT DEFAULT '0'",
        "ALTER TABLE ayahs ADD COLUMN ayah_num_quran INTEGER DEFAULT 0",
        "ALTER TABLE ayahs ADD COLUMN jummal_special_6 TEXT DEFAULT '0'",
        "ALTER TABLE words ADD COLUMN word_pos_in_surah INTEGER DEFAULT 0",
        "ALTER TABLE words ADD COLUMN word_pos_in_quran INTEGER DEFAULT 0",
        "ALTER TABLE words ADD COLUMN jummal_special_6 TEXT DEFAULT '0'",
        "ALTER TABLE names_99 ADD COLUMN name_without_al TEXT DEFAULT ''",
        "ALTER TABLE names_99 ADD COLUMN jummal_without_al INTEGER DEFAULT 0",
        "ALTER TABLE names_99 ADD COLUMN quran_mentions INTEGER DEFAULT 0",
    ]
    for sql in alterations:
        try:
            conn.execute(sql)
        except sqlite3.OperationalError as e:
            if 'duplicate column' not in str(e):
                print(f"  skip: {e}")
    # فهارس
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_words_surah_pos ON words(surah_id, word_pos_in_surah)",
        "CREATE INDEX IF NOT EXISTS idx_words_quran_pos ON words(word_pos_in_quran)",
        "CREATE INDEX IF NOT EXISTS idx_words_text ON words(text_clean)",
        "CREATE INDEX IF NOT EXISTS idx_ayahs_quran_num ON ayahs(ayah_num_quran)",
        "CREATE INDEX IF NOT EXISTS idx_surahs_digit ON surahs(digit_root)",
    ]:
        conn.execute(idx_sql)
    conn.commit()
    print("  OK")

    # 2. ترقية الحروف
    print("\n[2/7] ترقية الحروف...")
    for letter, (s6, alpha, solar, lunar, dots) in LETTER_EXTRA.items():
        conn.execute(
            "UPDATE letters SET special_6=?, position_alphabet=?, "
            "is_solar=?, is_lunar=?, dots_count=? WHERE letter=?",
            (s6, alpha, solar, lunar, dots, letter),
        )
    conn.commit()
    print("  28 حرف — بيانات إضافية")

    # 3. ترقية السور — اسم الجُمَّل + ترتيب النزول
    print("\n[3/7] ترقية السور...")
    surahs = conn.execute("SELECT surah_id, name_ar FROM surahs").fetchall()
    for sid, name in surahs:
        nj = compute_jummal(name)
        ndr = digit_root(nj)
        s6 = str(compute_special_6(name))
        rev_order = REVELATION_ORDER.get(sid, 0)

        # حساب الخاص-6 للسورة كاملة
        ayah_s6_total = 0
        ayah_rows = conn.execute(
            "SELECT text_clean FROM ayahs WHERE surah_id=?", (sid,)
        ).fetchall()
        for (text,) in ayah_rows:
            ayah_s6_total += compute_special_6(text)

        conn.execute(
            "UPDATE surahs SET name_jummal=?, name_digit_root=?, "
            "revelation_order=?, jummal_special_6=? WHERE surah_id=?",
            (nj, ndr, rev_order, str(ayah_s6_total), sid),
        )
    conn.commit()
    print(f"  114 سورة — اسم الجُمَّل + ترتيب النزول + خاص-6")

    # 4. ترقية الآيات — رقم في القرآن + خاص-6
    print("\n[4/7] ترقية الآيات...")
    ayahs = conn.execute(
        "SELECT ayah_id, surah_id, ayah_number, text_clean FROM ayahs ORDER BY surah_id, ayah_number"
    ).fetchall()
    quran_ayah_num = 0
    for aid, sid, anum, text in ayahs:
        quran_ayah_num += 1
        s6 = compute_special_6(text)
        conn.execute(
            "UPDATE ayahs SET ayah_num_quran=?, jummal_special_6=? WHERE ayah_id=?",
            (quran_ayah_num, str(s6), aid),
        )
    conn.commit()
    print(f"  {quran_ayah_num} آية — رقم عام + خاص-6")

    # 5. ترقية الكلمات — مواقع + خاص-6
    print("\n[5/7] ترقية الكلمات...")
    quran_word_pos = 0
    surah_word_pos = {}

    words = conn.execute(
        "SELECT word_id, surah_id, text_clean FROM words "
        "ORDER BY surah_id, ayah_number, word_position"
    ).fetchall()

    for wid, sid, text in words:
        quran_word_pos += 1
        surah_word_pos[sid] = surah_word_pos.get(sid, 0) + 1
        s6 = compute_special_6(text)
        conn.execute(
            "UPDATE words SET word_pos_in_surah=?, word_pos_in_quran=?, jummal_special_6=? "
            "WHERE word_id=?",
            (surah_word_pos[sid], quran_word_pos, str(s6), wid),
        )
    conn.commit()
    print(f"  {quran_word_pos} كلمة — مواقع + خاص-6")

    # 6. ترقية الأسماء — بدون أل
    print("\n[6/7] ترقية الأسماء...")
    names = conn.execute("SELECT name_id, arabic FROM names_99").fetchall()
    for nid, name in names:
        without_al = re.sub(r'^ال', '', name)
        j_without = compute_jummal(without_al)
        conn.execute(
            "UPDATE names_99 SET name_without_al=?, jummal_without_al=? WHERE name_id=?",
            (without_al, j_without, nid),
        )
    conn.commit()
    print(f"  {len(names)} اسم — بدون أل")

    # 7. تحقق
    print("\n[7/7] التحقق...")
    # خاص-6 للبسملة
    bsm = "بسم الله الرحمن الرحيم"
    s6_val = compute_special_6(bsm)
    print(f"  بسملة خاص-6: {s6_val}")
    print(f"  بسملة تقليدي: {compute_jummal(bsm)}")

    # القاهر بدون أل
    qaher = conn.execute(
        "SELECT arabic, jummal_value, name_without_al, jummal_without_al "
        "FROM names_99 WHERE arabic LIKE '%قاهر%'"
    ).fetchone()
    if qaher:
        print(f"  {qaher[0]}={qaher[1]} | {qaher[2]}={qaher[3]}")

    # موقع أول كلمة وآخر كلمة
    first = conn.execute(
        "SELECT text_clean, word_pos_in_quran FROM words ORDER BY word_pos_in_quran ASC LIMIT 1"
    ).fetchone()
    last = conn.execute(
        "SELECT text_clean, word_pos_in_quran FROM words ORDER BY word_pos_in_quran DESC LIMIT 1"
    ).fetchone()
    print(f"  أول كلمة: «{first[0]}» #{first[1]}")
    print(f"  آخر كلمة: «{last[0]}» #{last[1]}")

    conn.close()
    print("\n  v2 جاهز")


if __name__ == "__main__":
    upgrade()
