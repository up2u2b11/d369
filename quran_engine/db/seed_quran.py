"""
d369 — استيراد النص القرآني + حساب الجُمَّل
رواية حفص عن عاصم — الرسم العثماني المبسط (Tanzil)

يستورد → يحسب الجُمَّل لكل كلمة → آية → سورة
"""

import re
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, QURAN_TEXT, compute_jummal, digit_root, JUMMAL_MAP

# تشكيل للإزالة
DIACRITICS = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

# أسماء السور (114)
SURAH_NAMES = {
    1: ('الفاتحة', 'Al-Fatiha', 'meccan'),
    2: ('البقرة', 'Al-Baqara', 'medinan'),
    3: ('آل عمران', 'Aal-Imran', 'medinan'),
    4: ('النساء', 'An-Nisa', 'medinan'),
    5: ('المائدة', 'Al-Ma\'ida', 'medinan'),
    6: ('الأنعام', 'Al-An\'am', 'meccan'),
    7: ('الأعراف', 'Al-A\'raf', 'meccan'),
    8: ('الأنفال', 'Al-Anfal', 'medinan'),
    9: ('التوبة', 'At-Tawba', 'medinan'),
    10: ('يونس', 'Yunus', 'meccan'),
    11: ('هود', 'Hud', 'meccan'),
    12: ('يوسف', 'Yusuf', 'meccan'),
    13: ('الرعد', 'Ar-Ra\'d', 'medinan'),
    14: ('إبراهيم', 'Ibrahim', 'meccan'),
    15: ('الحجر', 'Al-Hijr', 'meccan'),
    16: ('النحل', 'An-Nahl', 'meccan'),
    17: ('الإسراء', 'Al-Isra', 'meccan'),
    18: ('الكهف', 'Al-Kahf', 'meccan'),
    19: ('مريم', 'Maryam', 'meccan'),
    20: ('طه', 'Ta-Ha', 'meccan'),
    21: ('الأنبياء', 'Al-Anbiya', 'meccan'),
    22: ('الحج', 'Al-Hajj', 'medinan'),
    23: ('المؤمنون', 'Al-Mu\'minun', 'meccan'),
    24: ('النور', 'An-Nur', 'medinan'),
    25: ('الفرقان', 'Al-Furqan', 'meccan'),
    26: ('الشعراء', 'Ash-Shu\'ara', 'meccan'),
    27: ('النمل', 'An-Naml', 'meccan'),
    28: ('القصص', 'Al-Qasas', 'meccan'),
    29: ('العنكبوت', 'Al-Ankabut', 'meccan'),
    30: ('الروم', 'Ar-Rum', 'meccan'),
    31: ('لقمان', 'Luqman', 'meccan'),
    32: ('السجدة', 'As-Sajda', 'meccan'),
    33: ('الأحزاب', 'Al-Ahzab', 'medinan'),
    34: ('سبأ', 'Saba', 'meccan'),
    35: ('فاطر', 'Fatir', 'meccan'),
    36: ('يس', 'Ya-Sin', 'meccan'),
    37: ('الصافات', 'As-Saffat', 'meccan'),
    38: ('ص', 'Sad', 'meccan'),
    39: ('الزمر', 'Az-Zumar', 'meccan'),
    40: ('غافر', 'Ghafir', 'meccan'),
    41: ('فصلت', 'Fussilat', 'meccan'),
    42: ('الشورى', 'Ash-Shura', 'meccan'),
    43: ('الزخرف', 'Az-Zukhruf', 'meccan'),
    44: ('الدخان', 'Ad-Dukhan', 'meccan'),
    45: ('الجاثية', 'Al-Jathiya', 'meccan'),
    46: ('الأحقاف', 'Al-Ahqaf', 'meccan'),
    47: ('محمد', 'Muhammad', 'medinan'),
    48: ('الفتح', 'Al-Fath', 'medinan'),
    49: ('الحجرات', 'Al-Hujurat', 'medinan'),
    50: ('ق', 'Qaf', 'meccan'),
    51: ('الذاريات', 'Adh-Dhariyat', 'meccan'),
    52: ('الطور', 'At-Tur', 'meccan'),
    53: ('النجم', 'An-Najm', 'meccan'),
    54: ('القمر', 'Al-Qamar', 'meccan'),
    55: ('الرحمن', 'Ar-Rahman', 'medinan'),
    56: ('الواقعة', 'Al-Waqi\'a', 'meccan'),
    57: ('الحديد', 'Al-Hadid', 'medinan'),
    58: ('المجادلة', 'Al-Mujadila', 'medinan'),
    59: ('الحشر', 'Al-Hashr', 'medinan'),
    60: ('الممتحنة', 'Al-Mumtahina', 'medinan'),
    61: ('الصف', 'As-Saff', 'medinan'),
    62: ('الجمعة', 'Al-Jumu\'a', 'medinan'),
    63: ('المنافقون', 'Al-Munafiqun', 'medinan'),
    64: ('التغابن', 'At-Taghabun', 'medinan'),
    65: ('الطلاق', 'At-Talaq', 'medinan'),
    66: ('التحريم', 'At-Tahrim', 'medinan'),
    67: ('الملك', 'Al-Mulk', 'meccan'),
    68: ('القلم', 'Al-Qalam', 'meccan'),
    69: ('الحاقة', 'Al-Haqqa', 'meccan'),
    70: ('المعارج', 'Al-Ma\'arij', 'meccan'),
    71: ('نوح', 'Nuh', 'meccan'),
    72: ('الجن', 'Al-Jinn', 'meccan'),
    73: ('المزمل', 'Al-Muzzammil', 'meccan'),
    74: ('المدثر', 'Al-Muddaththir', 'meccan'),
    75: ('القيامة', 'Al-Qiyama', 'meccan'),
    76: ('الإنسان', 'Al-Insan', 'medinan'),
    77: ('المرسلات', 'Al-Mursalat', 'meccan'),
    78: ('النبأ', 'An-Naba', 'meccan'),
    79: ('النازعات', 'An-Nazi\'at', 'meccan'),
    80: ('عبس', 'Abasa', 'meccan'),
    81: ('التكوير', 'At-Takwir', 'meccan'),
    82: ('الانفطار', 'Al-Infitar', 'meccan'),
    83: ('المطففين', 'Al-Mutaffifin', 'meccan'),
    84: ('الانشقاق', 'Al-Inshiqaq', 'meccan'),
    85: ('البروج', 'Al-Buruj', 'meccan'),
    86: ('الطارق', 'At-Tariq', 'meccan'),
    87: ('الأعلى', 'Al-A\'la', 'meccan'),
    88: ('الغاشية', 'Al-Ghashiya', 'meccan'),
    89: ('الفجر', 'Al-Fajr', 'meccan'),
    90: ('البلد', 'Al-Balad', 'meccan'),
    91: ('الشمس', 'Ash-Shams', 'meccan'),
    92: ('الليل', 'Al-Layl', 'meccan'),
    93: ('الضحى', 'Ad-Duha', 'meccan'),
    94: ('الشرح', 'Ash-Sharh', 'meccan'),
    95: ('التين', 'At-Tin', 'meccan'),
    96: ('العلق', 'Al-Alaq', 'meccan'),
    97: ('القدر', 'Al-Qadr', 'meccan'),
    98: ('البينة', 'Al-Bayyina', 'medinan'),
    99: ('الزلزلة', 'Az-Zalzala', 'medinan'),
    100: ('العاديات', 'Al-Adiyat', 'meccan'),
    101: ('القارعة', 'Al-Qari\'a', 'meccan'),
    102: ('التكاثر', 'At-Takathur', 'meccan'),
    103: ('العصر', 'Al-Asr', 'meccan'),
    104: ('الهمزة', 'Al-Humaza', 'meccan'),
    105: ('الفيل', 'Al-Fil', 'meccan'),
    106: ('قريش', 'Quraysh', 'meccan'),
    107: ('الماعون', 'Al-Ma\'un', 'meccan'),
    108: ('الكوثر', 'Al-Kawthar', 'meccan'),
    109: ('الكافرون', 'Al-Kafirun', 'meccan'),
    110: ('النصر', 'An-Nasr', 'medinan'),
    111: ('المسد', 'Al-Masad', 'meccan'),
    112: ('الإخلاص', 'Al-Ikhlas', 'meccan'),
    113: ('الفلق', 'Al-Falaq', 'meccan'),
    114: ('الناس', 'An-Nas', 'meccan'),
}


