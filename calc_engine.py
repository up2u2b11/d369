"""
calc_engine.py — محرك الحساب متعدد الأنظمة
8 أنظمة: kabir + saghir + ordinal + lettercount + special6 + cust_1..3

الملكية الفكرية: عماد سليمان علوان
"""

import re
import json
import sqlite3
from pathlib import Path
from config import DB_PATH, JUMMAL_MAP, SPECIAL_6_MAP, digit_root

# ─── خريطة التنظيف (إزالة التشكيل) ───
_CLEAN = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

# ─── خرائط الأنظمة الثابتة ───

# saghir = جذر رقمي لكل حرف من قيمة الكبير
SAGHIR_MAP = {ch: digit_root(v) for ch, v in JUMMAL_MAP.items()}

# ordinal = abjad_order من جدول letters
_ORDINAL_MAP = {}
def _load_ordinal():
    global _ORDINAL_MAP
    if _ORDINAL_MAP:
        return
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute('SELECT letter, abjad_order FROM letters').fetchall()
    conn.close()
    # نُغطي الأحرف المتشابهة (همزات + تاء مربوطة + ألف مقصورة)
    base = {ch: v for ch, v in rows}
    _ORDINAL_MAP = base.copy()
    # همزات الألف
    for ch in ('أ', 'إ', 'آ', 'ٱ', 'ء'):
        _ORDINAL_MAP.setdefault(ch, base.get('ا', 1))
    _ORDINAL_MAP.setdefault('ة', base.get('ه', 5))
    _ORDINAL_MAP.setdefault('ؤ', base.get('و', 6))
    _ORDINAL_MAP.setdefault('ئ', base.get('ي', 10))
    _ORDINAL_MAP.setdefault('ى', base.get('ي', 10))


def _clean(text: str) -> str:
    return _CLEAN.sub('', text)


# ─── حساب نص بنظام معيّن ───

def calc_kabir(text: str) -> int:
    t = _clean(text)
    return sum(JUMMAL_MAP.get(ch, 0) for ch in t)

def calc_saghir(text: str) -> int:
    t = _clean(text)
    return sum(SAGHIR_MAP.get(ch, 0) for ch in t)

def calc_ordinal(text: str) -> int:
    _load_ordinal()
    t = _clean(text)
    return sum(_ORDINAL_MAP.get(ch, 0) for ch in t)

def calc_lettercount(text: str) -> int:
    t = _clean(text)
    return sum(1 for ch in t if ch in JUMMAL_MAP)

def calc_special6(text: str) -> int:
    t = _clean(text)
    return sum(SPECIAL_6_MAP.get(ch, 0) for ch in t)

def calc_custom(text: str, mapping: dict) -> int:
    """حساب بنظام مخصص — mapping = {'ا': X, 'ب': Y, ...}"""
    t = _clean(text)
    return sum(mapping.get(ch, 0) for ch in t)


# ─── محرك موحد ───

BUILTIN_SYSTEMS = {
    'kabir':       calc_kabir,
    'saghir':      calc_saghir,
    'ordinal':     calc_ordinal,
    'lettercount': calc_lettercount,
    'special6':    calc_special6,
}

def calc_all(text: str) -> dict:
    """يحسب النص بكل الأنظمة المدمجة ويُعيد قاموساً"""
    results = {}
    for name, fn in BUILTIN_SYSTEMS.items():
        v = fn(text)
        results[name] = {'value': v, 'digit_root': digit_root(v)}
    return results

def calc_by_system(text: str, system_id: int) -> dict:
    """يحسب بنظام محدد (من قاعدة البيانات)"""
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        'SELECT name, mapping_json, apply_digit_reduction FROM calc_systems WHERE system_id=?',
        (system_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {'error': 'system not found'}
    name, mapping_json, apply_dr = row
    if name in BUILTIN_SYSTEMS:
        v = BUILTIN_SYSTEMS[name](text)
    elif mapping_json:
        mapping = json.loads(mapping_json)
        v = calc_custom(text, mapping)
    else:
        return {'error': 'no mapping defined', 'system': name}
    if apply_dr:
        v = digit_root(v)
    return {'system': name, 'value': v, 'digit_root': digit_root(v)}


# ─── حساب من قاعدة البيانات (نص الكلمة/الآية) ───

def calc_word_all_systems(word_text: str) -> dict:
    """يحسب كلمة بكل الأنظمة"""
    return calc_all(word_text)

def calc_ayah_from_db(surah: int, aya: int) -> dict:
    """يحسب آية بكل الأنظمة من النص الموجود في ref_ayat"""
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        'SELECT text_clean FROM ref_ayat WHERE surah=? AND aya=?',
        (surah, aya)
    ).fetchone()
    conn.close()
    if not row:
        return {'error': 'ayah not found'}
    text = row[0] or ''
    results = calc_all(text)
    results['text'] = text
    results['surah'] = surah
    results['aya'] = aya
    return results


# ─── جلب قيم ayah_calcs لآية محددة ───

def get_ayah_calcs(surah: int, aya: int) -> list:
    """يجلب كل القيم المحسوبة مسبقاً لآية من ayah_calcs"""
    conn = sqlite3.connect(str(DB_PATH))
    # نتحقق من وجود الجدول أولاً
    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ayah_calcs'"
    ).fetchone()
    if not tbl:
        conn.close()
        return []
    rows = conn.execute(
        '''SELECT cs.name, cs.name_ar, ac.value, ac.digit_root
           FROM ayah_calcs ac
           JOIN calc_systems cs ON ac.system_id = cs.system_id
           WHERE ac.surah=? AND ac.aya=?
           ORDER BY ac.system_id''',
        (surah, aya)
    ).fetchall()
    conn.close()
    return [{'system': r[0], 'name_ar': r[1], 'value': r[2], 'dr': r[3]} for r in rows]


def get_word_calcs(word_text: str) -> list:
    """يجلب كل القيم المحسوبة مسبقاً لكلمة من word_calcs"""
    conn = sqlite3.connect(str(DB_PATH))
    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='word_calcs'"
    ).fetchone()
    if not tbl:
        conn.close()
        return []
    rows = conn.execute(
        '''SELECT cs.name, cs.name_ar, wc.value, wc.digit_root
           FROM word_calcs wc
           JOIN calc_systems cs ON wc.system_id = cs.system_id
           WHERE wc.word_text=?
           ORDER BY wc.system_id''',
        (word_text,)
    ).fetchall()
    conn.close()
    return [{'system': r[0], 'name_ar': r[1], 'value': r[2], 'dr': r[3]} for r in rows]


# ─── قائمة الأنظمة المتاحة ───

def list_systems() -> list:
    """يُعيد كل الأنظمة من قاعدة البيانات"""
    conn = sqlite3.connect(str(DB_PATH))
    tbl = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='calc_systems'"
    ).fetchone()
    if not tbl:
        conn.close()
        return []
    rows = conn.execute(
        'SELECT system_id, name, name_ar, description, is_active FROM calc_systems ORDER BY system_id'
    ).fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'name_ar': r[2], 'desc': r[3], 'active': bool(r[4])} for r in rows]
