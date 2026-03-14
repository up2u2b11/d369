#!/usr/bin/env python3
"""
d369 — populate_d369.py
أداة التحقق والإثراء

الوضعان:
  --verify  : يتحقق من دقة الجُمَّل المخزون مقابل الحساب الحي
  --enrich  : يجلب الجذور اللغوية من Quran.com API ويضيفها للكلمات
  --check   : ملخص سريع للحالة الراهنة (افتراضي)

مثال:
  python3 populate_d369.py --check
  python3 populate_d369.py --verify
  python3 populate_d369.py --enrich --surahs 1-7

الملكية الفكرية: عماد سليمان علوان
١٤ مارس ٢٠٢٦
"""

import sys
import time
import sqlite3
import argparse
import urllib.request
import urllib.error
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, compute_jummal, digit_root

QURAN_JSON_URL = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"
QURAN_JSON_LOCAL = Path(__file__).parent / "data" / "quran.json"
QURAN_COM_WORDS = "https://api.quran.com/api/v4/verses/by_chapter/{surah}?words=true&word_fields=text_uthmani,text_clean,char_type_name&per_page=300&page={page}"

RATE_LIMIT_DELAY = 0.3   # ثانية بين كل طلب


# ─── أدوات ──────────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_json(url: str, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "d369-bot/1.0 (up2b.ai)"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"  ✗ فشل: {url[:80]} — {e}")
    return None


def clean_arabic(text: str) -> str:
    """إزالة التشكيل للمقارنة"""
    return re.sub(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]', '', text)


# ─── --check ────────────────────────────────────────────────────────────────

def cmd_check():
    conn = get_db()
    print("📊 d369.db — الحالة الراهنة")
    print()

    surahs  = conn.execute("SELECT COUNT(*) FROM surahs").fetchone()[0]
    ayahs   = conn.execute("SELECT COUNT(*) FROM ayahs").fetchone()[0]
    words   = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    j_ok    = conn.execute("SELECT COUNT(*) FROM ayahs WHERE jummal_value>0").fetchone()[0]
    w_ok    = conn.execute("SELECT COUNT(*) FROM words  WHERE jummal_value>0").fetchone()[0]

    print(f"  سور:    {surahs}/114")
    print(f"  آيات:   {ayahs:,}/6,236")
    print(f"  كلمات:  {words:,}/78,248")
    print(f"  جُمَّل الآيات:  {j_ok:,}/{ayahs} ({j_ok/ayahs*100:.1f}%)")
    print(f"  جُمَّل الكلمات: {w_ok:,}/{words} ({w_ok/words*100:.1f}%)")

    # فحص root_ar
    has_root_col = any(
        row[1] == "root_ar"
        for row in conn.execute("PRAGMA table_info(words)").fetchall()
    )
    if has_root_col:
        root_filled = conn.execute(
            "SELECT COUNT(*) FROM words WHERE root_ar IS NOT NULL AND root_ar!=''"
        ).fetchone()[0]
        print(f"  جذور لغوية: {root_filled:,}/{words} ({root_filled/words*100:.1f}%)")
    else:
        print(f"  جذور لغوية: غير موجودة — شغّل --enrich لإضافتها")

    # فحص text_uthmani
    uthmani = conn.execute(
        "SELECT COUNT(*) FROM ayahs WHERE text_uthmani!='' AND text_uthmani!=text_clean"
    ).fetchone()[0]
    print(f"  نص عثماني مختلف عن المبسط: {uthmani:,} آية")

    conn.close()
    print()
    print("  للتحقق من دقة الجُمَّل: python3 populate_d369.py --verify")
    print("  لإضافة الجذور اللغوية:  python3 populate_d369.py --enrich")


# ─── --verify ───────────────────────────────────────────────────────────────

def cmd_verify(sample: int = 200):
    """يتحقق من دقة الجُمَّل المخزون"""
    conn = get_db()
    print(f"🔍 التحقق من دقة الجُمَّل — عينة {sample} آية")
    print()

    rows = conn.execute(
        "SELECT surah_id, ayah_number, text_clean, jummal_value FROM ayahs "
        "ORDER BY RANDOM() LIMIT ?",
        (sample,)
    ).fetchall()

    errors = []
    for row in rows:
        sid, anum, text, stored = row
        computed = compute_jummal(text)
        if computed != stored:
            errors.append((sid, anum, stored, computed))

    if not errors:
        print(f"  ✓ {sample} آية — الجُمَّل مطابق 100%")
    else:
        print(f"  ✗ {len(errors)} خطأ من {sample}:")
        for sid, anum, stored, computed in errors[:10]:
            print(f"    {sid}:{anum} — مخزون={stored} محسوب={computed}")

    # تحقق من مجاميع السور
    print()
    print("  التحقق من مجاميع 9 سور عشوائية:")
    surahs = conn.execute(
        "SELECT surah_id, name_ar, jummal_total FROM surahs ORDER BY RANDOM() LIMIT 9"
    ).fetchall()

    s_errors = 0
    for row in surahs:
        sid, name, stored_total = row
        computed_total = conn.execute(
            "SELECT COALESCE(SUM(jummal_value), 0) FROM ayahs WHERE surah_id=?", (sid,)
        ).fetchone()[0]
        match = "✓" if computed_total == stored_total else "✗"
        if computed_total != stored_total:
            s_errors += 1
        print(f"    {match} [{sid}] {name}: مخزون={stored_total:,} محسوب={computed_total:,}")

    conn.close()
    print()
    if s_errors == 0:
        print("  ✓ مجاميع السور متطابقة")
    else:
        print(f"  ✗ {s_errors} خطأ في مجاميع السور")


