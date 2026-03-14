#!/usr/bin/env python3
"""
d369 — API محرك الجُمَّل
بورت 8369

الملكية الفكرية: عماد سليمان علوان
"""

import json
import sqlite3
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template

sys.path.insert(0, str(Path(__file__).parent))
from config import DB_PATH, DASHBOARD_PORT, digit_root
from quran_engine.search import (
    compute_all, search_by_number, get_divisors,
    get_ayah_detail, search_by_digit_root, find_matches, discover_patterns,
)
import eyes

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ─── لوحة التحكم ───

@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api')
def api_index():
    return jsonify({
        'name': 'd369',
        'description': 'محرك الجُمَّل القرآني + محاور ابن عربي',
        'version': '2.0',
    })


# ═══ JSON Data Endpoints (for dashboard) ═══

@app.route('/api/data/square')
def api_data_square():
    conn = get_db()
    row = conn.execute('SELECT grid_json, is_valid FROM magic_squares WHERE square_id=1').fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'no data'})
    grid = json.loads(row['grid_json'])
    return jsonify({'grid': grid, 'valid': bool(row['is_valid']), 'sum': 3394})


@app.route('/api/data/axes')
def api_data_axes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM axes_28 ORDER BY axis_id').fetchall()
    conn.close()
    axes = [dict(r) for r in rows]
    return jsonify({'axes': axes})


@app.route('/api/data/name')
def api_data_name():
    name = request.args.get('name', '')
    if not name:
        return jsonify({'found': False})
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM names_99 WHERE arabic=? OR name_without_al=? OR arabic LIKE ?',
        (name, name, f'%{name}%')
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({'found': False})
    return jsonify({'found': True, 'data': dict(row)})


@app.route('/api/data/surah')
def api_data_surah():
    sid = request.args.get('id', type=int)
    if not sid:
        return jsonify({'found': False})
    conn = get_db()
    row = conn.execute('SELECT * FROM surahs WHERE surah_id=?', (sid,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'found': False})
    return jsonify({'found': True, 'data': dict(row)})


@app.route('/api/data/search_value')
def api_data_search_value():
    value = request.args.get('value', type=int)
    scope = request.args.get('scope', 'words')
    if value is None:
        return jsonify({'results': []})
    conn = get_db()
    results = []
    if scope == 'words':
        rows = conn.execute(
            'SELECT w.text_clean, w.surah_id, w.ayah_number, w.jummal_value '
            'FROM words w WHERE w.jummal_value=? LIMIT 100', (value,)
        ).fetchall()
        results = [{'text': r['text_clean'], 'surah': r['surah_id'],
                     'ayah': r['ayah_number'], 'jummal': r['jummal_value']} for r in rows]
    elif scope == 'ayahs':
        rows = conn.execute(
            'SELECT a.surah_id, a.ayah_number, a.jummal_value, a.digit_root, s.name_ar '
            'FROM ayahs a JOIN surahs s ON a.surah_id=s.surah_id '
            'WHERE a.jummal_value=? LIMIT 100', (value,)
        ).fetchall()
        results = [{'surah': r['surah_id'], 'ayah': r['ayah_number'],
                     'jummal': r['jummal_value'], 'digit_root': r['digit_root'],
                     'surah_name': r['name_ar']} for r in rows]
    elif scope == 'surahs':
        rows = conn.execute(
            'SELECT surah_id, name_ar, jummal_total, digit_root FROM surahs '
            'WHERE jummal_total=? OR name_jummal=?', (value, value)
        ).fetchall()
        results = [{'id': r['surah_id'], 'name': r['name_ar'],
                     'jummal': r['jummal_total'], 'digit_root': r['digit_root']} for r in rows]
    elif scope == 'names':
        rows = conn.execute(
            'SELECT arabic, jummal_value, digit_root FROM names_99 '
            'WHERE jummal_value=?', (value,)
        ).fetchall()
        results = [{'name': r['arabic'], 'jummal': r['jummal_value'],
                     'digit_root': r['digit_root']} for r in rows]
    conn.close()
    return jsonify({'results': results, 'scope': scope, 'value': value})


