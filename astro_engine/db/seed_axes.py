"""
d369 — بذر محاور ابن عربي الـ28
كل حرف عربي مرتبط بـ: اسم إلهي، نبي، سورة، عنصر كوني، طاقة روحية، نجم، برج
"""

import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, JUMMAL_MAP, compute_jummal, digit_root

# المحاور الـ28 — ترتيب أبجدي (ا ب ج د ...)
# المصدر: جدول ابن عربي من الفتوحات المكية
AXES_28 = [
    # (axis_id, letter, divine_name, cosmic_element, surah, prophet, spiritual_energy, lunar_mansion, zodiac)
    (1, 'ا', 'البديع', 'القلم/الأعلى', 'القلم/الأعلى', 'آدم', 'إلهي', 'ثريا', 'الثور'),
    (2, 'ه', 'الباعث', 'اللوح المحفوظ', 'الضحى', 'شيث', 'نفثي', 'دبران', 'الثور'),
    (3, 'ع', 'الباطن', 'الطبيعة', 'القدر', 'نوح', 'سبوحي', 'ذراع', 'الجوزاء'),
    (4, 'ح', 'الآخر', 'الهباء', 'الليل', 'إدريس', 'قدوسي', 'نثرة', 'الجوزاء'),
    (5, 'غ', 'الظاهر', 'الجسم الكلي', 'البينة', 'إبراهيم', 'مهيمني', 'مقعه', 'السرطان'),
    (6, 'خ', 'الحكيم', 'الشكل الكلي', 'التين', 'إسحاق', 'حمي', 'هنعه', 'السرطان'),
    (7, 'ق', 'المحيط', 'العرش', 'الفجر', 'إسماعيل', 'علي', 'ذراع', 'الأسد'),
    (8, 'ك', 'الشكور', 'الكرسي', 'الشمس', 'يعقوب', 'روحي', 'نثرة', 'الأسد'),
    (9, 'ج', 'الغني', 'فلك البروج', 'الإخلاص', 'يوسف', 'نوري', 'طرف', 'السرطان'),
    (10, 'ش', 'القدير', 'فلك المنازل', 'الفيل', 'هود', 'أحدي', 'ظرف', 'السرطان'),
    (11, 'ي', 'الرب', 'سماء زحل', 'قريش', 'صالح', 'فاتحي', 'زبرة', 'الأسد'),
    (12, 'ض', 'العليم', 'سماء المشتري', 'التكاثر', 'شعيب', 'قلبي', 'صرفه', 'العذراء'),
    (13, 'ل', 'القاهر', 'سماء المريخ', 'القارعة', 'لوط', 'ملكي', 'عواء', 'العذراء'),
    (14, 'ن', 'النور', 'سماء الشمس', 'العاديات', 'عزير', 'قدري', 'سماك', 'الميزان'),
    (15, 'ر', 'المصور', 'سماء الزهرة', 'العصر', 'عيسى', 'نبوي', 'غفر', 'الميزان'),
    (16, 'ط', 'المحصي', 'سماء الكتب (محتمل)', 'الهمزة', 'سليمان', 'رحماني', 'زبانا', 'العقرب'),
    (17, 'د', 'المبين', 'سماء القمر', 'الماعون', 'داود', 'وجودي', 'إكليل', 'العقرب'),
    (18, 'ت', 'القابض', 'كرة النار', 'المسد', 'يونس', 'نفسي', 'قلب', 'القوس'),
    (19, 'ز', 'الحي', 'كرة الهواء', 'الشرح', 'أيوب', 'غيبي', 'شونه', 'القوس'),
    (20, 'س', 'المحيي', 'كرة الماء', 'الكوثر', 'يحيى', 'جلالي', 'نحام', 'الجدي'),
    (21, 'ص', 'المميت', 'كرة التراب', 'البلد', 'زكريا', 'ملكي', 'بندة', 'الجدي'),
    (22, 'ظ', 'العزيز', 'المعدن', 'النصر', 'إلياس', 'إيناسي', 'سعد الذابح', 'الجدي'),
    (23, 'ث', 'الرزاق', 'النبات', 'الزلزلة', 'لقمان', 'إحساني', 'سعد المانع', 'الدلو'),
    (24, 'د', 'المذل', 'الحيواني', 'الكافرون', 'هارون', 'إمامي', 'سعد السعود', 'الدلو'),
    (25, 'ف', 'القوي', 'الملائكة', 'الفلق', 'موسى', 'علوي', 'سعد الأخبية', 'الحوت'),
    (26, 'ب', 'اللطيف', 'الجن', 'الناس', 'خالد', 'صمدي', 'مقدم', 'الحوت'),
    (27, 'م', 'الجامع', 'الإنسان', 'الفاتحة', 'محمد', 'فردي', 'مؤخر', 'الحوت'),
    (28, 'و', 'رفيع الدرجات', 'تعيين المراتب', 'كل القرآن', 'الخاتم', 'الخاتم', 'رثاء', 'الحوت'),
]


def seed(conn: sqlite3.Connection):
    count = 0
    for axis_id, letter, divine_name, cosmic_element, surah, prophet, spiritual_energy, lunar_mansion, zodiac in AXES_28:
        letter_jummal = JUMMAL_MAP.get(letter, 0)
        divine_jummal = compute_jummal(divine_name)
        conn.execute(
            "INSERT OR REPLACE INTO axes_28 "
            "(axis_id, letter, letter_jummal, divine_name, divine_name_jummal, prophet, "
            "surah, cosmic_element, spiritual_energy, lunar_mansion, zodiac_sign) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (axis_id, letter, letter_jummal, divine_name, divine_jummal, prophet,
             surah, cosmic_element, spiritual_energy, lunar_mansion, zodiac),
        )
        count += 1
    conn.commit()
    print(f"  axes_28: {count} محور")

    # تحقق — المحور الأول والأخير
    first = conn.execute("SELECT letter, divine_name, prophet FROM axes_28 WHERE axis_id=1").fetchone()
    last = conn.execute("SELECT letter, divine_name, prophet FROM axes_28 WHERE axis_id=28").fetchone()
    print(f"  تحقق: محور 1 = {first[0]} / {first[1]} / {first[2]}")
    print(f"  تحقق: محور 28 = {last[0]} / {last[1]} / {last[2]}")

    # إحصائيات
    zodiac_count = conn.execute("SELECT COUNT(DISTINCT zodiac_sign) FROM axes_28").fetchone()[0]
    prophet_count = conn.execute("SELECT COUNT(DISTINCT prophet) FROM axes_28").fetchone()[0]
    print(f"  أبراج: {zodiac_count} | أنبياء: {prophet_count}")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    seed(conn)
    conn.close()