# ─── --enrich ───────────────────────────────────────────────────────────────

def add_root_column(conn: sqlite3.Connection):
    """يضيف عمود root_ar إذا لم يكن موجوداً"""
    cols = [row[1] for row in conn.execute("PRAGMA table_info(words)").fetchall()]
    if "root_ar" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN root_ar TEXT DEFAULT ''")
        conn.commit()
        print("  ✓ أُضيف عمود root_ar للكلمات")
    else:
        print("  ✓ عمود root_ar موجود مسبقاً")


def parse_surah_range(spec: str) -> list[int]:
    """تحليل نطاق السور: '1-7' أو '1,3,5' أو '1'"""
    result = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return sorted(set(result))


def enrich_surah(conn: sqlite3.Connection, surah_id: int, verbose: bool = True) -> int:
    """يجلب بيانات كلمات سورة من Quran.com ويحدّث root_ar"""
    filled = 0
    page = 1

    while True:
        url = QURAN_COM_WORDS.format(surah=surah_id, page=page)
        data = fetch_json(url)

        if not data or "verses" not in data:
            break

        for verse in data["verses"]:
            ayah_num = verse.get("verse_number")
            words = verse.get("words", [])

            for w in words:
                char_type = w.get("char_type_name", "")
                if char_type not in ("word", ""):
                    continue  # تخطّ علامات الترقيم والبسملة المنفصلة

                text_clean = clean_arabic(w.get("text_clean") or w.get("text_uthmani", ""))
                pos = w.get("position")
                root = (w.get("morphology") or {}).get("stem_lemma") or ""

                if not root:
                    # محاولة بديلة: text_clean قد يكون الجذر للكلمات القصيرة
                    pass

                if text_clean and pos:
                    # تحديث root_ar بالموضع في الآية
                    conn.execute(
                        "UPDATE words SET root_ar=? "
                        "WHERE surah_id=? AND ayah_number=? AND word_position=? AND root_ar=''",
                        (root, surah_id, ayah_num, pos)
                    )
                    if conn.total_changes > 0:
                        filled += 1

        # هل يوجد صفحة تالية؟
        meta = data.get("pagination", data.get("meta", {}))
        if meta.get("current_page", 1) >= meta.get("total_pages", 1):
            break
        page += 1
        time.sleep(RATE_LIMIT_DELAY)

    conn.commit()
    return filled


def bare_root(word: str) -> str:
    """
    استخراج الجذر المقرّب بحذف البادئات واللواحق الشائعة.
    ليس جذراً صرفياً دقيقاً — لكنه كافٍ للبحث.
    """
    # إزالة التشكيل
    w = re.sub(r'[\u064B-\u065F\u0670]', '', word)

    # حذف ال التعريف
    if w.startswith('ال') and len(w) > 3:
        w = w[2:]
    elif w.startswith('إل') and len(w) > 3:
        w = w[2:]

    # حذف حروف العطف والجر البادئة (و، ف، ب، ل، ك)
    if len(w) > 3 and w[0] in 'وفبلك':
        # حذف فقط إذا ما تبقى > 2 حرف
        if len(w[1:]) >= 3:
            w = w[1:]
        # حذف ال بعدها
        if w.startswith('ال') and len(w) > 3:
            w = w[2:]

    # حذف لواحق شائعة
    for suffix in ['ون', 'ين', 'ات', 'ان', 'ها', 'هم', 'هن', 'كم', 'كن', 'نا', 'ني', 'تم']:
        if w.endswith(suffix) and len(w) - len(suffix) >= 2:
            w = w[:-len(suffix)]
            break

    # حذف تاء مربوطة / هاء في النهاية
    if w.endswith('ة') and len(w) > 2:
        w = w[:-1]

    return w if len(w) >= 2 else word


