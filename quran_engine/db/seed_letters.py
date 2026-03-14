"""
d369 — بذر الحروف العربية الـ28 بقيم الجُمَّل
الترتيب الأبجدي المشرقي
"""

import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH, digit_root

LETTERS = [
    # (id, letter, name, jummal)
    (1, 'ا', 'ألف', 1),
    (2, 'ب', 'باء', 2),
    (3, 'ج', 'جيم', 3),
    (4, 'د', 'دال', 4),
    (5, 'ه', 'هاء', 5),
    (6, 'و', 'واو', 6),
    (7, 'ز', 'زاي', 7),
    (8, 'ح', 'حاء', 8),
    (9, 'ط', 'طاء', 9),
    (10, 'ي', 'ياء', 10),
    (11, 'ك', 'كاف', 20),
    (12, 'ل', 'لام', 30),
    (13, 'م', 'ميم', 40),
    (14, 'ن', 'نون', 50),
    (15, 'س', 'سين', 60),
    (16, 'ع', 'عين', 70),
    (17, 'ف', 'فاء', 80),
    (18, 'ص', 'صاد', 90),
    (19, 'ق', 'قاف', 100),
    (20, 'ر', 'راء', 200),
    (21, 'ش', 'شين', 300),
    (22, 'ت', 'تاء', 400),
    (23, 'ث', 'ثاء', 500),
    (24, 'خ', 'خاء', 600),
    (25, 'ذ', 'ذال', 700),
    (26, 'ض', 'ضاد', 800),
    (27, 'ظ', 'ظاء', 900),
    (28, 'غ', 'غين', 1000),
]


def seed(conn: sqlite3.Connection):
    for lid, letter, name, jummal in LETTERS:
        conn.execute(
            "INSERT OR REPLACE INTO letters (letter_id, letter, letter_name, jummal_value, digit_root, abjad_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (lid, letter, name, jummal, digit_root(jummal), lid),
        )
    conn.commit()
    print(f"  letters: {len(LETTERS)} حرف")


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    seed(conn)
    conn.close()