def clean_text(text: str) -> str:
    """إزالة التشكيل من النص"""
    return DIACRITICS.sub('', text)


def count_letters(text: str) -> int:
    """عدد الحروف (بدون مسافات وعلامات)"""
    clean = clean_text(text)
    return sum(1 for ch in clean if ch in JUMMAL_MAP)


def seed(conn: sqlite3.Connection):
    quran_path = QURAN_TEXT
    if not quran_path.exists():
        print(f"  ERROR: {quran_path} not found")
        return

    # 1. بذر السور
    for sid in range(1, 115):
        name_ar, name_en, rev = SURAH_NAMES.get(sid, (f'سورة {sid}', f'Surah {sid}', 'meccan'))
        conn.execute(
            "INSERT OR REPLACE INTO surahs (surah_id, name_ar, name_en, revelation_type) "
            "VALUES (?, ?, ?, ?)",
            (sid, name_ar, name_en, rev),
        )
    conn.commit()
    print(f"  surahs: 114 سورة")

    # 2. قراءة وبذر الآيات والكلمات
    ayah_count = 0
    word_count = 0

    with open(quran_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split('|', 2)
            if len(parts) != 3:
                continue

            surah_id = int(parts[0])
            ayah_num = int(parts[1])
            text = parts[2]
            clean = clean_text(text)

            # حساب الجُمَّل للآية
            j = compute_jummal(text)
            dr = digit_root(j)
            wc = len(clean.split())
            lc = count_letters(text)

            conn.execute(
                "INSERT OR REPLACE INTO ayahs "
                "(surah_id, ayah_number, text_uthmani, text_clean, jummal_value, digit_root, word_count, letter_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (surah_id, ayah_num, text, clean, j, dr, wc, lc),
            )
            ayah_id = conn.execute(
                "SELECT ayah_id FROM ayahs WHERE surah_id=? AND ayah_number=?",
                (surah_id, ayah_num),
            ).fetchone()[0]
            ayah_count += 1

            # 3. بذر الكلمات
            words = clean.split()
            for pos, word in enumerate(words, 1):
                wj = compute_jummal(word)
                wdr = digit_root(wj)
                wlc = sum(1 for ch in word if ch in JUMMAL_MAP)
                conn.execute(
                    "INSERT INTO words "
                    "(ayah_id, surah_id, ayah_number, word_position, text_uthmani, text_clean, "
                    "jummal_value, digit_root, letter_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (ayah_id, surah_id, ayah_num, pos, word, word, wj, wdr, wlc),
                )
                word_count += 1

    conn.commit()
    print(f"  ayahs: {ayah_count} آية")
    print(f"  words: {word_count} كلمة")

    # 4. تحديث إحصائيات السور
    conn.execute("""
        UPDATE surahs SET
            ayah_count = (SELECT COUNT(*) FROM ayahs WHERE ayahs.surah_id = surahs.surah_id),
            jummal_total = (SELECT COALESCE(SUM(jummal_value), 0) FROM ayahs WHERE ayahs.surah_id = surahs.surah_id),
            word_count = (SELECT COALESCE(SUM(word_count), 0) FROM ayahs WHERE ayahs.surah_id = surahs.surah_id),
            letter_count = (SELECT COALESCE(SUM(letter_count), 0) FROM ayahs WHERE ayahs.surah_id = surahs.surah_id)
    """)
    conn.execute("""
        UPDATE surahs SET digit_root = CASE
            WHEN jummal_total > 0 THEN (jummal_total - 1) % 9 + 1
            ELSE 0
        END
    """)
    conn.commit()

    # 5. التحقق — الفاتحة
    print("\n  === اختبار الفاتحة ===")
    fatiha_expected = [(1, 786), (2, 582), (3, 618), (4, 242), (5, 836), (6, 1073), (7, 6010)]
    all_ok = True
    for ayah_num, expected in fatiha_expected:
        row = conn.execute(
            "SELECT jummal_value FROM ayahs WHERE surah_id=1 AND ayah_number=?", (ayah_num,)
        ).fetchone()
        actual = row[0] if row else None
        ok = 'OK' if actual == expected else 'FAIL'
        if actual != expected:
            all_ok = False
        print(f"  1:{ayah_num} = {actual} (expected {expected}) {ok}")

    print(f"\n  {'ALL PASS' if all_ok else 'NEEDS FIX'}")
    return all_ok


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    seed(conn)
    conn.close()
