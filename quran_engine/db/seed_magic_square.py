"""
d369 — بذر المعشّر السحري (المربع السحري 10×10)
99 اسم من أسماء الله الحسنى + محمد ﷺ
كل صف وعمود وقطر = 3394
3394 → 19 (حروف البسملة) → 10 (الأبعاد) → 1 (التوحيد)

الملكية الفكرية: عماد سليمان علوان
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, digit_root, KSA

# المعشّر — 10 صفوف × 10 أعمدة
# كل خلية = (اسم, قيمة جُمَّل)
MAGIC_GRID = [
    # الصف الأول
    [('الله', 66), ('الرحمن', 298), ('الرحيم', 258), ('الملك', 90), ('القدوس', 170),
     ('السلام', 131), ('المتعالي', 551), ('الباري', 213), ('المصور', 336), ('الغفار', 1281)],
    # الصف الثاني
    [('الواحد', 19), ('المعز', 117), ('المقيت', 550), ('الحفيظ', 998), ('القيوم', 156),
     ('المحصي', 148), ('المانع', 161), ('المغني', 1100), ('الحليم', 88), ('المجيد', 57)],
    # الصف الثالث
    [('الحي', 18), ('الخافض', 1481), ('المحيي', 68), ('العليم', 150), ('الواسع', 137),
     ('الشهيد', 319), ('الرءوف', 286), ('النافع', 201), ('الباسط', 72), ('المتكبر', 662)],
    # الصف الرابع
    [('المقتدر', 744), ('الودود', 20), ('الضار', 1001), ('القاهر', 306), ('الفاتح', 489),
     ('البصير', 302), ('مالك الملك', 212), ('المقدم', 184), ('الحسيب', 80), ('المبدئ', 56)],
    # الصف الخامس
    [('الهادي', 20), ('الأحد', 13), ('الباقي', 113), ('الجامع', 114), ('الآخر', 801),
     ('الباعث', 573), ('المميت', 490), ('الظاهر', 1106), ('الحكيم', 78), ('البديع', 86)],
    # الصف السادس
    [('الوهاب', 14), ('غير واضح', 48), ('العظيم', 1020), ('القابض', 903), ('الرقيب', 312),
     ('الشكور', 526), ('الرزاق', 308), ('المعيد', 124), ('الجليل', 73), ('الوكيل', 66)],
    # الصف السابع
    [('الوارث', 707), ('الولي', 46), ('الحميد', 62), ('الكريم', 270), ('المؤخر', 846),
     ('الكبير', 232), ('القوي', 116), ('الصمد', 134), ('الرافع', 351), ('المنتقم', 630)],
    # الصف الثامن
    [('المذل', 770), ('الوالي', 37), ('العدل', 104), ('الصبور', 298), ('المقسط', 209),
     ('المهيمن', 145), ('الرشيد', 514), ('البر', 202), ('الغني', 1060), ('المجيب', 55)],
    # الصف التاسع
    [('الخالق', 731), ('الماجد', 48), ('الحق', 108), ('المؤمن', 136), ('العزيز', 94),
     ('الجبار', 206), ('المتين', 500), ('الباطن', 62), ('ذو الجلال والإكرام', 1100), ('التواب', 409)],
    # الصف العاشر
    [('القادر', 305), ('الغفور', 1286), ('العلي', 110), ('اللطيف', 129), ('السميع', 180),
     ('الخبير', 812), ('النور', 256), ('الحكيم', 68), ('العفو', 156), ('محمد', 92)],
]

EXPECTED_SUM = 3394


def verify_magic_square():
    """التحقق الكامل من المعشّر"""
    size = len(MAGIC_GRID)
    values = [[cell[1] for cell in row] for row in MAGIC_GRID]

    row_sums = [sum(row) for row in values]
    col_sums = [sum(values[r][c] for r in range(size)) for c in range(size)]
    diag1 = sum(values[i][i] for i in range(size))
    diag2 = sum(values[i][size - 1 - i] for i in range(size))

    all_ok = True
    for i, s in enumerate(row_sums):
        if s != EXPECTED_SUM:
            print(f"  FAIL: صف {i+1} = {s} (متوقع {EXPECTED_SUM})")
            all_ok = False
    for i, s in enumerate(col_sums):
        if s != EXPECTED_SUM:
            print(f"  FAIL: عمود {i+1} = {s} (متوقع {EXPECTED_SUM})")
            all_ok = False
    if diag1 != EXPECTED_SUM:
        print(f"  FAIL: قطر ↘ = {diag1}")
        all_ok = False
    if diag2 != EXPECTED_SUM:
        print(f"  FAIL: قطر ↗ = {diag2}")
        all_ok = False

    return all_ok, row_sums, col_sums, [diag1, diag2]


def seed(conn: sqlite3.Connection):
    print("  === المعشّر السحري 10×10 ===")

    is_valid, row_sums, col_sums, diag_sums = verify_magic_square()

    # تخزين الشبكة كـ JSON
    grid_json = json.dumps(
        [[{'name': cell[0], 'value': cell[1]} for cell in row] for row in MAGIC_GRID],
        ensure_ascii=False,
    )

    conn.execute(
        "INSERT OR REPLACE INTO magic_squares "
        "(square_id, name, size, expected_sum, grid_json, "
        "actual_row_sums, actual_col_sums, actual_diag_sums, is_valid, verified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            1,
            'معشّر الأسماء الحسنى — 99 + محمد ﷺ',
            10,
            EXPECTED_SUM,
            grid_json,
            json.dumps(row_sums),
            json.dumps(col_sums),
            json.dumps(diag_sums),
            1 if is_valid else 0,
            datetime.now(KSA).isoformat(),
        ),
    )
    conn.commit()

    status = 'ALL PASS ✓' if is_valid else 'NEEDS FIX'
    print(f"  22 مجموع (10 صفوف + 10 أعمدة + 2 قطر) = {EXPECTED_SUM}")
    print(f"  3394 → {digit_root(3394)} | 19 → {digit_root(19)} | التوحيد")
    print(f"  {status}")

    # القاهر على القطر — إشارة عماد
    diag_names = [MAGIC_GRID[i][i][0] for i in range(10)]
    print(f"  قطر ↘: {' → '.join(diag_names)}")

    # تحديث أسماء الله الحسنى بقيم المعشّر
    print("\n  تحديث names_99 بقيم المعشّر...")
    updated = 0
    for row in MAGIC_GRID:
        for name, value in row:
            if name == 'غير واضح':
                continue
            result = conn.execute(
                "UPDATE names_99 SET jummal_value=?, digit_root=? WHERE arabic=?",
                (value, digit_root(value), name),
            )
            if result.rowcount > 0:
                updated += 1
    conn.commit()
    print(f"  تحديث: {updated} اسم من 100")

    return is_valid


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    seed(conn)
    conn.close()
