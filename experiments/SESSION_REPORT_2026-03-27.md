# Session Report — March 27, 2026
# تقرير الجلسة — 27 مارس 2026

**22 discoveries in a single session. Self-correction of G14. Paper VII v2 published.**
**22 اكتشافاً في جلسة واحدة. تصحيح ذاتي لـ G14. نشر Paper VII v2.**

---

## The Bedrock — What Cannot Be Broken
## الصخرة — ما لا يُكسر

**Paper I word-level fingerprint works in BOTH orthographies:**

| Orthography | Words | In {3,6,9} | Percentage |
|-------------|-------|-----------|------------|
| Modern (simple) | 78,248 | 29,917 | **38.23%** |
| Uthmani (classical) | 77,881 | 30,888 | **39.66%** |
| Expected (random) | — | — | 33.33% |

- **5 control texts** show no deviation from chance
- **Frame (function words) drives the bias** — ~45% in both orthographies
- **Content words** are lower — 36-38% — but also above chance
- Uthmani rules add ~1.4% to ANY Arabic text — the 5% Quran advantage is text-intrinsic
- Bukhari after same Uthmani rules: 33.20% → 34.54% (still at chance)

---

## Discoveries 1-22 — Summary
## الاكتشافات 1-22 — ملخص

### Encoding Systems (1-5)
1. **Abjad = Saghir = Ordinal** — mathematical identity (35/114 identical for all three)
2. **K6 alone** carries surah-level fingerprint (51/114 = 44.7%, p = 0.007)
3. **Letter Count** — independent layer (48/114 = 42.1%, p = 0.031)
4. **Shape independent of length** — Z/9Z modular residual (47/114, p = 0.047)
5. **Short surahs strongest** (17/29 = 58.6%, p = 0.005)

### G14 Correction (6-7)
6. **G14 = counting property**: d×(n−1) ≡ 0 (mod 9). Real p ≈ 0.054, not p < 0.00001
7. **Paper I unaffected** — its main argument was word-level, never G14

### Mechanism Identification (8-12)
8. **Three hamza forms (ؤ, ئ, ء)** are the driver — not ة
9. **ؤ alone** (673 chars = 0.2%) drops fingerprint from 51 → 30
10. **No correlation with hamza density** (r = −0.02)
11. **Shuffling hamza distribution breaks fingerprint** (p = 0.007)
12. Fingerprint linked to **orthographic script**, not phonetics

### Orthographic Tests (13-18)
13. K6 fingerprint carried by hamza **forms** in the script
14. **K6 surah: modern only** (51/114) — disappears in Uthmani (37/114)
15. **Meccan vs Medinan**: no difference (p = 0.25) — spans both
16. **~0.7% of random encodings** give any text a fingerprint
17. **Any value with dr(ؤ)=1** gives 51/114 — K6 is not unique
18. **K6 fingerprint = synergy** (alifs + hamzas) — neither alone suffices

### The Decisive Tests (19-22)
19. ⭐ **Paper I works in BOTH orthographies** — Uthmani is STRONGER (39.66% > 38.23%)
20. Uthmani rules pull words toward {3,6,9} — but this is true for ANY Arabic text (~1.4% lift)
21. **Frame vs Content holds in both orthographies** — function words ~45% in both
22. ⭐ **Bukhari after Uthmani rules: 34.54%** — still at chance. The ~5% Quran advantage is text-intrinsic.

---

## What Stands, What Fell
## ما صمد وما سقط

### Unbreakable ✓
- Paper I word-level: 38.23% (modern) / 39.66% (uthmani) — both significant
- Frame vs Content: function words carry the bias in both scripts
- 5 control texts = nothing, in any system, any orthography
- The ~5% advantage is text-intrinsic, not from spelling rules

### With Caveats ⚠
- K6 surah-level (p=0.007) — modern orthography only
- Letter Count (p=0.031) — needs Uthmani verification
- Shape residual (p=0.047) — borderline

### Fell ✗
- G14 as statistical argument (p≈0.054, counting property)
- "System-independent" as absolute claim (Abjad gives 30.7% at surah level)

---

## Files Created
## الملفات المُنشأة

| File | Purpose |
|------|---------|
| `experiment_blind.py` | 5 systems × 3 texts blind test |
| `experiment_reveal.py` | Identity reveal |
| `experiment_question.py` | Hard question + JSON output |
| `experiment_all_systems.py` | All 5 encoding systems |
| `experiment_shape_clean.py` | Modular residual (length vs shape) |
| `experiment_length_vs_shape.py` | Length decomposition |
| `experiment_g14_verify.py` | G14 permutation test |
| `experiment_g14_correct.py` | G14 counting property proof + Monte Carlo |

Results saved in `/home/emad/d369/results/experiment_*.json`

---

## Paper VII v2 — Published
## نشر Paper VII v2

- **DOI:** 10.5281/zenodo.19250269
- Section 2.3 corrected: G14 p < 0.00001 → p ≈ 0.054
- Mathematical proof added: d×(n−1) ≡ 0 (mod 9)
- Statistical argument redirected to K6 (p=0.006) and word-level (p=0.036)

---

*"The algorithms speak — not I." — Emad Suleiman Alwan*
*"الخوارزميات هي التي تنطق وليس أنا" — عماد سليمان علوان*

*22 discoveries. 1 self-correction. 1 unbreakable bedrock.*
*Session: March 27, 2026 — d369 Project*
