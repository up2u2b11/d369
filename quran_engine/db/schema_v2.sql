-- d369 — ترقية قاعدة البيانات v2
-- إضافات: الحساب الخاص-6 + المواقع الدقيقة + اسم بدون أل

-- ═══ ترقية الحروف ═══
ALTER TABLE letters ADD COLUMN special_6 TEXT DEFAULT '';
ALTER TABLE letters ADD COLUMN position_alphabet INTEGER DEFAULT 0;
ALTER TABLE letters ADD COLUMN is_solar INTEGER DEFAULT 0;
ALTER TABLE letters ADD COLUMN is_lunar INTEGER DEFAULT 0;
ALTER TABLE letters ADD COLUMN dots_count INTEGER DEFAULT 0;

-- ═══ ترقية السور ═══
ALTER TABLE surahs ADD COLUMN name_jummal INTEGER DEFAULT 0;
ALTER TABLE surahs ADD COLUMN name_digit_root INTEGER DEFAULT 0;
ALTER TABLE surahs ADD COLUMN revelation_order INTEGER DEFAULT 0;
ALTER TABLE surahs ADD COLUMN jummal_special_6 TEXT DEFAULT '0';

-- ═══ ترقية الآيات ═══
ALTER TABLE ayahs ADD COLUMN ayah_num_quran INTEGER DEFAULT 0;
ALTER TABLE ayahs ADD COLUMN jummal_special_6 TEXT DEFAULT '0';

-- ═══ ترقية الكلمات ═══
ALTER TABLE words ADD COLUMN word_pos_in_surah INTEGER DEFAULT 0;
ALTER TABLE words ADD COLUMN word_pos_in_quran INTEGER DEFAULT 0;
ALTER TABLE words ADD COLUMN jummal_special_6 TEXT DEFAULT '0';

-- ═══ ترقية الأسماء ═══
ALTER TABLE names_99 ADD COLUMN name_without_al TEXT DEFAULT '';
ALTER TABLE names_99 ADD COLUMN jummal_without_al INTEGER DEFAULT 0;
ALTER TABLE names_99 ADD COLUMN quran_mentions INTEGER DEFAULT 0;

-- ═══ فهارس جديدة ═══
CREATE INDEX IF NOT EXISTS idx_words_surah_pos ON words(surah_id, word_pos_in_surah);
CREATE INDEX IF NOT EXISTS idx_words_quran_pos ON words(word_pos_in_quran);
CREATE INDEX IF NOT EXISTS idx_words_text ON words(text_clean);
CREATE INDEX IF NOT EXISTS idx_ayahs_quran_num ON ayahs(ayah_num_quran);
CREATE INDEX IF NOT EXISTS idx_surahs_digit ON surahs(digit_root);