@app.route('/api/data/digit_root')
def api_data_digit_root():
    root = request.args.get('root', type=int)
    scope = request.args.get('scope', 'surahs')
    if root is None:
        return jsonify({'results': []})
    conn = get_db()
    results = []
    if scope == 'surahs':
        rows = conn.execute(
            'SELECT surah_id, name_ar, jummal_total, digit_root FROM surahs '
            'WHERE digit_root=? ORDER BY surah_id', (root,)
        ).fetchall()
        results = [{'id': r['surah_id'], 'name': r['name_ar'],
                     'jummal': r['jummal_total'], 'digit_root': r['digit_root']} for r in rows]
    elif scope == 'names':
        rows = conn.execute(
            'SELECT arabic, jummal_value, digit_root FROM names_99 '
            'WHERE digit_root=? ORDER BY jummal_value', (root,)
        ).fetchall()
        results = [{'name': r['arabic'], 'jummal': r['jummal_value'],
                     'digit_root': r['digit_root']} for r in rows]
    conn.close()
    return jsonify({'results': results})


@app.route('/api/data/stats')
def api_data_stats():
    conn = get_db()
    surahs = conn.execute('SELECT COUNT(*) as c FROM surahs').fetchone()['c']
    ayahs = conn.execute('SELECT COUNT(*) as c FROM ayahs').fetchone()['c']
    words = conn.execute('SELECT COUNT(*) as c FROM words').fetchone()['c']
    names = conn.execute('SELECT COUNT(*) as c FROM names_99').fetchone()['c']
    axes = conn.execute('SELECT COUNT(*) as c FROM axes_28').fetchone()['c']
    total_j = conn.execute('SELECT SUM(jummal_total) as s FROM surahs').fetchone()['s'] or 0
    total_dr = digit_root(total_j)

    # digit root distribution
    dr_rows = conn.execute(
        'SELECT digit_root, COUNT(*) as c FROM surahs GROUP BY digit_root ORDER BY digit_root'
    ).fetchall()
    dr_dist = [{'root': r['digit_root'], 'count': r['c']} for r in dr_rows]

    # top 10 surahs
    top = conn.execute(
        'SELECT surah_id, name_ar, jummal_total, digit_root FROM surahs '
        'ORDER BY jummal_total DESC LIMIT 10'
    ).fetchall()
    top_surahs = [{'id': r['surah_id'], 'name': r['name_ar'],
                    'jummal': r['jummal_total'], 'digit_root': r['digit_root']} for r in top]

    conn.close()
    return jsonify({
        'surahs': surahs, 'ayahs': ayahs, 'words': words,
        'names': names, 'axes': axes,
        'total_jummal': total_j, 'total_digit_root': total_dr,
        'digit_root_distribution': dr_dist,
        'top_surahs': top_surahs,
    })


# ═══ Original API Endpoints ═══

@app.route('/api/jummal')
def api_jummal():
    text = request.args.get('text', '')
    if not text:
        return jsonify({'error': 'text parameter required'}), 400
    return jsonify(compute_all(text))


@app.route('/api/search/number')
def api_search_number():
    value = request.args.get('value', type=int)
    system = request.args.get('system', 'traditional')
    scope = request.args.get('scope', 'words')
    limit = request.args.get('limit', 100, type=int)
    if value is None:
        return jsonify({'error': 'value parameter required'}), 400
    return jsonify(search_by_number(value, system, scope, limit))


@app.route('/api/divisors')
def api_divisors():
    number = request.args.get('number', type=int)
    if number is None:
        return jsonify({'error': 'number parameter required'}), 400
    return jsonify(get_divisors(number))


@app.route('/api/ayah')
def api_ayah():
    surah = request.args.get('surah', type=int)
    ayah = request.args.get('ayah', type=int)
    if surah is None or ayah is None:
        return jsonify({'error': 'surah and ayah parameters required'}), 400
    result = get_ayah_detail(surah, ayah)
    if result is None:
        return jsonify({'error': 'ayah not found'}), 404
    return jsonify(result)


@app.route('/api/search/digit_root')
def api_digit_root():
    root = request.args.get('root', type=int)
    scope = request.args.get('scope', 'surahs')
    if root is None:
        return jsonify({'error': 'root parameter required'}), 400
    return jsonify(search_by_digit_root(root, scope))


@app.route('/api/match')
def api_match():
    text = request.args.get('text', '')
    if not text:
        return jsonify({'error': 'text parameter required'}), 400
    return jsonify(find_matches(text))


@app.route('/api/discover')
def api_discover():
    return jsonify(discover_patterns())


@app.route('/api/names99')
def api_names99():
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': 'name parameter required'}), 400
    result = eyes.name_info(name)
    return jsonify({'result': result})


