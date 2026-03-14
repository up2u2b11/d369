-- d369 — قاعدة بيانات المحرك الفلكي
-- 5 جداول

-- 1. الكواكب — 7 كواكب كلاسيكية
CREATE TABLE IF NOT EXISTS planets (
    planet_id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    symbol TEXT,
    jummal_value INTEGER,
    digit_root INTEGER,
    day_of_week TEXT,
    metal TEXT,
    letter TEXT
);

-- 2. محاور ابن عربي — 28 محور
CREATE TABLE IF NOT EXISTS axes_28 (
    axis_id INTEGER PRIMARY KEY,
    letter TEXT NOT NULL,
    letter_jummal INTEGER NOT NULL,
    divine_name TEXT NOT NULL,
    divine_name_jummal INTEGER,
    prophet TEXT NOT NULL,
    surah TEXT,
    cosmic_element TEXT,
    spiritual_energy TEXT,
    lunar_mansion TEXT,
    zodiac_sign TEXT
);

-- 3. الأبراج — 12 برج
CREATE TABLE IF NOT EXISTS zodiac_signs (
    sign_id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    symbol TEXT,
    element TEXT,
    ruling_planet_id INTEGER,
    start_degree REAL,
    jummal_value INTEGER,
    digit_root INTEGER
);

-- 4. التقويم الفلكي — المواقع اليومية
CREATE TABLE IF NOT EXISTS ephemeris_cache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    planet_id INTEGER NOT NULL,
    longitude REAL NOT NULL,
    latitude REAL,
    speed REAL,
    sign_id INTEGER,
    degree_in_sign REAL,
    axis_id INTEGER,
    retrograde INTEGER DEFAULT 0,
    UNIQUE(date, planet_id),
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

-- 5. العلاقات الفلكية
CREATE TABLE IF NOT EXISTS aspects (
    aspect_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    planet1_id INTEGER NOT NULL,
    planet2_id INTEGER NOT NULL,
    aspect_type TEXT NOT NULL,
    angle REAL NOT NULL,
    orb REAL NOT NULL,
    exact_date TEXT,
    significance TEXT
);

-- الفهارس
CREATE INDEX IF NOT EXISTS idx_eph_date ON ephemeris_cache(date);
CREATE INDEX IF NOT EXISTS idx_eph_planet ON ephemeris_cache(planet_id);
CREATE INDEX IF NOT EXISTS idx_aspects_date ON aspects(date);
