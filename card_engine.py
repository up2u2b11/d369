#!/usr/bin/env python3
"""
card_engine.py — نظام البطاقات المنهجية
══════════════════════════════════════════
الملكية الفكرية: عماد سليمان علوان

بطاقة واحدة لكل اكتشاف:
  السؤال | النتيجة | الرقم | الجذر | المصدر | التحقق | المرحلة

3 مراحل:
  constants  — ما يصح في كل القرآن
  patterns   — ما يتكرر في أكثر من 10 حالات
  exceptions — ما يخرج عن النمط (يكشف قانوناً أعمق)

قانون التوقف:
  كل جلسة = اكتشاف واحد — ثم أغلق الباب
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DB_PATH, KSA, digit_root
from calc_engine import calc_kabir

# ──────────────────────────────────────────────────────────
#  إنشاء الجداول
# ──────────────────────────────────────────────────────────

def init_cards_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS cards (
        card_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id  TEXT,                       -- رقم الجلسة YYYYMMDD-N
        phase       TEXT DEFAULT 'constants',   -- constants | patterns | exceptions
        question    TEXT NOT NULL,              -- السؤال الذي بدأت منه
        result      TEXT,                       -- النتيجة في جملة واحدة
        number      INTEGER,                    -- الرقم المحوري
        digit_root  INTEGER,                    -- جذره الرقمي
        evidence    TEXT,                       -- الأرقام المُثبِّتة (JSON)
        surah_ref   INTEGER,                    -- رقم السورة
        ayah_ref    INTEGER,                    -- رقم الآية
        source_text TEXT,                       -- نص المصدر
        verified    TEXT DEFAULT 'pending',     -- verified | rejected | pending
        note        TEXT,                       -- ملاحظة إضافية
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );

    CREATE TABLE IF NOT EXISTS sessions (
        session_id   TEXT PRIMARY KEY,          -- YYYYMMDD-N
        question     TEXT NOT NULL,             -- السؤال اليوم
        status       TEXT DEFAULT 'open',       -- open | closed
        card_id      INTEGER,                   -- البطاقة الناتجة
        opened_at    TEXT DEFAULT (datetime('now','localtime')),
        closed_at    TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_cards_phase    ON cards(phase);
    CREATE INDEX IF NOT EXISTS idx_cards_dr       ON cards(digit_root);
    CREATE INDEX IF NOT EXISTS idx_cards_verified ON cards(verified);
    CREATE INDEX IF NOT EXISTS idx_cards_number   ON cards(number);
    """)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────
#  الجلسة
# ──────────────────────────────────────────────────────────

def open_session(question: str) -> str:
    """افتح جلسة جديدة — بسؤال واحد."""
    conn = sqlite3.connect(str(DB_PATH))

    # رقم الجلسة: YYYYMMDD-N
    today = datetime.now(KSA).strftime("%Y%m%d")
    count = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE session_id LIKE ?", (f"{today}%",)
    ).fetchone()[0]
    sid = f"{today}-{count+1}"

    conn.execute(
        "INSERT INTO sessions(session_id, question) VALUES (?,?)",
        (sid, question)
    )
    conn.commit()
    conn.close()
    return sid


def close_session(session_id: str, card_id: int = None):
    """أغلق الجلسة بعد تثبيت بطاقتها."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "UPDATE sessions SET status='closed', card_id=?, closed_at=datetime('now','localtime') WHERE session_id=?",
        (card_id, session_id)
    )
    conn.commit()
    conn.close()


def get_open_session() -> dict | None:
    """هل يوجد جلسة مفتوحة؟"""
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT * FROM sessions WHERE status='open' ORDER BY opened_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(zip(['session_id','question','status','card_id','opened_at','closed_at'], row))


# ──────────────────────────────────────────────────────────
#  البطاقة
# ──────────────────────────────────────────────────────────

def add_card(
    question: str,
    result: str,
    number: int,
    evidence: dict | list,
    phase: str = "constants",
    session_id: str = None,
    surah_ref: int = None,
    ayah_ref: int = None,
    source_text: str = None,
    note: str = None,
) -> int:
    """أضف بطاقة اكتشاف — وأغلق الجلسة تلقائياً."""
    conn = sqlite3.connect(str(DB_PATH))
    dr = digit_root(number) if number else None

    cur = conn.execute("""
        INSERT INTO cards
            (session_id, phase, question, result, number, digit_root,
             evidence, surah_ref, ayah_ref, source_text, note)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        session_id, phase, question, result, number, dr,
        json.dumps(evidence, ensure_ascii=False) if evidence else None,
        surah_ref, ayah_ref, source_text, note
    ))
    card_id = cur.lastrowid
    conn.commit()
    conn.close()

    # أغلق الجلسة
    if session_id:
        close_session(session_id, card_id)

    return card_id


