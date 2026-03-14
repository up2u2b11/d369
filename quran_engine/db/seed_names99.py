"""
d369 — بذر أسماء الله الحسنى الـ99 + محمد ﷺ
القيم محسوبة بحساب الجُمَّل المشرقي
"""

import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, compute_jummal, digit_root

# الأسماء الحسنى — 99 اسم + محمد ﷺ = 100
# الترتيب التقليدي المتداول
NAMES_99 = [
    (1, 'الله', 'Allah', 'الإله المعبود', 'God'),
    (2, 'الرحمن', 'Ar-Rahman', 'الرحمن', 'The Most Gracious'),
    (3, 'الرحيم', 'Ar-Raheem', 'الرحيم', 'The Most Merciful'),
    (4, 'الملك', 'Al-Malik', 'المالك', 'The King'),
    (5, 'القدوس', 'Al-Quddus', 'المنزه', 'The Holy'),
    (6, 'السلام', 'As-Salam', 'السلام', 'The Peace'),
    (7, 'المؤمن', 'Al-Mu\'min', 'المؤمن', 'The Granter of Security'),
    (8, 'المهيمن', 'Al-Muhaymin', 'المهيمن', 'The Guardian'),
    (9, 'العزيز', 'Al-Aziz', 'العزيز', 'The Almighty'),
    (10, 'الجبار', 'Al-Jabbar', 'الجبار', 'The Compeller'),
    (11, 'المتكبر', 'Al-Mutakabbir', 'المتكبر', 'The Supreme'),
    (12, 'الخالق', 'Al-Khaliq', 'الخالق', 'The Creator'),
    (13, 'البارئ', 'Al-Bari', 'البارئ', 'The Originator'),
    (14, 'المصور', 'Al-Musawwir', 'المصور', 'The Fashioner'),
    (15, 'الغفار', 'Al-Ghaffar', 'الغفار', 'The Forgiver'),
    (16, 'القهار', 'Al-Qahhar', 'القهار', 'The Subduer'),
    (17, 'الوهاب', 'Al-Wahhab', 'الوهاب', 'The Bestower'),
    (18, 'الرزاق', 'Ar-Razzaq', 'الرزاق', 'The Provider'),
    (19, 'الفتاح', 'Al-Fattah', 'الفتاح', 'The Opener'),
    (20, 'العليم', 'Al-Aleem', 'العليم', 'The All-Knowing'),
    (21, 'القابض', 'Al-Qabid', 'القابض', 'The Constrictor'),
    (22, 'الباسط', 'Al-Basit', 'الباسط', 'The Expander'),
    (23, 'الخافض', 'Al-Khafid', 'الخافض', 'The Abaser'),
    (24, 'الرافع', 'Ar-Rafi', 'الرافع', 'The Exalter'),
    (25, 'المعز', 'Al-Mu\'izz', 'المعز', 'The Honourer'),
    (26, 'المذل', 'Al-Mudhill', 'المذل', 'The Dishonourer'),
    (27, 'السميع', 'As-Sami', 'السميع', 'The All-Hearing'),
    (28, 'البصير', 'Al-Basir', 'البصير', 'The All-Seeing'),
    (29, 'الحكم', 'Al-Hakam', 'الحكم', 'The Judge'),
    (30, 'العدل', 'Al-Adl', 'العدل', 'The Just'),
    (31, 'اللطيف', 'Al-Latif', 'اللطيف', 'The Subtle'),
    (32, 'الخبير', 'Al-Khabir', 'الخبير', 'The All-Aware'),
    (33, 'الحليم', 'Al-Halim', 'الحليم', 'The Forbearing'),
    (34, 'العظيم', 'Al-Azim', 'العظيم', 'The Magnificent'),
    (35, 'الغفور', 'Al-Ghafur', 'الغفور', 'The Forgiving'),
    (36, 'الشكور', 'Ash-Shakur', 'الشكور', 'The Grateful'),
    (37, 'العلي', 'Al-Ali', 'العلي', 'The Most High'),
    (38, 'الكبير', 'Al-Kabir', 'الكبير', 'The Greatest'),
    (39, 'الحفيظ', 'Al-Hafiz', 'الحفيظ', 'The Preserver'),
    (40, 'المقيت', 'Al-Muqit', 'المقيت', 'The Sustainer'),
    (41, 'الحسيب', 'Al-Hasib', 'الحسيب', 'The Reckoner'),
    (42, 'الجليل', 'Al-Jalil', 'الجليل', 'The Majestic'),
    (43, 'الكريم', 'Al-Karim', 'الكريم', 'The Generous'),
    (44, 'الرقيب', 'Ar-Raqib', 'الرقيب', 'The Watchful'),
    (45, 'المجيب', 'Al-Mujib', 'المجيب', 'The Responsive'),
    (46, 'الواسع', 'Al-Wasi', 'الواسع', 'The All-Encompassing'),
    (47, 'الحكيم', 'Al-Hakim', 'الحكيم', 'The Wise'),
    (48, 'الودود', 'Al-Wadud', 'الودود', 'The Loving'),
    (49, 'المجيد', 'Al-Majid', 'المجيد', 'The Glorious'),
    (50, 'الباعث', 'Al-Ba\'ith', 'الباعث', 'The Resurrector'),
    (51, 'الشهيد', 'Ash-Shahid', 'الشهيد', 'The Witness'),
    (52, 'الحق', 'Al-Haqq', 'الحق', 'The Truth'),
    (53, 'الوكيل', 'Al-Wakil', 'الوكيل', 'The Trustee'),
    (54, 'القوي', 'Al-Qawi', 'القوي', 'The Strong'),
    (55, 'المتين', 'Al-Matin', 'المتين', 'The Firm'),
    (56, 'الولي', 'Al-Wali', 'الولي', 'The Protector'),
    (57, 'الحميد', 'Al-Hamid', 'الحميد', 'The Praiseworthy'),
    (58, 'المحصي', 'Al-Muhsi', 'المحصي', 'The Accounter'),
    (59, 'المبدئ', 'Al-Mubdi', 'المبدئ', 'The Originator'),
    (60, 'المعيد', 'Al-Mu\'id', 'المعيد', 'The Restorer'),
    (61, 'المحيي', 'Al-Muhyi', 'المحيي', 'The Giver of Life'),
    (62, 'المميت', 'Al-Mumit', 'المميت', 'The Taker of Life'),
    (63, 'الحي', 'Al-Hayy', 'الحي', 'The Living'),
    (64, 'القيوم', 'Al-Qayyum', 'القيوم', 'The Self-Subsisting'),
    (65, 'الواجد', 'Al-Wajid', 'الواجد', 'The Finder'),
    (66, 'الماجد', 'Al-Majid', 'الماجد', 'The Noble'),
    (67, 'الواحد', 'Al-Wahid', 'الواحد', 'The One'),
    (68, 'الصمد', 'As-Samad', 'الصمد', 'The Eternal'),
    (69, 'القادر', 'Al-Qadir', 'القادر', 'The Able'),
    (70, 'المقتدر', 'Al-Muqtadir', 'المقتدر', 'The Powerful'),
    (71, 'المقدم', 'Al-Muqaddim', 'المقدم', 'The Expediter'),
    (72, 'المؤخر', 'Al-Mu\'akhkhir', 'المؤخر', 'The Delayer'),
    (73, 'الأول', 'Al-Awwal', 'الأول', 'The First'),
    (74, 'الآخر', 'Al-Akhir', 'الآخر', 'The Last'),
    (75, 'الظاهر', 'Az-Zahir', 'الظاهر', 'The Manifest'),
    (76, 'الباطن', 'Al-Batin', 'الباطن', 'The Hidden'),
    (77, 'الوالي', 'Al-Wali', 'الوالي', 'The Governor'),
    (78, 'المتعالي', 'Al-Muta\'ali', 'المتعالي', 'The Most Exalted'),
    (79, 'البر', 'Al-Barr', 'البر', 'The Source of Goodness'),
    (80, 'التواب', 'At-Tawwab', 'التواب', 'The Acceptor of Repentance'),
    (81, 'المنتقم', 'Al-Muntaqim', 'المنتقم', 'The Avenger'),
    (82, 'العفو', 'Al-Afuww', 'العفو', 'The Pardoner'),
    (83, 'الرؤوف', 'Ar-Ra\'uf', 'الرؤوف', 'The Compassionate'),
    (84, 'مالك الملك', 'Malik al-Mulk', 'مالك الملك', 'Owner of Sovereignty'),
    (85, 'ذو الجلال والإكرام', 'Dhul-Jalali wal-Ikram', 'ذو الجلال والإكرام', 'Lord of Majesty'),
    (86, 'المقسط', 'Al-Muqsit', 'المقسط', 'The Equitable'),
    (87, 'الجامع', 'Al-Jami', 'الجامع', 'The Gatherer'),
    (88, 'الغني', 'Al-Ghani', 'الغني', 'The Self-Sufficient'),
    (89, 'المغني', 'Al-Mughni', 'المغني', 'The Enricher'),
    (90, 'المانع', 'Al-Mani', 'المانع', 'The Preventer'),
    (91, 'الضار', 'Ad-Darr', 'الضار', 'The Distresser'),
    (92, 'النافع', 'An-Nafi', 'النافع', 'The Propitious'),
    (93, 'النور', 'An-Nur', 'النور', 'The Light'),
    (94, 'الهادي', 'Al-Hadi', 'الهادي', 'The Guide'),
    (95, 'البديع', 'Al-Badi', 'البديع', 'The Originator'),
    (96, 'الباقي', 'Al-Baqi', 'الباقي', 'The Everlasting'),
    (97, 'الوارث', 'Al-Warith', 'الوارث', 'The Inheritor'),
    (98, 'الرشيد', 'Ar-Rashid', 'الرشيد', 'The Guide to the Right Path'),
    (99, 'الصبور', 'As-Sabur', 'الصبور', 'The Patient'),
    (100, 'محمد', 'Muhammad', 'النبي ﷺ', 'The Prophet'),
]


def seed(conn: sqlite3.Connection):
    count = 0
    for nid, arabic, translit, meaning_ar, meaning_en in NAMES_99:
        j = compute_jummal(arabic)
        dr = digit_root(j)
        conn.execute(
            "INSERT OR REPLACE INTO names_99 "
            "(name_id, arabic, transliteration, meaning_ar, meaning_en, jummal_value, digit_root) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nid, arabic, translit, meaning_ar, meaning_en, j, dr),
        )
        count += 1
    conn.commit()
    print(f"  names_99: {count} اسم")

    # تحقق سريع
    allah = conn.execute("SELECT jummal_value FROM names_99 WHERE name_id=1").fetchone()
    muhammad = conn.execute("SELECT jummal_value FROM names_99 WHERE name_id=100").fetchone()
    print(f"  تحقق: الله={allah[0]} (متوقع=66) | محمد={muhammad[0]} (متوقع=92)")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    seed(conn)
    conn.close()