@app.route('/api/names99/search')
def api_names99_search():
    jummal = request.args.get('jummal', type=int)
    if jummal is None:
        return jsonify({'error': 'jummal parameter required'}), 400
    result = eyes.names_by_jummal(jummal)
    return jsonify({'result': result})


@app.route('/api/surah')
def api_surah():
    sid = request.args.get('id', type=int)
    if sid is None:
        return jsonify({'error': 'id parameter required'}), 400
    result = eyes.surah_info(sid)
    return jsonify({'result': result})


@app.route('/api/axis')
def api_axis():
    aid = request.args.get('id', type=int)
    if aid is None:
        return jsonify({'error': 'id parameter required'}), 400
    result = eyes.axis_info(aid)
    return jsonify({'result': result})


@app.route('/api/square')
def api_square():
    result = eyes.magic_square_overview()
    return jsonify({'result': result})


@app.route('/api/explore')
def api_explore():
    result = eyes.explore_digit_roots()
    return jsonify({'result': result})


@app.route('/api/ref/jummal')
def api_ref_jummal():
    """آيات بقيمة جُمَّل محددة من مرجع التطبيق"""
    value = request.args.get('value', type=int)
    limit = request.args.get('limit', 20, type=int)
    if value is None:
        return jsonify({'error': 'value parameter required'}), 400
    conn = get_db()
    ayat = conn.execute(
        "SELECT surah, aya, text_clean, jummal FROM ref_ayat "
        "WHERE jummal=? ORDER BY surah, aya LIMIT ?",
        (value, limit)
    ).fetchall()
    words = conn.execute(
        "SELECT word_text, COUNT(*) as cnt FROM ref_words "
        "WHERE jummal=? GROUP BY word_text ORDER BY cnt DESC LIMIT 15",
        (value,)
    ).fetchall()
    conn.close()
    return jsonify({
        'value': value,
        'digit_root': digit_root(value),
        'ayat': [{'surah': r[0], 'aya': r[1], 'text': r[2], 'jummal': r[3]} for r in ayat],
        'words': [{'word': r[0], 'count': r[1]} for r in words],
    })


@app.route('/api/ref/ayah')
def api_ref_ayah():
    """بيانات آية من مرجع التطبيق مع كلماتها"""
    surah = request.args.get('surah', type=int)
    aya   = request.args.get('aya', type=int)
    if surah is None or aya is None:
        return jsonify({'error': 'surah and aya required'}), 400
    conn = get_db()
    row = conn.execute(
        "SELECT aya_global_id, text_clean, text_tashkeel, jummal, word_count, letter_count "
        "FROM ref_ayat WHERE surah=? AND aya=?", (surah, aya)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    gid, text_c, text_t, jum, wc, lc = row
    words_rows = conn.execute(
        "SELECT word_pos, word_text, jummal FROM ref_words "
        "WHERE aya_global_id=? ORDER BY word_pos", (gid,)
    ).fetchall()
    conn.close()
    return jsonify({
        'surah': surah, 'aya': aya,
        'text_clean': text_c, 'text_tashkeel': text_t,
        'jummal': jum, 'digit_root': digit_root(jum),
        'word_count': wc, 'letter_count': lc,
        'words': [{'pos': r[0], 'text': r[1], 'jummal': r[2], 'digit_root': digit_root(r[2])} for r in words_rows],
    })


@app.route('/api/ref/word')
def api_ref_word():
    """إحصاء كلمة في القرآن من مرجع التطبيق"""
    word = request.args.get('word', '').strip()
    if not word:
        return jsonify({'error': 'word parameter required'}), 400
    conn = get_db()
    rows = conn.execute(
        "SELECT word_text, jummal, COUNT(*) as cnt "
        "FROM ref_words WHERE word_text=? GROUP BY word_text, jummal",
        (word,)
    ).fetchall()
    if not rows:
        rows = conn.execute(
            "SELECT word_text, jummal, COUNT(*) as cnt "
            "FROM ref_words WHERE word_text LIKE ? GROUP BY word_text, jummal "
            "ORDER BY cnt DESC LIMIT 20",
            (f"%{word}%",)
        ).fetchall()
    conn.close()
    total = sum(r[2] for r in rows)
    return jsonify({
        'query': word, 'total': total,
        'forms': [{'word': r[0], 'jummal': r[1], 'digit_root': digit_root(r[1]), 'count': r[2]} for r in rows],
    })


if __name__ == '__main__':
    print(f"d369 API — بورت {DASHBOARD_PORT}")
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)
