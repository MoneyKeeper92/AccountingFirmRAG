# 08 — Metrics, instrumentation and the month-6 decision

## 1. Principle: the database is the analytics source of truth

Under Spanish rules (AEPD), Mixpanel and GA4 may only track users who **accept cookies**, and
many won't. But the learning data (every answer, attempt, time, report) is **core service
data** stored in Supabase under the contract basis. So, as with Maxwell's 504k-attempt DB
export:

| Question | Source |
|---|---|
| Retention, questions/user, accuracy, question health, percentiles | **Supabase SQL** (100% of users) |
| Funnels on the website, acquisition channel, UX clicks, session replay | **Mixpanel** (consented users only, EU residency, opt-out by default) |
| SEO traffic | **Google Search Console** (no consent needed; aggregate) + GA4 (consented) |
| Cookieless site totals | **Cloudflare Web Analytics** (aggregate, no cookies) |
| Qualitative | Tally surveys, interviews, impugnaciones, community listening |

Acquisition channel is also stored server-side: the UTM params captured at sign-up are saved to
`users_profile.signup_source`, so channel attribution survives cookie rejection.

## 2. Mixpanel event plan (names in English, snake_case)

| Event | Key properties |
|---|---|
| `signup_completed` | method (magic_link/google), signup_source, utm_* |
| `onboarding_completed` | target_exam, exam_date_expected, has_academy, academy_name, hours_per_week, first_time_opositor |
| `test_started` | mode (tema/bloque/ley/simulacro/official_exam/review), exam_code, tema_codes[], n_questions, penalty_on, timed |
| `question_answered` | question_id, question_version, tema_code, correct, blank, time_ms, answer_changed, position_in_test |
| `explanation_viewed` | question_id, dwell_ms, boe_link_clicked |
| `explanation_rated` | question_id, helpful (bool) |
| `test_completed` | mode, n_correct, n_wrong, n_blank, score_net, score_100, duration_s, abandoned (bool) |
| `question_reported` | question_id, reason, has_comment |
| `review_queue_started` / `review_queue_completed` | items_due, items_done |
| `dashboard_viewed` | section |
| `percentile_viewed` | percentile |
| `share_card_created` | score_100, channel |
| `invite_sent` | channel |
| `pwa_installed` | platform |
| `survey_submitted` | survey_id (nps/pmf/wtp/monthly), score |
| `seo_page_cta_clicked` (site) | page_type (article/tema/exam/tool), page_path |

User properties: `target_exam`, `exam_date_expected`, `has_academy`, `academy_name`,
`signup_source`, `cohort_week`, `fundador` (bool).

## 3. Weekly digest (Claude generates it automatically, Kyle reads it in 5 minutes)

Sent every Monday to `hola@` (Make scenario or Claude scheduled run):
1. New sign-ups by channel; activation rate
2. WAU, questions answered, tests completed, simulacros
3. Retention: cohort table (W1/W2/W4)
4. Top 5 impugnaciones + status; questions auto-flagged by health metrics
5. SEO: clicks, impressions, top gaining queries, indexing issues
6. Notable feedback quotes (verbatim, Spanish, with a one-line English gloss)
7. **"One decision for Kyle this week"** (or "none")

## 4. North-star and supporting metrics

**North-star:** **Weekly Active Learners (WAL)**, users who answered ≥20 questions in the
week. (Captures real study, not drive-by visits.)

| Metric | Definition | Month-6 "good" | Month-6 "great" |
|---|---|---|---|
| Activation | % of sign-ups completing ≥1 test within 24 h | 50% | 65% |
| W4 retention | % of a cohort that is a WAL in week 4 | 20% | 30% |
| W8 retention | % of a cohort that is a WAL in week 8 | 12% | 20% |
| Depth | Median questions/week per WAL | 100 | 200 |
| Simulacro adoption | % of WAL doing ≥1 simulacro/month | 30% | 50% |
| Explanation engagement | % of wrong answers where the explanation is opened | 40% | 60% |
| Quality | Published-question error rate (upheld impugnaciones / questions attempted ≥30×) | <3% | <1% |
| Response time | Median impugnación resolution | <72 h | <24 h |
| PMF (Sean Ellis) | % "muy decepcionado" if Tesón disappeared (users with ≥3 active weeks) | 30% | ≥40% |
| NPS | Monthly survey | 30 | 50 |
| Organic share | % of sign-ups from SEO + word of mouth | 30% | 50% |
| Willingness to pay | Van Westendorp "acceptable" price range | overlaps €5–10/mo | overlaps €10–15/mo |
| B2B signal | Named academies among users + academies that respond to "¿te interesa?" | 20 named / 2 conversations | 50 named / 5 conversations |

## 5. Month-6 decision (≈ end of April 2027)

| Outcome | Condition | Next step |
|---|---|---|
| **Go B2C + start B2B** | W4 ≥20%, PMF ≥30%, WTP overlaps €5–10 | Turn on paid plans before the exam (Fundadores keep a discount); build the academy dashboard; pilot with 1–2 academies from the `academy_name` list |
| **Pivot to B2B-first** | Retention OK but WTP low | Use the calibrated bank + data as the demo for academies/preparadores (the original research thesis) |
| **Rethink / stop** | W4 <10% and PMF <20% after fixing the top 3 feedback themes | Write up learnings, keep the SEO asset or sell it, stop spending |

Claude prepares a month-6 memo with the data behind each criterion.
