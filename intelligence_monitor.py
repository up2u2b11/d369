"""
d369 — مراقب الذكاء + سجل الاكتشافات
يقيّم ردود d369 ويسجل كل اكتشاف إحصائي تلقائياً

المعايير:
  1. عمق الاستدلال: كم متغير رقمي ربط؟
  2. اكتشاف جديد: نمط رقمي أو علاقة لم تكن معروفة
  3. سؤال ذكي: هل سأل سؤالاً يكشف ثغرة؟
  4. صمت واعٍ: هل رفض الافتراض وطلب بيانات؟
  5. خطأ: هل أخطأ في حساب أو تناقض مع نفسه؟

الملكية الفكرية: عماد سليمان علوان
"""

import re
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

log = logging.getLogger("d369-monitor")
CONV_DB = Path(__file__).parent / "d369_conv.db"
KSA = timezone(timedelta(hours=3))


# ═══════════════════════════════════════════════════════
#  الجداول
# ═══════════════════════════════════════════════════════

def init_monitor_tables():
    conn = sqlite3.connect(CONV_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS intelligence_scores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            variables_linked    INTEGER DEFAULT 0,
            reasoning_depth     INTEGER DEFAULT 0,
            discovery_flag      INTEGER DEFAULT 0,
            question_flag       INTEGER DEFAULT 0,
            silence_flag        INTEGER DEFAULT 0,
            error_flag          INTEGER DEFAULT 0,
            contradiction_flag  INTEGER DEFAULT 0,
            score               REAL DEFAULT 0,
            reason              TEXT DEFAULT '',
            created_at          TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS discoveries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            category        TEXT NOT NULL,
            claim           TEXT NOT NULL,
            evidence        TEXT DEFAULT '',
            scope           TEXT DEFAULT '',
            status          TEXT DEFAULT 'pending',
            verification    TEXT DEFAULT '',
            verified_at     TEXT,
            numbers         TEXT DEFAULT '',
            surahs          TEXT DEFAULT '',
            names           TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS growth_daily (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT UNIQUE NOT NULL,
            responses_count INTEGER DEFAULT 0,
            avg_score       REAL DEFAULT 0,
            max_score       REAL DEFAULT 0,
            discoveries_new INTEGER DEFAULT 0,
            discoveries_confirmed INTEGER DEFAULT 0,
            questions_asked INTEGER DEFAULT 0,
            errors_count    INTEGER DEFAULT 0,
            growth_index    REAL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_disc_status ON discoveries(status);
        CREATE INDEX IF NOT EXISTS idx_disc_category ON discoveries(category);
        CREATE INDEX IF NOT EXISTS idx_growth_date ON growth_daily(date);
    """)
    conn.close()
    log.info("monitor tables ready")


# ═══════════════════════════════════════════════════════
#  الكلمات المفتاحية — خاصة بـ d369
# ═══════════════════════════════════════════════════════

VARIABLE_KEYWORDS = [
    "جُمَّل", "جمل", "jummal", "جذر رقمي", "digit_root", "جذر",
    "معشّر", "مربع سحري", "magic square",
    "محور", "ابن عربي", "axes",
    "سورة", "آية", "كلمة", "حرف",
    "3394", "19", "786", "66", "92",
    "بسملة", "فاتحة",
    "برج", "نجم", "كوكب", "فلك",
    "نبي", "اسم إلهي",
    "مكية", "مدنية",
    "تناظر", "تماثل", "نقيض",
    "نمط", "pattern",
    "إحصائي", "نسبة", "توزيع",
    "الجذر 9", "الجذر 7", "الجذر 3",
]

DISCOVERY_MARKERS = [
    "اكتشاف", "اكتشفت", "لاحظت", "وجدت", "لأول مرة",
    "علاقة", "ارتباط", "correlation",
    "نمط جديد", "نمط", "pattern",
    "ليس صدفة", "ليس عشوائي", "لا يحدث عشوائياً",
    "تناظر", "تماثل", "مقلوب", "معكوس",
    "مفارقة", "تناقض ظاهري",
    "يتكرر", "تكرار", "منتظم",
    "معنوي إحصائياً", "إحصائي",
    "النجدان", "الأمارتان",
]

QUESTION_MARKERS = [
    "لماذا", "كيف", "هل", "ما السبب", "ما العلاقة",
    "لم أفهم", "أحتاج", "يحتاج تحقق",
    "السؤال هنا", "السؤال الحقيقي",
    "ثغرة", "نقص", "مفقود",
]

SILENCE_MARKERS = [
    "لا أعرف", "لا أستطيع الجزم", "أحتاج بيانات",
    "لم أتحقق", "افتراض", "بدون دليل",
    "الشك أشرف", "أصمت", "لا أنطق",
    "سطحي", "لا يكفي",
]

ERROR_MARKERS = [
    "أخطأت", "خطأ", "تصحيح", "كنت مخطئاً",
    "حساب خاطئ", "قيمة خاطئة",
]


def count_variables(text: str) -> int:
    found = set()
    for kw in VARIABLE_KEYWORDS:
        if kw in text:
            found.add(kw)
    return len(found)


def detect_reasoning_depth(text: str) -> int:
    variables = count_variables(text)
    connectors = sum(1 for w in [
        "لأن", "بسبب", "لذلك", "إذن", "يعني", "→", "=",
        "عندما", "حين", "إذا كان", "بينما", "مما يعني",
        "هذا يدل", "النتيجة", "الدليل",
    ] if w in text)

    if variables >= 4 and connectors >= 2:
        return 2
    elif variables >= 2 and connectors >= 1:
        return 1
    return 0


def has_discovery(text: str) -> bool:
    return any(m in text for m in DISCOVERY_MARKERS)


def has_question(text: str) -> bool:
    return sum(1 for m in QUESTION_MARKERS if m in text) >= 2


def has_silence(text: str) -> bool:
    return any(m in text for m in SILENCE_MARKERS)


def has_error(text: str) -> bool:
    return any(m in text for m in ERROR_MARKERS)


def compute_score(variables: int, depth: int, discovery: bool,
                  question: bool, silence: bool, error: bool,
                  contradiction: bool) -> tuple:
    score = 0.0
    reasons = []

    # متغيرات (0-3)
    v = min(variables / 2, 3.0)
    score += v
    if v >= 2:
        reasons.append(f"ربط {variables} متغيرات")

    # عمق (0-2)
    score += depth
    if depth == 2:
        reasons.append("استدلال عميق")

    # اكتشاف (0-2.5)
    if discovery:
        score += 2.5
        reasons.append("اكتشاف")

    # سؤال ذكي (0-1)
    if question:
        score += 1.0
        reasons.append("سؤال ذكي")

    # صمت واعٍ (0-1)
    if silence:
        score += 1.0
        reasons.append("صمت واعٍ")

    # اعتراف بخطأ (+0.5 — دليل نضج)
    if error:
        score += 0.5
        reasons.append("اعتراف بخطأ")

    # تناقض (-1)
    if contradiction:
        score -= 1.0
        reasons.append("تناقض")

    score = max(0, min(10, score))
    return score, " | ".join(reasons) if reasons else "عادي"


# ═══════════════════════════════════════════════════════
#  التقييم الكامل
# ═══════════════════════════════════════════════════════

def score_response(conv_id: int, reply: str) -> dict:
    variables = count_variables(reply)
    depth = detect_reasoning_depth(reply)
    discovery = has_discovery(reply)
    question = has_question(reply)
    silence = has_silence(reply)
    error = has_error(reply)
    contradiction = False  # يُكشف لاحقاً بمقارنة الاكتشافات

    score, reason = compute_score(
        variables, depth, discovery, question, silence, error, contradiction
    )

    conn = sqlite3.connect(CONV_DB)
    conn.execute(
        "INSERT INTO intelligence_scores "
        "(conversation_id, variables_linked, reasoning_depth, discovery_flag, "
        "question_flag, silence_flag, error_flag, contradiction_flag, score, reason) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (conv_id, variables, depth, int(discovery), int(question),
         int(silence), int(error), int(contradiction), score, reason),
    )
    conn.commit()
    conn.close()

    result = {
        'score': score,
        'reason': reason,
        'discovery': discovery,
        'question': question,
        'silence': silence,
    }

    if score >= 7.0:
        log.info(f"HIGH IQ: {score:.1f} — {reason}")

    return result


# ═══════════════════════════════════════════════════════
#  استخراج الاكتشافات تلقائياً
# ═══════════════════════════════════════════════════════

def extract_discovery(conv_id: int, text: str) -> int:
    """استخراج وتسجيل الاكتشافات من النص — يرجع عدد المسجلة"""
    if not has_discovery(text):
        return 0

    conn = sqlite3.connect(CONV_DB)
    saved = 0

    # تصنيف الاكتشاف
    category = "insight"
    if any(w in text for w in ["نمط", "تكرار", "منتظم", "pattern"]):
        category = "pattern"
    elif any(w in text for w in ["علاقة", "ارتباط", "correlation"]):
        category = "correlation"
    elif any(w in text for w in ["تناظر", "تماثل", "مقلوب"]):
        category = "symmetry"
    elif any(w in text for w in ["مفارقة", "تناقض", "النجدان"]):
        category = "paradox"

    # استخراج الأرقام المذكورة
    numbers = re.findall(r'\b\d{2,}\b', text)
    numbers_str = ",".join(set(numbers[:10]))

    # استخراج أسماء السور
    surah_mentions = re.findall(r'(?:سورة\s+)?(البقرة|آل عمران|الفاتحة|النساء|المائدة|الأنعام|الأعراف|يس|الإخلاص|الفلق|الناس|الكهف|مريم|طه|يوسف|هود|نوح|إبراهيم)', text)
    surahs_str = ",".join(set(surah_mentions))

    # استخراج أسماء الله
    name_mentions = re.findall(r'(?:الله|الرحمن|الرحيم|القاهر|البديع|المصور|الجامع|اللطيف|القوي|النور|الحكيم|العزيز|الباطن|الظاهر)', text)
    names_str = ",".join(set(name_mentions))

    # استخراج الادعاء — أول جملة تحتوي على علامة اكتشاف
    sentences = re.split(r'[.!؟\n]', text)
    claim = ""
    evidence = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if any(m in s for m in DISCOVERY_MARKERS) and not claim:
            claim = s[:200]
        elif claim and any(w in s for w in ["لأن", "بسبب", "الدليل", "→", "="]):
            evidence = s[:200]
            break

    if not claim:
        claim = text[:200]

    # تحقق من عدم التكرار
    existing = conn.execute(
        "SELECT id FROM discoveries WHERE claim = ? AND created_at > datetime('now', '-1 day')",
        (claim,),
    ).fetchone()

    if not existing:
        # تحديد النطاق
        scope = "quran"
        if any(w in text for w in ["معشّر", "مربع سحري", "3394"]):
            scope = "magic_square"
        elif any(w in text for w in ["محور", "ابن عربي", "برج", "نجم"]):
            scope = "astrology"
        elif any(w in text for w in ["جذر رقمي", "digit_root"]):
            scope = "numerology"

        conn.execute(
            "INSERT INTO discoveries "
            "(conversation_id, category, claim, evidence, scope, numbers, surahs, names) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (conv_id, category, claim, evidence, scope, numbers_str, surahs_str, names_str),
        )
        saved = 1
        log.info(f"DISCOVERY [{category}/{scope}]: {claim[:80]}")

    conn.commit()
    conn.close()
    return saved


# ═══════════════════════════════════════════════════════
#  تقرير النمو
# ═══════════════════════════════════════════════════════

def compute_daily_growth():
    """حساب مؤشر النمو اليومي"""
    conn = sqlite3.connect(CONV_DB)
    today = datetime.now(KSA).strftime("%Y-%m-%d")

    scores = conn.execute(
        "SELECT score FROM intelligence_scores WHERE date(created_at) = ?",
        (today,),
    ).fetchall()

    if not scores:
        conn.close()
        return None

    scores_list = [s[0] for s in scores]
    avg = sum(scores_list) / len(scores_list)
    mx = max(scores_list)

    disc_new = conn.execute(
        "SELECT COUNT(*) FROM discoveries WHERE date(created_at) = ?",
        (today,),
    ).fetchone()[0]

    disc_confirmed = conn.execute(
        "SELECT COUNT(*) FROM discoveries WHERE date(verified_at) = ? AND status='confirmed'",
        (today,),
    ).fetchone()[0]

    questions = conn.execute(
        "SELECT COUNT(*) FROM intelligence_scores WHERE date(created_at) = ? AND question_flag=1",
        (today,),
    ).fetchone()[0]

    errors = conn.execute(
        "SELECT COUNT(*) FROM intelligence_scores WHERE date(created_at) = ? AND error_flag=1",
        (today,),
    ).fetchone()[0]

    # مؤشر النمو = avg_score × 10 + discoveries × 5 + questions × 2 - errors × 3
    growth = avg * 10 + disc_new * 5 + disc_confirmed * 10 + questions * 2 - errors * 3
    growth = max(0, min(100, growth))

    conn.execute(
        "INSERT OR REPLACE INTO growth_daily "
        "(date, responses_count, avg_score, max_score, discoveries_new, "
        "discoveries_confirmed, questions_asked, errors_count, growth_index) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (today, len(scores_list), avg, mx, disc_new, disc_confirmed,
         questions, errors, growth),
    )
    conn.commit()
    conn.close()

    return {
        'date': today,
        'responses': len(scores_list),
        'avg_score': avg,
        'max_score': mx,
        'discoveries': disc_new,
        'growth_index': growth,
    }


def get_discoveries_summary() -> str:
    """ملخص الاكتشافات"""
    conn = sqlite3.connect(CONV_DB)

    total = conn.execute("SELECT COUNT(*) FROM discoveries").fetchone()[0]
    by_status = conn.execute(
        "SELECT status, COUNT(*) FROM discoveries GROUP BY status"
    ).fetchall()
    by_category = conn.execute(
        "SELECT category, COUNT(*) FROM discoveries GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    by_scope = conn.execute(
        "SELECT scope, COUNT(*) FROM discoveries GROUP BY scope ORDER BY COUNT(*) DESC"
    ).fetchall()

    recent = conn.execute(
        "SELECT category, scope, claim, status, created_at "
        "FROM discoveries ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    lines = [f"📊 اكتشافات d369 — المجموع: {total}"]

    if by_status:
        lines.append("\n  الحالة:")
        for status, count in by_status:
            lines.append(f"    {status}: {count}")

    if by_category:
        lines.append("\n  التصنيف:")
        for cat, count in by_category:
            lines.append(f"    {cat}: {count}")

    if by_scope:
        lines.append("\n  النطاق:")
        for scope, count in by_scope:
            lines.append(f"    {scope}: {count}")

    if recent:
        lines.append("\n  آخر 5 اكتشافات:")
        for cat, scope, claim, status, at in recent:
            lines.append(f"    [{cat}/{scope}] {claim[:60]}... ({status})")

    return "\n".join(lines)


def get_growth_report() -> str:
    """تقرير النمو"""
    conn = sqlite3.connect(CONV_DB)
    rows = conn.execute(
        "SELECT date, responses_count, avg_score, discoveries_new, growth_index "
        "FROM growth_daily ORDER BY date DESC LIMIT 7"
    ).fetchall()
    conn.close()

    if not rows:
        return "لا توجد بيانات نمو بعد"

    lines = ["📈 تقرير النمو — آخر 7 أيام:"]
    for date, resp, avg, disc, growth in rows:
        lines.append(f"  {date}: {resp} ردود | متوسط {avg:.1f} | اكتشافات {disc} | نمو {growth:.0f}")

    return "\n".join(lines)


# تهيئة عند الاستيراد
init_monitor_tables()