def verify_card(card_id: int, status: str = "verified"):
    """تحقق من بطاقة: verified / rejected."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("UPDATE cards SET verified=? WHERE card_id=?", (status, card_id))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────
#  القراءة
# ──────────────────────────────────────────────────────────

def list_cards(phase: str = None, verified: str = None, limit: int = 20) -> list:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    q = "SELECT * FROM cards WHERE 1=1"
    params = []
    if phase:
        q += " AND phase=?"; params.append(phase)
    if verified:
        q += " AND verified=?"; params.append(verified)
    q += " ORDER BY card_id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_card(card_id: int) -> dict | None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM cards WHERE card_id=?", (card_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def stats() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    total   = conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    by_phase = {r[0]: r[1] for r in conn.execute(
        "SELECT phase, COUNT(*) FROM cards GROUP BY phase").fetchall()}
    by_dr   = {r[0]: r[1] for r in conn.execute(
        "SELECT digit_root, COUNT(*) FROM cards WHERE digit_root IS NOT NULL GROUP BY digit_root ORDER BY digit_root").fetchall()}
    verified = conn.execute("SELECT COUNT(*) FROM cards WHERE verified='verified'").fetchone()[0]
    sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    conn.close()
    return {
        "total_cards": total,
        "verified": verified,
        "sessions": sessions,
        "by_phase": by_phase,
        "by_digit_root": by_dr,
        "to_100": max(0, 100 - total),
        "to_1000": max(0, 1000 - total),
    }


# ──────────────────────────────────────────────────────────
#  الاستنباط السريع — جواب من الأرقام
# ──────────────────────────────────────────────────────────

def quick_probe(query_text: str) -> dict:
    """
    أجب على سؤال نصي بالأرقام فقط.
    يحسب جُمَّل القطعة النصية + يبحث في الآيات المشابهة.
    """
    from quran_engine.search import search_by_number, search_by_digit_root

    val = calc_kabir(query_text)
    dr_val = digit_root(val)

    # بحث عن آيات جُمَّلها نفس القيمة
    exact = search_by_number(val, limit=5)

    # بحث عن آيات جذرها نفس الجذر
    same_dr = search_by_digit_root(dr_val, limit=5)

    return {
        "text": query_text,
        "jummal": val,
        "digit_root": dr_val,
        "exact_matches": len(exact),
        "same_root_ayahs": len(same_dr),
        "sample_exact": exact[:3] if exact else [],
        "sample_same_dr": same_dr[:3] if same_dr else [],
    }


# ──────────────────────────────────────────────────────────
#  تنسيق البطاقة للعرض
# ──────────────────────────────────────────────────────────

def format_card(card: dict) -> str:
    phase_ar = {"constants": "ثوابت", "patterns": "أنماط", "exceptions": "استثناءات"}.get(
        card.get("phase", ""), card.get("phase", ""))
    v_icon = {"verified": "✅", "rejected": "❌", "pending": "⏳"}.get(card.get("verified", ""), "⏳")

    lines = [
        f"╔══ بطاقة #{card['card_id']} ═══════════════════════╗",
        f"  المرحلة : {phase_ar}",
        f"  السؤال  : {card.get('question','—')}",
        f"  النتيجة : {card.get('result','—')}",
        f"  الرقم   : {card.get('number','—')}  |  الجذر: {card.get('digit_root','—')}",
    ]
    if card.get('surah_ref'):
        ref = f"سورة {card['surah_ref']}"
        if card.get('ayah_ref'):
            ref += f" آية {card['ayah_ref']}"
        lines.append(f"  المصدر  : {ref}")
    if card.get('source_text'):
        lines.append(f"  النص    : {card['source_text']}")
    if card.get('note'):
        lines.append(f"  ملاحظة  : {card['note']}")
    lines.append(f"  التحقق  : {v_icon}  |  {card.get('created_at','')[:10]}")
    lines.append(f"╚{'═'*42}╝")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────
#  تشغيل مباشر — اختبار
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_cards_db()
    print("تهيئة جداول البطاقات ✅")
    print(stats())
