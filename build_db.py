#!/usr/bin/env python3
"""
d369 — بناء قاعدة البيانات الكاملة
3 + 6 + 9 = 18 → 9

يبني كل شيء من الصفر:
1. إنشاء الجداول (12 جدول)
2. بذر الحروف (28 حرف)
3. استيراد القرآن (6236 آية) + حساب الجُمَّل
4. بذر الأسماء الحسنى (99 + محمد)
5. بذر المعشّر السحري (10×10 = 3394)
6. بذر محاور ابن عربي (28 محور)
7. إحصائيات نهائية

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH

def main():
    print("=" * 60)
    print("  d369 — بناء قاعدة البيانات")
    print("  3 + 6 + 9 = 18 → 9")
    print("=" * 60)

    # حذف القديمة إن وُجدت
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"\n  حُذفت القديمة: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # 1. إنشاء الجداول
    print("\n[1/7] إنشاء الجداول...")
    quran_schema = Path(__file__).parent / "quran_engine" / "db" / "schema.sql"
    astro_schema = Path(__file__).parent / "astro_engine" / "db" / "schema.sql"

    conn.executescript(quran_schema.read_text(encoding="utf-8"))
    print("  quran tables: OK")
    conn.executescript(astro_schema.read_text(encoding="utf-8"))
    print("  astro tables: OK")

    # 2. بذر الحروف
    print("\n[2/7] بذر الحروف...")
    from quran_engine.db.seed_letters import seed as seed_letters
    seed_letters(conn)

    # 3. استيراد القرآن + حساب الجُمَّل
    print("\n[3/7] استيراد القرآن + حساب الجُمَّل...")
    from quran_engine.db.seed_quran import seed as seed_quran
    ok = seed_quran(conn)
    if not ok:
        print("\n  ERROR: الفاتحة لم تمر! أوقف البناء.")
        conn.close()
        sys.exit(1)

    # 4. بذر الأسماء الحسنى
    print("\n[4/7] بذر الأسماء الحسنى...")
    from quran_engine.db.seed_names99 import seed as seed_names
    seed_names(conn)

    # 5. بذر المعشّر السحري + تحديث قيم الأسماء
    print("\n[5/7] بذر المعشّر السحري...")
    from quran_engine.db.seed_magic_square import seed as seed_magic
    seed_magic(conn)

    # 6. بذر محاور ابن عربي
    print("\n[6/7] بذر محاور ابن عربي...")
    from astro_engine.db.seed_axes import seed as seed_axes
    seed_axes(conn)

    # 7. إحصائيات نهائية
    print("\n[7/7] إحصائيات نهائية...")
    stats = {
        "letters": conn.execute("SELECT COUNT(*) FROM letters").fetchone()[0],
        "surahs": conn.execute("SELECT COUNT(*) FROM surahs").fetchone()[0],
        "ayahs": conn.execute("SELECT COUNT(*) FROM ayahs").fetchone()[0],
        "words": conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        "names": conn.execute("SELECT COUNT(*) FROM names_99").fetchone()[0],
        "axes": conn.execute("SELECT COUNT(*) FROM axes_28").fetchone()[0],
        "magic_squares": conn.execute("SELECT COUNT(*) FROM magic_squares").fetchone()[0],
    }
    for k, v in stats.items():
        print(f"  {k}: {v:,}")

    # إحصائيات الجُمَّل
    quran_total = conn.execute("SELECT SUM(jummal_total) FROM surahs").fetchone()[0]
    from config import digit_root
    print(f"\n  مجموع جُمَّل القرآن الكامل: {quran_total:,}")
    print(f"  الجذر الرقمي: {digit_root(quran_total)}")

    # أعلى وأقل سورة
    highest = conn.execute("SELECT name_ar, jummal_total FROM surahs ORDER BY jummal_total DESC LIMIT 1").fetchone()
    lowest = conn.execute("SELECT name_ar, jummal_total FROM surahs ORDER BY jummal_total ASC LIMIT 1").fetchone()
    print(f"  أعلى سورة: {highest[0]} ({highest[1]:,})")
    print(f"  أقل سورة: {lowest[0]} ({lowest[1]:,})")

    # سور جذرها = 9
    nines = conn.execute("SELECT COUNT(*) FROM surahs WHERE digit_root = 9").fetchone()[0]
    print(f"  سور جذرها = 9: {nines} من 114")

    conn.close()

    db_size = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n  حجم القاعدة: {db_size:.1f} MB")
    print(f"  المسار: {DB_PATH}")
    print("\n" + "=" * 60)
    print("  بسم الله — d369 جاهز")
    print("=" * 60)


if __name__ == "__main__":
    main()
