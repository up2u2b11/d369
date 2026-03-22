# Addendum to Paper III — Orthographic Layer Clarification
## Added: March 22, 2026

### Clarification

The K6 Surah-level result reported in this paper (51/114 = 44.7%, p = 0.007) was computed on phonetically faithful text (Simple-Clean orthography). Under Uthmani orthography — the historical script of the Quran manuscript tradition — the K6 Surah-level result is 30/114 = 26% (not significant).

### Cause of divergence

The divergence between orthographic layers traces to 16,534 word-level differences, predominantly:

1. **ي/ى alternation** in "في" (1,125 occurrences) — K6 assigns different values to yāʼ (111,000) and alif maqṣūra (111,100); Abjad treats them identically (both = 10)
2. **Hamza representation** آ vs ءا (252 occurrences)
3. **الصلاة/الصلوة alternation** (68 occurrences)

### What is unaffected

**Word-level results are entirely robust across both scripts:**

| | Abjad SC | Abjad UT | K6 SC | K6 UT |
|---|---|---|---|---|
| Word-level | 37.9% p≈0 | 39.1% p≈0 | 34.2% p≈0 | 35.3% p≈0 |

The Uthmani text produces slightly **stronger** z-scores than Simple-Clean.

### Additional finding

All ten canonical readings (Hafs, Warsh, Qalun, Shuʿba, al-Duri, al-Bazzi, Qunbul, al-Susi, Hisham, Rawis) produce identical results under Uthmani orthography. 12 Surahs maintain invariant digital roots across both orthographic layers.

### Correction to this paper

The original text should be read with the understanding that K6 Surah-level results apply to Simple-Clean orthography. The core claim of system-independence is supported by word-level results, which are invariant across both orthographic layers and both encoding systems.
