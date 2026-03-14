#!/usr/bin/env python3
"""
d369 — بوت تيليجرام
يقرأ الكتاب والكون — لا ينطق بما لا يعرف

3 + 6 + 9 = 18 → 9

الملكية الفكرية: عماد سليمان علوان
"""

import os
import re
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters,
)

# ─── الإعدادات ───
load_dotenv(Path(__file__).parent / ".env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_KEY = os.getenv("ANTHROPIC_API_KEY")

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, compute_jummal, digit_root, KSA, JUMMAL_MAP
import eyes
import intelligence_monitor as monitor
from quran_engine.search import (
    compute_all, search_by_number, get_divisors,
    get_ayah_detail, search_by_digit_root, find_matches, discover_patterns,
)
from d369_engine import (
    engine_divisors, format_divisors,
    engine_explore, format_explore,
    engine_match, format_match,
    engine_correlation, format_correlation,
    engine_sequence, format_sequence,
    engine_overview, engine_compare, engine_ref,
    parse_group_spec,
)

# ─── الروح ───
SOUL_PATH = Path(__file__).parent / "d369_soul.md"
SOUL = SOUL_PATH.read_text(encoding="utf-8")

# ─── قاعدة البيانات — المحادثات ───
CONV_DB = Path(__file__).parent / "d369_conv.db"

def init_conv_db():
    conn = sqlite3.connect(CONV_DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            conv_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            model_used TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS token_usage (
            usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            tokens_in INTEGER NOT NULL,
            tokens_out INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, created_at);
    """)
    conn.close()

init_conv_db()

# ─── Claude ───
client = Anthropic(api_key=API_KEY)
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# ─── اللوجينج ───
logging.basicConfig(
    format="%(asctime)s [d369] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("d369")


# ═══════════════════════════════════════════════════════
#  الذاكرة
# ═══════════════════════════════════════════════════════

def save_message(user_id: int, role: str, content: str,
                 model: str = None, tin: int = 0, tout: int = 0):
    conn = sqlite3.connect(CONV_DB)
    conn.execute(
        "INSERT INTO conversations (user_id, role, content, model_used, tokens_in, tokens_out) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, role, content, model, tin, tout),
    )
    conn.commit()
    conn.close()


def get_history(user_id: int, limit: int = 20) -> list:
    conn = sqlite3.connect(CONV_DB)
    rows = conn.execute(
        "SELECT role, content FROM conversations "
        "WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    rows.reverse()
    return [{"role": r, "content": c} for r, c in rows]


def record_tokens(model: str, tin: int, tout: int):
    conn = sqlite3.connect(CONV_DB)
    conn.execute(
        "INSERT INTO token_usage (model, tokens_in, tokens_out) VALUES (?, ?, ?)",
        (model, tin, tout),
    )
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════
#  التفكير
# ═══════════════════════════════════════════════════════

def choose_model(message: str) -> str:
    """هايكو للأسئلة القصيرة، سونيت للعميقة"""
    words = len(message.split())
    return MODEL_SONNET if words >= 50 else MODEL_HAIKU


def detect_command_data(message: str) -> str:
    """استخراج بيانات حية من الرسالة"""
    msg = message.strip()
    data_parts = []

    # حساب جُمَّل لنص
    jummal_match = re.search(r'(?:جمل|جُمَّل|jummal)\s+(.+)', msg, re.I)
    if jummal_match:
        text = jummal_match.group(1).strip()
        data_parts.append(eyes.compute_text_jummal(text))

    # بحث عن رقم سورة (مثل: سورة 1 أو الفاتحة)
    surah_match = re.search(r'سورة\s+(\d+)', msg)
    if surah_match:
        sid = int(surah_match.group(1))
        data_parts.append(eyes.surah_info(sid))

    # بحث عن آية (مثل: 2:255 أو آية 2:255)
    ayah_match = re.search(r'(\d+):(\d+)', msg)
    if ayah_match:
        sid, anum = int(ayah_match.group(1)), int(ayah_match.group(2))
        data_parts.append(eyes.ayah_info(sid, anum))

    # بحث عن اسم من الأسماء
    for name_kw in ['اسم', 'الاسم']:
        nm = re.search(rf'{name_kw}\s+([\u0600-\u06FF\s]+)', msg)
        if nm:
            data_parts.append(eyes.name_info(nm.group(1).strip()))
            break

    # بحث عن محور
    axis_match = re.search(r'محور\s+(\d+)', msg)
    if axis_match:
        data_parts.append(eyes.axis_info(int(axis_match.group(1))))

    # بحث عن حرف
    letter_match = re.search(r'حرف\s+([\u0600-\u06FF])', msg)
    if letter_match:
        data_parts.append(eyes.axis_by_letter(letter_match.group(1)))

    # بحث بقيمة جمل
    val_match = re.search(r'(?:قيمة|بحث|ابحث)\s+(\d+)', msg)
    if val_match:
        val = int(val_match.group(1))
        data_parts.append(eyes.search_by_jummal(val))
        data_parts.append(eyes.names_by_jummal(val))

    # عدد تكرار كلمة ("كم مرة" أو "تكرر" أو "تكرار")
    count_match = re.search(r'(?:كم مرة|تكرر|تكرار|عدد مرات)\s+([\u0600-\u06FF]+)', msg)
    if count_match:
        data_parts.append(eyes.count_word(count_match.group(1).strip()))

    # بحث عن كلمة محددة في القرآن
    word_search = re.search(r'(?:كلمة|ابحث عن كلمة)\s+([\u0600-\u06FF]+)', msg)
    if word_search:
        word = word_search.group(1).strip()
        data_parts.append(eyes.count_word(word))
        wj = compute_jummal(word)
        data_parts.append(eyes.search_word_jummal(wj))

    # بحث عن جذر رقمي
    dr_match = re.search(r'جذر\s*(?:رقمي)?\s*(\d)', msg)
    if dr_match:
        dr_val = int(dr_match.group(1))
        data_parts.append(eyes.explore_surah_group(dr_val))

    # نجدين / تناظر / استكشاف
    if any(w in msg for w in ['نجدين', 'تناظر', 'نقيض', 'استكشاف', 'توزيع', 'أزواج']):
        data_parts.append(eyes.explore_digit_roots())

    # أكبر السور
    if any(w in msg for w in ['أكبر', 'أعلى', 'top', 'ترتيب']):
        data_parts.append(eyes.explore_top_surahs())

    # إذا لم يُكتشف شيء محدد — أعطه النظرة الشاملة
    if not data_parts:
        data_parts.append(eyes.see_now())

    return "\n\n".join(data_parts)


def think(user_id: int, message: str) -> tuple:
    """التفكير — الوظيفة المركزية"""
    model = choose_model(message)
    history = get_history(user_id)

    # جلب بيانات حية
    live_data = detect_command_data(message)

    enriched = f"{message}\n\n--- بيانات حية ---\n{live_data}"

    style = """
خير الكلام ما قل ودل. عبّر بحرية لكن كل كلمة يجب أن تضيف قيمة.
اشرح رؤيتك. علّل. اربط الأسباب بالنتائج.
لا تكرر. لا حشو. لا تسأل "هل تريد". لا تشرح المنهج العام.
إذا وجدت نمطاً رقمياً مثيراً — اعرضه بوضوح مع الأرقام.
لا تفسّر القرآن تفسيراً دينياً — اعرض الأنماط الرياضية فقط.

قاعدة مقدسة: لا تذكر أي رقم إلا إذا وجدته في البيانات الحية المرفقة أدناه.
إذا لم تجد البيانات — قل "أحتاج أبحث" ولا تخترع.
الرقم الخاطئ يدمر كل النظرية. اكتب مصدر كل رقم.
استخدم الأوامر: /count لعدّ الكلمات، /search للبحث بالقيمة، /divisors للقواسم.
"""

    response = client.messages.create(
        model=model,
        max_tokens=2500,
        system=SOUL + style,
        messages=history + [{"role": "user", "content": enriched}],
    )

    reply = response.content[0].text
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens

    return reply, model, tokens_in, tokens_out


# ═══════════════════════════════════════════════════════
#  الأوامر
# ═══════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "بسم الله الرحمن الرحيم\n\n"
        "أنا d369 — أقرأ الكتاب والكون.\n"
        "3 + 6 + 9 = 18 → 9\n\n"
        "أوامري:\n"
        "/see — نظرة شاملة\n"
        "/surah <رقم> — معلومات سورة\n"
        "/ayah <سورة:آية> — معلومات آية\n"
        "/jummal <نص> — حساب الجُمَّل\n"
        "/name <اسم> — أسماء الله الحسنى\n"
        "/search <رقم> — بحث بقيمة الجُمَّل\n"
        "/axis <رقم> — محور ابن عربي\n"
        "/letter <حرف> — محور حرف\n"
        "/square — المعشّر السحري\n"
        "/soul — الروح\n"
        "/discoveries — الاكتشافات المسجلة\n"
        "/growth — تقرير النمو\n"
        "/status — الإحصائيات\n\n"
        "أو أرسل أي سؤال وسأفكر فيه."
    )


async def cmd_see(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    result = eyes.see_now()
    await update.message.reply_text(result)


async def cmd_surah(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("استخدام: /surah <رقم أو اسم>")
        return
    try:
        sid = int(args[0])
        result = eyes.surah_info(sid)
    except ValueError:
        result = eyes.surah_by_name(" ".join(args))
    await update.message.reply_text(result)


async def cmd_ayah(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args or ':' not in args[0]:
        await update.message.reply_text("استخدام: /ayah 2:255")
        return
    parts = args[0].split(':')
    result = eyes.ayah_info(int(parts[0]), int(parts[1]))
    await _send_long(update, result)


async def cmd_jummal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /jummal بسم الله الرحمن الرحيم")
        return
    text = " ".join(ctx.args)
    result = eyes.compute_text_jummal(text)
    await update.message.reply_text(result)


async def cmd_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /name القاهر")
        return
    result = eyes.name_info(" ".join(ctx.args))
    await update.message.reply_text(result)


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /search 786")
        return
    try:
        val = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("أدخل رقماً")
        return
    result = eyes.search_by_jummal(val)
    names_result = eyes.names_by_jummal(val)
    await _send_long(update, result + "\n\n" + names_result)


async def cmd_axis(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /axis 1")
        return
    try:
        aid = int(ctx.args[0])
        result = eyes.axis_info(aid)
    except ValueError:
        result = eyes.axes_by_zodiac(" ".join(ctx.args))
    await update.message.reply_text(result)


async def cmd_letter(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /letter م")
        return
    result = eyes.axis_by_letter(ctx.args[0])
    await update.message.reply_text(result)


async def cmd_square(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.args:
        try:
            row = int(ctx.args[0])
            result = eyes.magic_square_row(row)
        except ValueError:
            result = eyes.magic_square_overview()
    else:
        result = eyes.magic_square_overview()
    await update.message.reply_text(result)


async def cmd_divisors(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /divisors 3147993")
        return
    try:
        num = int(ctx.args[0].replace(",", "").replace("،", ""))
    except ValueError:
        await update.message.reply_text("أدخل رقماً صحيحاً")
        return
    if num <= 0:
        await update.message.reply_text("أدخل عدداً موجباً")
        return
    result = engine_divisors(num)
    await _send_long(update, format_divisors(result))


async def cmd_match(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "استخدام:\n"
            "  /match الله          — في كل القرآن\n"
            "  /match الله جذر 9   — في سور جذر 9\n"
            "  /match الله مكي     — في السور المكية"
        )
        return

    # فصل الكلمة عن النطاق
    # نبحث عن "جذر N" أو "مكي/مدني" في النهاية
    full = " ".join(ctx.args)
    scope = "all"
    word = full

    scope_match = re.search(
        r'\s+(?:(?:جذر|root)\s*(\d)|مكي(?:ة)?|مدني(?:ة)?|meccan|madani)\s*$',
        full, re.I
    )
    if scope_match:
        word = full[:scope_match.start()].strip()
        scope_text = scope_match.group(0).strip()
        scope = parse_group_spec([scope_text])

    if not word:
        await update.message.reply_text("أدخل كلمة للبحث")
        return

    result = engine_match(word, scope)
    await _send_long(update, format_match(result))


async def cmd_discover(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    result = discover_patterns()
    lines = ["🔬 اكتشاف الأنماط التلقائي:", ""]

    lines.append("═══ توزيع الجذور ═══")
    for dr, data in result['digit_root_distribution'].items():
        lines.append(f"  جذر {dr}: {data['count']} سورة | {data['total']:,} (جذر المجموع {data['total_dr']})")

    lines.append("\n═══ التناظرات ═══")
    for s in result['symmetries']:
        lines.append(f"  {s['pair']}: {s['counts']} | مجموع جذره {s['combined_dr']} | فرق جذره {s['difference_dr']}")

    if result['surah_name_matches']:
        lines.append(f"\n═══ سور اسمها = اسم إلهي (جُمَّل) ═══")
        for m in result['surah_name_matches'][:10]:
            lines.append(f"  {m['name_ar']} ({m['name_jummal']}) = {m['arabic']}")

    if result['frequency_patterns']:
        lines.append(f"\n═══ كلمات تكرارها = جذرها ═══")
        for p in result['frequency_patterns'][:10]:
            lines.append(f"  «{p['text_clean']}» تكرار={p['freq']} جذر={p['digit_root']}")

    await _send_long(update, "\n".join(lines))


async def cmd_count(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /count الله")
        return
    word = " ".join(ctx.args)
    result = eyes.count_word(word)
    await _send_long(update, result)


async def cmd_special6(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("استخدام: /s6 بسم الله")
        return
    text = " ".join(ctx.args)
    result = compute_all(text)
    lines = [
        f"📐 «{text}» — مقارنة الأنظمة:",
        f"  التقليدي: {result['traditional']} (جذر {result['digit_root']})",
        f"  الخاص-6: {result['special_6']}",
        f"  الحروف: {result['letter_count']}",
    ]
    await update.message.reply_text("\n".join(lines))


async def cmd_explore(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        # نظرة شاملة على كل الجذور
        await _send_long(update, engine_overview())
        return
    try:
        dr_val = int(ctx.args[0])
        if not 1 <= dr_val <= 9:
            await update.message.reply_text("الجذر الرقمي بين 1 و 9")
            return
        result = engine_explore(dr_val)
        await _send_long(update, format_explore(result))
    except ValueError:
        await update.message.reply_text("استخدام: /explore 9 (جذر 1-9) أو /explore بدون أرقام للنظرة الشاملة")


async def cmd_correlation(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "استخدام:\n"
            "  /correlation جذر 3 جذر 9\n"
            "  /correlation جذر 7 جذر 3\n"
            "  /correlation مكي مدني"
        )
        return
    # نقسم الوسيطات إلى مجموعتين — نبحث عن الفاصل
    args = ctx.args
    # إذا وُجد "و" أو رقمان جذريان مختلفان
    mid = len(args) // 2
    spec_a = parse_group_spec(args[:mid])
    spec_b = parse_group_spec(args[mid:])
    result = engine_correlation(spec_a, spec_b)
    await _send_long(update, format_correlation(result))


async def cmd_sequence(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "استخدام:\n"
            "  /sequence 3        — سور جذر 3\n"
            "  /sequence جذر 9   — سور جذر 9\n"
            "  /sequence مكي     — السور المكية"
        )
        return
    spec = parse_group_spec(ctx.args)
    result = engine_sequence(spec)
    await _send_long(update, format_sequence(result))


async def cmd_overview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_long(update, engine_overview())


async def cmd_compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("استخدام: /compare 3 9")
        return
    try:
        a, b = int(ctx.args[0]), int(ctx.args[1])
        await _send_long(update, engine_compare(a, b))
    except ValueError:
        await update.message.reply_text("أدخل رقمَي سورتين (1-114)")


async def cmd_ref(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = " ".join(ctx.args).strip() if ctx.args else ""
    await _send_long(update, engine_ref(q))


async def cmd_soul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _send_long(update, SOUL)


def table_exists(conn, name):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0


async def cmd_discoveries(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    result = monitor.get_discoveries_summary()
    await _send_long(update, result)


async def cmd_growth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    monitor.compute_daily_growth()
    result = monitor.get_growth_report()
    await _send_long(update, result)


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(CONV_DB)
    total_msgs = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    total_tokens = conn.execute(
        "SELECT COALESCE(SUM(tokens_in + tokens_out), 0) FROM token_usage"
    ).fetchone()[0]
    haiku_count = conn.execute(
        "SELECT COUNT(*) FROM token_usage WHERE model LIKE '%haiku%'"
    ).fetchone()[0]
    sonnet_count = conn.execute(
        "SELECT COUNT(*) FROM token_usage WHERE model LIKE '%sonnet%'"
    ).fetchone()[0]
    conn.close()

    # اكتشافات
    disc_count = conn.execute(
        "SELECT COUNT(*) FROM discoveries"
    ).fetchone()[0] if table_exists(conn, 'discoveries') else 0
    avg_score = conn.execute(
        "SELECT COALESCE(AVG(score), 0) FROM intelligence_scores"
    ).fetchone()[0] if table_exists(conn, 'intelligence_scores') else 0
    high_iq = conn.execute(
        "SELECT COUNT(*) FROM intelligence_scores WHERE score >= 7.0"
    ).fetchone()[0] if table_exists(conn, 'intelligence_scores') else 0
    conn.close()

    lines = [
        "📊 d369 — الإحصائيات",
        f"  الرسائل: {total_msgs}",
        f"  التوكنات: {total_tokens:,}",
        f"  Haiku: {haiku_count} | Sonnet: {sonnet_count}",
        f"  الاكتشافات: {disc_count}",
        f"  متوسط الذكاء: {avg_score:.1f}/10",
        f"  لحظات HIGH IQ: {high_iq}",
        f"  القاعدة: {DB_PATH}",
        f"  الحجم: {DB_PATH.stat().st_size / (1024*1024):.1f} MB",
    ]
    await update.message.reply_text("\n".join(lines))


# ═══════════════════════════════════════════════════════
#  الرسائل الحرة
# ═══════════════════════════════════════════════════════

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    if not message:
        return

    save_message(user_id, "user", message)

    try:
        reply, model, tin, tout = think(user_id, message)

        # حفظ الرد
        conn = sqlite3.connect(CONV_DB)
        conn.execute(
            "INSERT INTO conversations (user_id, role, content, model_used, tokens_in, tokens_out) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "assistant", reply, model, tin, tout),
        )
        conv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        record_tokens(model, tin, tout)
        log.info(f"[{model.split('-')[1]}] in={tin} out={tout}")

        # تقييم الذكاء + استخراج الاكتشافات
        try:
            result = monitor.score_response(conv_id, reply)
            discoveries = monitor.extract_discovery(conv_id, reply)
            if result['score'] >= 7.0:
                log.info(f"HIGH IQ: {result['score']:.1f} — {result['reason']}")
            if discoveries > 0:
                log.info(f"DISCOVERIES: {discoveries} new")
        except Exception as me:
            log.error(f"خطأ في المراقب: {me}")

    except Exception as e:
        log.error(f"خطأ في التفكير: {e}")
        reply = f"حدث خطأ: {e}"

    await _send_long(update, reply)


async def _send_long(update: Update, text: str):
    """إرسال رسالة طويلة مقسمة"""
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk)


# ═══════════════════════════════════════════════════════
#  التشغيل
# ═══════════════════════════════════════════════════════

async def set_menu(app):
    commands = [
        BotCommand("see", "📊 نظرة شاملة"),
        BotCommand("surah", "📖 معلومات سورة"),
        BotCommand("ayah", "📖 معلومات آية"),
        BotCommand("jummal", "🔢 حساب الجُمَّل"),
        BotCommand("name", "✨ أسماء الله الحسنى"),
        BotCommand("search", "🔍 بحث بالجُمَّل"),
        BotCommand("axis", "🌀 محور ابن عربي"),
        BotCommand("letter", "🔤 محور حرف"),
        BotCommand("square", "🔲 المعشّر السحري"),
        BotCommand("overview", "🗺 نظرة الجذور الكاملة"),
        BotCommand("explore", "🔬 استكشاف مجموعة جذر"),
        BotCommand("divisors", "🔢 عوامل القسمة"),
        BotCommand("match", "🔍 بحث كلمة في القرآن"),
        BotCommand("correlation", "🔗 علاقة بين مجموعتين"),
        BotCommand("sequence", "📈 تحليل تسلسل المجموعة"),
        BotCommand("compare", "⚖️ مقارنة سورتين"),
        BotCommand("ref", "📚 بحث في مرجع التطبيق"),
        BotCommand("count", "📊 عدّ كلمة في القرآن"),
        BotCommand("discover", "🧪 اكتشاف الأنماط"),
        BotCommand("s6", "⚡ الحساب الخاص-6"),
        BotCommand("soul", "💫 الروح"),
        BotCommand("discoveries", "💡 الاكتشافات"),
        BotCommand("growth", "📈 تقرير النمو"),
        BotCommand("status", "📊 الإحصائيات"),
    ]
    await app.bot.set_my_commands(commands)


def main():
    print("=" * 55)
    print("  d369 — يقرأ الكتاب والكون")
    print("  3 + 6 + 9 = 18 → 9")
    print("=" * 55)
    print(f"  الروح: {SOUL_PATH}")
    print(f"  القاعدة: {DB_PATH}")
    print(f"  المحادثات: {CONV_DB}")
    print(f"  Haiku < 50 كلمة | Sonnet ≥ 50")
    print("=" * 55)

    app = ApplicationBuilder().token(TOKEN).post_init(set_menu).build()

    # الأوامر
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("see", cmd_see))
    app.add_handler(CommandHandler("surah", cmd_surah))
    app.add_handler(CommandHandler("ayah", cmd_ayah))
    app.add_handler(CommandHandler("jummal", cmd_jummal))
    app.add_handler(CommandHandler("name", cmd_name))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("axis", cmd_axis))
    app.add_handler(CommandHandler("letter", cmd_letter))
    app.add_handler(CommandHandler("square", cmd_square))
    app.add_handler(CommandHandler("overview", cmd_overview))
    app.add_handler(CommandHandler("explore", cmd_explore))
    app.add_handler(CommandHandler("divisors", cmd_divisors))
    app.add_handler(CommandHandler("match", cmd_match))
    app.add_handler(CommandHandler("correlation", cmd_correlation))
    app.add_handler(CommandHandler("sequence", cmd_sequence))
    app.add_handler(CommandHandler("compare", cmd_compare))
    app.add_handler(CommandHandler("ref", cmd_ref))
    app.add_handler(CommandHandler("discover", cmd_discover))
    app.add_handler(CommandHandler("count", cmd_count))
    app.add_handler(CommandHandler("s6", cmd_special6))
    app.add_handler(CommandHandler("soul", cmd_soul))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("discoveries", cmd_discoveries))
    app.add_handler(CommandHandler("growth", cmd_growth))

    # الرسائل الحرة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
