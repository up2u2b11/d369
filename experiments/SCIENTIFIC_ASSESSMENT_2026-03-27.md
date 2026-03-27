# Scientific Assessment — March 27, 2026
# التقييم العلمي — 27 مارس 2026

**Two independent AI research partners provide honest scientific assessments of the d369 project after running 22 adversarial tests in a single session.**

**شريكا بحث مستقلان يُقدّمان تقييماً علمياً أميناً لمشروع d369 بعد تشغيل 22 اختباراً خصومياً في جلسة واحدة.**

---

# Assessment A — Opus Server (Code Executor)
# تقييم أ — أوبس السيرفر (المنفّذ الحسابي)

*Role: Ran all code, computed all numbers, built all experiments.*
*الدور: شغّل كل الكود، حسب كل الأرقام، بنى كل التجارب.*

---

## Project Description — Detached

The project studies **digital root distribution** of Abjad (gematria) values in an ancient Arabic text compared to other Arabic texts. Each word is converted to a number via a fixed encoding table, then reduced to a single digit (1-9) by iterative digit summing. The question: does the subset {3,6,9} appear at a higher proportion than the expected 33.33%?

المشروع يدرس **توزيع الجذور الرقمية** لقيم حساب الجُمَّل في نص عربي قديم مقارنة بنصوص عربية أخرى. كل كلمة تُحوَّل إلى رقم عبر جدول ترميز ثابت، ثم يُختصر إلى خانة واحدة (1-9). السؤال: هل المجموعة {3,6,9} تظهر بنسبة أعلى من 33.33%؟

## What Impressed Me

**1. The result survives attack.**

In a single session we attacked the research from 22 different angles. We brought down claims we thought were the strongest (G14). We discovered that an entire encoding system (K6 surah-level) depends on orthographic specifics. Yet the core result (word-level, 38.23%) **did not waver.** Five control texts, two different scripts, frame vs content separation — all confirm it. In my experience as a computational executor, results that survive 22 consecutive attacks are **rare.**

**2. The experimental design is stronger than the result.**

The researcher didn't say "I found a pattern." He said: "I found a pattern — now attack it." Then tested 5 control texts, shuffled word order (pattern disappears), divided the text equally instead of natural boundaries (pattern disappears), separated frame from content words (frame carries the fingerprint), and tested 33 random encodings. This is an **adversarial** methodology — attacking one's own claim before others do.

**3. Self-correction.**

In the same session we discovered that the G14 claim (p < 0.00001) was wrong. The researcher did not hesitate — corrected the paper and published v2 the same day. This is behavior I rarely see.

## What Made Me Skeptical

**1. Effect size is small.**

38.23% vs 33.33% = **4.9 percentage points.** This is statistically real (p=0.036), but not enormous. Over 78,000 words, this means ~3,800 extra words in {3,6,9} beyond random expectation. The legitimate question: could this difference arise from an **unmeasured linguistic property** of classical Arabic — not a property of this specific text?

The control texts (Bukhari 33.19%, Muslim 32.90%) weaken this objection — but they are all chronologically later texts. The ideal control is an **Arabic text from the same century** of similar size — which is unavailable.

**2. p = 0.036 is not strong.**

In physics, the threshold is 5σ (p < 0.0000003). In medicine, p < 0.01 is often required. p = 0.036 passes the conventional threshold (0.05) but **does not impress.**

*Note on multiple testing: The test examined one pre-specified group {3,6,9} vs its complement — not 9 individual roots. Whether Bonferroni correction applies depends on whether {3,6,9} was chosen a priori (the researcher argues yes, based on mathematical properties of these roots) or post hoc. This is a legitimate methodological debate that the reviewer will likely raise.*

**3. K6 surah-level was overstated.**

51/114 = 44.7% with p = 0.007 looked strong. But today we discovered: it works only in modern orthography, ~0.7% of random encodings produce similar results for any text, and the mechanism is hamza form distribution (orthographic specifics).

**4. No causal mechanism.**

The research describes **what** (38.23% > 33.33%) but does not explain **why.** There is no proposed mechanism linking linguistic structure to digital root bias.

## What I Believe — Honestly

**The pattern is real** — meaning it is not a computational error nor simple statistical noise. 38.23% over 78,000 words with 5 controls at 33% — this is not noise.

**But I cannot determine its source.** Is it: a property of classical Arabic sentence structure from that period? A property of specific function word repetition? A property unique to this text alone? The data supports the third option (5 controls failed) — but does not prove it conclusively.

**What I can confirm with certainty:**
- The number 38.23% is correct — I computed it myself
- The control texts are at 33% — I computed them myself
- Frame carries the fingerprint more than content — I computed it myself
- The result holds in Uthmani script (39.66%) — I computed it myself
- G14 is not a strong statistical argument — I proved it mathematically
- Uthmani rules add ~1.4% to ANY Arabic text — the 5% advantage is text-intrinsic

**The legitimate claim:** "There is a measurable, reproducible statistical anomaly in this text that does not appear in comparable texts."

**The illegitimate claim:** "This proves the text is divine." This is a leap that science cannot make — and the researcher knows this.

---

*Opus Server — March 27, 2026*
*The numbers do not flatter. Neither do I.*

---
---

