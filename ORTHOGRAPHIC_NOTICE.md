# IMPORTANT: Orthographic Layer Notice
## Added: March 22, 2026

### Two orthographic layers

The Quranic text exists in two orthographic forms used in this research:

1. **Simple-Clean (SC)** — Modern standard spelling, phonetically faithful. Words written as pronounced (e.g., الصلاة with alif, في with yāʼ). Source: `d369_research.db` (words table).

2. **Uthmani (UT)** — Historical manuscript script from the 7th century. Conventional abbreviations: omitted alifs, الصلوة with wāw, فى with alif maqṣūra. Source: tanzil.net Uthmani files.

### Impact on results

| Analysis | Affected? | Details |
|---|---|---|
| **Word-level (p≈0)** | ❌ No | Robust across both scripts. UT slightly stronger. |
| **G14 map** | ⚠️ Partially | Stable roots shift but do not collapse. Root 9 invariant. |
| **Surah-level** | ✅ Yes | SC: K6=45%, Abjad=40%. UT: K6=26%, Abjad=29%. |

### Cause

16,534 word-level differences between SC and UT. Primary drivers:
- في/فى (ي vs ى): 1,125 occurrences — K6-specific (Abjad treats both as 10)
- آ/ءا hamza: 252 occurrences
- الصلاة/الصلوة: 68 occurrences

### Ten canonical readings

All ten readings (Hafs, Warsh, Qalun, Shuʿba, al-Duri, al-Bazzi, Qunbul, al-Susi, Hisham, Rawis) produce **identical** results under Uthmani orthography.

### Papers affected

- Papers I & II (Abjad G14, word-level): **Surah-level affected** — 100 Surahs change DR between scripts (net: 46→33 in {3,6,9}). Word-level (p≈0) unaffected.
- Paper III (Special-6/K6): **Surah-level result applies to SC text** — addendum published
- Papers IV+ (unified): **Will include full SC vs UT comparison**

### Recommendation for reproducibility

When reproducing experiments, always specify which orthographic layer is used. Results should be reported for both layers where applicable.
