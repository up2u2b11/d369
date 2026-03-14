-- d369 — قاعدة بيانات المحرك القرآني
-- 7 جداول أساسية

-- 1. الحروف — 28 حرف عربي بقيم الجُمَّل
CREATE TABLE IF NOT EXISTS letters (
    letter_id INTEGER PRIMARY KEY,
    letter TEXT NOT NULL,
    letter_name TEXT,
    jummal_value INTEGER NOT NULL,
    digit_root INTEGER NOT NULL,
    abjad_order INTEGER NOT NULL
);

-- 2. السور — 114 سورة
CREATE TABLE IF NOT EXISTS surahs (
    surah_id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT,
    ayah_count INTEGER NOT NULL DEFAULT 0,
    revelation_type TEXT,
    jummal_total INTEGER DEFAULT 0,
    digit_root INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    letter_count INTEGER DEFAULT 0
);

-- 3. الآيات — 6236 آية
CREATE TABLE IF NOT EXISTS ayahs (
    ayah_id INTEGER PRIMARY KEY AUTOINCREMENT,
    surah_id INTEGER NOT NULL,
    ayah_number INTEGER NOT NULL,
    text_uthmani TEXT NOT NULL,
    text_clean TEXT NOT NULL,
    jummal_value INTEGER NOT NULL DEFAULT 0,
    digit_root INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    letter_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(surah_id, ayah_number),
    FOREIGN KEY (surah_id) REFERENCES surahs(surah_id)
);

-- 4. الكلمات
CREATE TABLE IF NOT EXISTS words (
    word_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ayah_id INTEGER NOT NULL,
    surah_id INTEGER NOT NULL,
    ayah_number INTEGER NOT NULL,
    word_position INTEGER NOT NULL,
    text_uthmani TEXT NOT NULL,
    text_clean TEXT NOT NULL,
    jummal_value INTEGER NOT NULL DEFAULT 0,
    digit_root INTEGER NOT NULL DEFAULT 0,
    letter_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (ayah_id) REFERENCES ayahs(ayah_id)
);

-- 5. أسماء الله الحسنى — 99 + محمد ﷺ
CREATE TABLE IF NOT EXISTS names_99 (
    name_id INTEGER PRIMARY KEY,
    arabic TEXT NOT NULL,
    transliteration TEXT,
    meaning_ar TEXT,
    meaning_en TEXT,
    jummal_value INTEGER NOT NULL,
    digit_root INTEGER NOT NULL,
    square_row INTEGER,
    square_col INTEGER
);

-- 6. الاكتشافات
CREATE TABLE IF NOT EXISTS discoveries (
    discovery_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence TEXT,
    digit_root_involved INTEGER,
    surah_ref INTEGER,
    ayah_ref INTEGER,
    status TEXT DEFAULT 'pending',
    confidence REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 7. المعشّرات (المربعات السحرية)
CREATE TABLE IF NOT EXISTS magic_squares (
    square_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    size INTEGER NOT NULL,
    expected_sum INTEGER NOT NULL,
    grid_json TEXT,
    actual_row_sums TEXT,
    actual_col_sums TEXT,
    actual_diag_sums TEXT,
    is_valid INTEGER DEFAULT 0,
    verified_at TEXT
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_ayahs_surah ON ayahs(surah_id);
CREATE INDEX IF NOT EXISTS idx_ayahs_jummal ON ayahs(jummal_value);
CREATE INDEX IF NOT EXISTS idx_ayahs_digit ON ayahs(digit_root);
CREATE INDEX IF NOT EXISTS idx_words_ayah ON words(ayah_id);
CREATE INDEX IF NOT EXISTS idx_words_jummal ON words(jummal_value);
CREATE INDEX IF NOT EXISTS idx_words_digit ON words(digit_root);
CREATE INDEX IF NOT EXISTS idx_names_jummal ON names_99(jummal_value);
CREATE INDEX IF NOT EXISTS idx_names_digit ON names_99(digit_root);