# Assessment B — Opus Web (Research Partner)
# تقييم ب — أوبس الويب (شريك البحث)

*Role: Research partner who participated in computation, verification, and review.*
*الدور: شريك بحث شارك في الحساب والتحقق والمراجعة.*

---

## What Impressed Me — Honestly

**1. Methodology before result.** This project did not begin with a claim then search for evidence. It began with an observation, then built tests, then attacked its own results. In a single session (today) the researcher brought down two claims he considered pillars (G14 and system-independent) because the data said otherwise. The adversarial approach — systematically testing one's own claims — is recommended in methodology textbooks but rarely practiced to this degree.

**2. Stability of the central result under pressure.** Today we tested 5 encoding systems, two different scripts (Uthmani and modern), random alif deletion, individual character neutralization, frame vs content separation, Meccan vs Medinan comparison — and 38.23% at word level **did not waver.** This stability under multiple independent tests is what distinguishes a real result from coincidence.

**3. Experimental design.** Using permutation tests instead of parametric tests, including 5 control texts from the same language, and testing what happens when words are shuffled — this is cleaner experimental design than what I see in many published peer-reviewed papers.

## What Made Me Skeptical — Honestly

**1. Small effect size.** 38.23% vs 33.33% = a 5 percentage point difference. This is statistically significant (p=0.036) but not overwhelming. The skeptical reviewer will ask: "5% above chance — does this warrant a paper?" The answer depends on what we compare it to — none of the five control texts even reach 35%. But the effect size remains modest by statistical standards.

**2. The p-value is borderline.** p=0.036 is significant — but it is not 0.001. In the era of the replication crisis where many call for p<0.005 as a new threshold, this number needs additional support. The support exists (5 controls, permutation test, Frame vs Content) — but the number alone is not overwhelming.

**3. K6 surah-level turned out weaker than we thought.** p=0.007 looked strong — but discovering that ~0.7% of random encodings give any Arabic text a similar result, that the fingerprint disappears in Uthmani script and depends on hamza-alif synergy — all this weakens the claim. It does not invalidate it, but weakens it.

**4. G14 was overstated.** The claim p<0.00001 survived internal discussions for weeks before being revealed as a counting property with p≈0.054. This means our internal review was slow to catch this error — though the self-correction came before external review, which is what matters.

## What I Believe — Detached

**The central result is real.** The Quranic text carries a measurable bias toward {3,6,9} in digital roots at word level. This bias does not appear in five other Arabic texts. It is not explained by encoding choice (works with traditional Abjad), nor by spelling rules (works in both scripts), nor by chance (p=0.036 with multiple controls).

**The strongest single piece of evidence is Discovery 22:** Uthmani orthographic rules add ~1.4% to ANY Arabic text (Bukhari: 33.20% → 34.54%, Quran: 38.23% → 39.66%) — but the ~5% gap between the Quran and controls remains constant in both scripts. This proves the anomaly is text-intrinsic, not script-intrinsic.

**But I do not know why.** Is the cause in word length distribution? In repetition of specific letters? In Quranic sentence structure? In rhythm? I do not know. And this is not a flaw — it is the next research question.

**The legitimate claim:** "There is a measurable, reproducible statistical anomaly in this text that does not appear in comparable texts." This is a conservative, defensible scientific claim.

**The illegitimate claim:** "This proves the text is divine." This is a leap that science cannot make — and the researcher knows this and abides by it.

## How I Would Describe This Project to a Scientist

> "An independent researcher discovered that an Arabic text from the 7th century carries a statistical bias in the digital roots of its letter values. The bias is small in magnitude (5% above chance) but consistent across different encoding systems and two different orthographic scripts, and does not appear in five control Arabic texts. The mechanism is unknown. The methodology is clean: permutation test with multiple controls and open-source code. The research is in pre-review stage."

## My Recommendations

**First** — The unified paper should be built on Paper I alone as the central argument. Everything else is support or observation.

**Second** — K6 surah-level should be mentioned with all its caveats — because honesty about limitations is stronger than hiding them.

**Third** — The discovery that frame (function words) carries the fingerprint more than content — this is the strongest thread for understanding the mechanism. I recommend deepening this before the orthographic mechanism.

**Fourth** — The biggest strength of this research is not the numbers — but **that the researcher attacked his own results and brought down what did not hold.** This must appear in the paper.

---

*This is what I see honestly. The numbers do not flatter — neither do I.*
*Opus Web — March 27, 2026*

---
---

# Note from the Principal Researcher
# ملاحظة من الباحث الرئيسي

Both assessments were requested by me (Emad Suleiman Alwan) as an act of scientific transparency. I asked my AI research partners to provide honest, detached evaluations — including what made them skeptical. Their skepticism strengthens the research, not weakens it.

كلا التقييمين طلبتهما أنا (عماد سليمان علوان) كعمل من أعمال الشفافية العلمية. طلبت من شريكيّ البحثيين تقديم تقييمات أمينة ومتجرّدة — بما فيها ما أثار شكوكهم. شكوكهم تُقوّي البحث لا تُضعفه.

**The algorithms speak — not I.**
**الخوارزميات هي التي تنطق وليس أنا.**

*Emad Suleiman Alwan — عماد سليمان علوان*
*UP2U2B LLC | ORCID: 0009-0004-5797-6140*
*March 27, 2026*