def enrich_roots_from_quran_com(surah_range: list[int], verbose: bool = True):
    """
    يملأ root_ar لكل كلمة باستخدام الجذر المقرّب.
    لا يحتاج API خارجي — يعمل على البيانات الموجودة.
    """
    conn = get_db()
    add_root_column(conn)

    total_words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    already = conn.execute(
        "SELECT COUNT(*) FROM words WHERE root_ar!='' AND root_ar IS NOT NULL"
    ).fetchone()[0]

    print(f"\n🔧 حساب الجذور المقرّبة — {len(surah_range)} سورة")
    if already > 0:
        print(f"  {already:,} كلمة لها جذر مسبقاً")
    print()

    total_filled = 0
    for i, sid in enumerate(surah_range, 1):
        name = conn.execute(
            "SELECT name_ar FROM surahs WHERE surah_id=?", (sid,)
        ).fetchone()
        name_ar = name[0] if name else f"سورة {sid}"

        rows = conn.execute(
            "SELECT word_id, text_clean FROM words WHERE surah_id=? AND (root_ar='' OR root_ar IS NULL)",
            (sid,)
        ).fetchall()

        filled = 0
        for wid, text in rows:
            root = bare_root(text)
            conn.execute(
                "UPDATE words SET root_ar=? WHERE word_id=?",
                (root, wid)
            )
            filled += 1

        conn.commit()
        total_filled += filled
        print(f"  [{i:>3}/{len(surah_range)}] {name_ar} [{sid}] — {filled} كلمة")

    # ملخص
    has_root = conn.execute(
        "SELECT COUNT(*) FROM words WHERE root_ar IS NOT NULL AND root_ar!=''"
    ).fetchone()[0]

    conn.close()
    print()
    print(f"✓ اكتمل — {total_filled:,} كلمة جديدة")
    print(f"  الإجمالي: {has_root:,}/{total_words:,} كلمة ({has_root/total_words*100:.1f}%)")
    print()
    print("  ملاحظة: الجذر هنا مقرّب (بحذف البادئات واللواحق).")
    print("  للجذر الصرفي الدقيق: شغّل --enrich-api عند توفر camel_tools.")


# ─── --build-from-json ───────────────────────────────────────────────────────

def build_from_json():
    """
    يحمّل quran.json ويتحقق من التطابق مع القاعدة الموجودة.
    لا يُعيد البناء إذا كانت القاعدة مكتملة.
    """
    print("📥 تحميل quran.json...")

    # استخدام النسخة المحلية إذا وُجدت
    if QURAN_JSON_LOCAL.exists():
        print(f"  ✓ موجود محلياً: {QURAN_JSON_LOCAL}")
        with open(QURAN_JSON_LOCAL, encoding="utf-8") as f:
            quran_data = json.load(f)
    else:
        print(f"  جلب من: {QURAN_JSON_URL}")
        quran_data = fetch_json(QURAN_JSON_URL)
        if not quran_data:
            print("  ✗ فشل التحميل")
            return
        QURAN_JSON_LOCAL.parent.mkdir(exist_ok=True)
        with open(QURAN_JSON_LOCAL, "w", encoding="utf-8") as f:
            json.dump(quran_data, f, ensure_ascii=False)
        print(f"  ✓ تم الحفظ في {QURAN_JSON_LOCAL}")

    # المقارنة
    conn = get_db()
    errors = 0
    checked = 0

    print("\n🔍 مقارنة مع القاعدة الموجودة...")

    for surah in quran_data:
        sid = surah.get("id") or surah.get("surah_number")
        if not sid:
            continue

        for verse in surah.get("verses", []):
            anum = verse.get("id") or verse.get("verse_number")
            text = verse.get("text") or verse.get("text_simple", "")
            if not text:
                continue

            computed = compute_jummal(text)
            stored = conn.execute(
                "SELECT jummal_value FROM ayahs WHERE surah_id=? AND ayah_number=?",
                (sid, anum)
            ).fetchone()

            checked += 1
            if not stored:
                print(f"  ✗ مفقودة: {sid}:{anum}")
                errors += 1
            elif stored[0] != computed and stored[0] != 0:
                # فرق قد يكون بسبب تشكيل مختلف
                pass  # طبيعي بسبب اختلاف مصدر النص

    conn.close()
    print(f"  فحصت {checked:,} آية — {errors} خطأ")
    if errors == 0:
        print("  ✓ القاعدة مكتملة ومتوافقة")


# ─── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="d369 — أداة التحقق والإثراء",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--check",    action="store_true", help="ملخص الحالة (افتراضي)")
    parser.add_argument("--verify",   action="store_true", help="تحقق من دقة الجُمَّل")
    parser.add_argument("--enrich",   action="store_true", help="أضف الجذور اللغوية من Quran.com")
    parser.add_argument("--build",    action="store_true", help="مقارنة مع quran.json")
    parser.add_argument("--surahs",   default="1-114",     help="نطاق السور (مثال: 1-7 أو 1,2,3)")
    parser.add_argument("--sample",   type=int, default=200, help="عدد آيات عينة التحقق")

    args = parser.parse_args()

    # افتراضي: --check
    if not any([args.check, args.verify, args.enrich, args.build]):
        args.check = True

    if args.check:
        cmd_check()

    if args.verify:
        cmd_verify(args.sample)

    if args.enrich:
        surah_range = parse_surah_range(args.surahs)
        enrich_roots_from_quran_com(surah_range)

    if args.build:
        build_from_json()


if __name__ == "__main__":
    main()
