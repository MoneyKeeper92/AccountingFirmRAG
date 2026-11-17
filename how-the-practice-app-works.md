# How the Maxwell practice app works

The live app is **https://practice.maxwellstudy.com**. This guide covers what a student sees, how the app decides what to show them, and how to set up a personal version for one student from their results.

It describes `main` as of Nov 17, 2026 (commit 979da9a).

---

## 1. The app in one paragraph

A student signs in with an email and lands on the practice app for their exam section. For FAR they pick a topic, such as Leases, and work its scenarios one at a time, easiest first. Each scenario is one question, answered in one shot. The answer can be a journal entry, a number, a multiple choice, tick boxes, a dropdown, an adjustment ladder or a bank reconciliation. After they answer, the worked solution opens under the question. At the end of a topic they get a short results page, then go back to the topic list.

On top of that standard app, there are three ways to personalize what one student sees. They're covered in section 6.

---

## 2. Signing in

There is no password. The student types an email, and the app takes their word for it.

- The email is never stored or sent anywhere as-is. The app turns it into a **slug**: the first 16 hex characters of the SHA-256 hash of the lowercased, trimmed email. Everything downstream is keyed by the slug: personal quizzes, picker history and Mixpanel identity. Code: `src/lib/student.js`.
- If the student filled in the Tally intake survey (Make writes it to Supabase through `netlify/functions/intake.js`), the app already knows their exam section and date, so they aren't asked again.
- The signed-in student is remembered in the browser (localStorage key `hub_student`). Sign out is on the topics page, not under every question.

To get a student's slug from their email:

```bash
node -e 'console.log(require("crypto").createHash("sha256").update(process.argv[1].trim().toLowerCase()).digest("hex").slice(0,16))' student@example.com
```

For testing, use the test slug `0000test0000test` or the bot's account. Never sign in as a real student.

---

## 3. Where a student lands

`src/App.js` and `src/FrontDoor.js` decide this, in this order:

| Who | Where they go |
|---|---|
| Anyone whose slug is in `personal-quizzes.json` | Their personal quiz, on every address. No topic list, no other apps. See 6A. |
| FAR student | `/far-practice-beta`, the FAR Practice App |
| AUD student | `/aud-practice-beta`, the AUD practice app |
| REG student | The assigned deck. The picker chooses a set of layered REG scenarios for them. See 6C. |

REG still uses the older layered app because no one-shot REG app exists yet. FAR and AUD stopped using it on Oct 1.

---

## 4. The FAR Practice App

### What the student sees

1. **Topic list.** It shows 24 FAR topics in your teaching order (your topic codes: Cash, Receivables, Inventory, and so on through the balance sheet), not alphabetically. A topic link like `?topic=Accounting for Leases` survives a refresh and can be sent to a student.
2. **One scenario at a time,** with a progress bar, the scenario ID and the question.
3. **Answering:**
   - Multiple choice grades as soon as they click a choice.
   - Typed answers (numbers, journal entries) have a Submit button.
   - Submitting with nothing entered means "show me." It opens the worked answer without marking them wrong.
   - The journal entry form has account-name autocomplete.
4. **Worked answer** opens under the question and scrolls into view, which matters on a phone.
5. **Results page** at the end of the topic. Each scenario shows ✓ Right, ✗ Not right or – Looked at the answer, plus a % right on the first try. Only the first attempt counts, so looking at the answer and then typing it in isn't scored as right. From there they can open any scenario again or go back to the topics.

### Where the scenarios live

428 scenarios across three files in `src/data/far-beta/`. The app joins them into one list (`src/topics/farbeta/sections/OneShot.js`).

| File | What's in it |
|---|---|
| `oneshot.json` | The original 144 authored scenarios |
| `legacy-topics.json` | The ten old topic apps (leases, bonds, inventory, receivables, cash flow...), converted to this format |
| `authored-new.json` | Scenarios written since |

Answer types across all 428: 155 numeric, 145 journal entry, 115 multiple choice, 7 tick boxes, 6 dropdown, plus ladders and bank reconciliations.

Every scenario has:
- `id`
- `num`, the number shown in the app, e.g. #721
- `module`, the topic it sits under
- `sectionCode`, your topic code, which sets the topic order
- `task`, the question
- `solution`, the answer key, typed by answer kind
- `explanation`, the worked answer

It can also have:
- `difficulty`
- `accept`, alternate account names that also count as right
- `accounts`, the account list for the autocomplete

### Easiest first

Within a topic, scenarios sort by:

1. `difficulty` (1 to 3, decimals allowed). Without one, a pick-an-answer question counts as 1 and a typed one as 2.
2. Then answer type: choices, then numbers, then entries.
3. Then `num`.

To move a scenario earlier or later, change its `difficulty`. That's how the lease classification questions sit at 0.9 and the residual value guarantees at 2.6 to 2.8.

### Other FAR versions (same questions, different front page)

These are unlisted: they don't show on the topic list, and students reach them only by a link you send.

| URL | What it is | Built for |
|---|---|---|
| `/far-blueprint` | Every FAR question filed under its AICPA blueprint task (Areas I, II and III, area tabs at the top, a code like II-B1 on each question). Link to one task with `?task=II-B1`. Mapping lives in `blueprint-area1/2/3.json`. | Kavitha, who studies the blueprint one task at a time |
| `/far-tbs-focus` | Only four topics: adjusting entries, bank rec, inventory rec and consolidation. Each comes with links to the course's own MCQs and simulations. Config in `focus-tbs.json`. | A tutoring student who needed the common TBS topics |
| `/far-journal-entries` | Only the journal entry scenarios, in random order | Entry drilling |

These are shared URLs, not tied to one student. Anyone with the link sees the same thing.

---

## 5. AUD and REG

**AUD** (`/aud-practice-beta`, `src/topics/audbeta/`) has the same one-question-at-a-time shape as FAR, but it tests the audit chain: account → assertion → risk → procedure → document → what to do when a procedure doesn't go to plan. Each question is tagged with which link of the chain it's testing. Data lives in `src/data/aud-beta/`.

**REG** (`/reg-practice`) still runs on the older layered format. The **picker** (`netlify/functions/pick-next.js`) hands the student a set of scenarios:

- **First set:** high-importance topics, medium-difficulty questions, one or two topics at a time.
- **After each set:** it ranks topics by importance × miss rate and builds the next set from the top.
- **Spaced review:** earlier misses come back around.

The full picker logic is in `docs/how-the-picker-works.md`.

---

## 6. Personalizing the app for one student

There are three levers. Which one you use depends on the student's exam and what you have from them.

| | A. Personal final review quiz | B. Custom version of the app | C. Seeding the picker |
|---|---|---|---|
| **Exams** | FAR | FAR | REG today (see the note in 6C) |
| **Tied to** | The student's slug | A URL you send them | The student's slug |
| **Built from** | Their weak topics, as weights | What you want them to focus on | Their course history or diagnostic results |
| **What they see** | 10-scenario quizzes, weakest topics most, then results, then a new 10 | A cut-down app (by blueprint task, or only a few topics) | Their first set is already aimed at their weak lectures |
| **Lives in** | `src/data/far-beta/personal-quizzes.json` | `src/topics/farbeta/*App.js` plus a config JSON | Supabase tables, written by scripts in `scripts/` |
| **Example** | Kennedy (Nov 14) | Kavitha, `/far-blueprint` | Isaac, Joe, Grace, Kavitha (Sept) |

---

### 6A. Personal final review quiz (FAR)

**What the student sees.** They sign in as usual. Instead of the topic list, they get **"Your FAR final review quiz"**:

- 10 scenarios, sorted easiest first
- then a results page
- then a **Start new quiz** button that draws the next 10

They never see the topic list. If they reload mid-quiz, they pick up where they were.

**How each quiz is drawn** (`src/lib/personalQuiz.js`):

1. **Topics.** Each topic has a weight. A topic with weight 3 gets three times the slots of a weight-1 topic. Slots are rounded so they always total 10.
2. **Scenarios within a topic,** in this order:
   1. ones they got wrong, or only looked at, on an earlier quiz
   2. ones they haven't seen
   3. ones they just missed on the quiz they just finished (held back one round, so a new quiz isn't a repeat)
   4. ones they got right
3. **Topics that open later.** A topic can carry a `from` date, and it stays out of the draw until that day. This is how a quiz follows a study plan: Cash Flows joins on the day the plan teaches it.
4. **Topics that run out.** If a topic has fewer scenarios than its share, the spare slots go to the other topics.

Quiz history is kept **in the student's browser**. The server keeps no record of answers. If they switch phones or clear their browser, the quiz still works; the next draw is just less targeted.

**How to set one up, from a student's results:**

1. **Find their weak topics.** Use whatever you have:
   - their study plan
   - a course history export
   - a diagnostic
   - their score report

   For Kennedy, it was her Nov 14 study plan PDF, which listed her weakest topics first.
2. **Turn them into weights.** Use 3 for the weakest, 2 for the next tier and 1 for topics to keep warm. If the plan teaches a topic later, give it a `from` date so it doesn't appear before she has studied it.
3. **Match the topic names exactly** to FAR module names. The list is in section 8. A topic that doesn't exist in the app can't be covered. For example, there's no Conceptual Framework module.
4. **Get the slug** from their email with the command in section 2.
5. **Add an entry** to `src/data/far-beta/personal-quizzes.json`. Kennedy's, for example:

```json
"6b48167af89caa10": {
  "title": "Your FAR final review quiz",
  "plan": "FAR study plan Nov 14 to Dec 1: weakest first (Payables, Investments), then ...",
  "size": 10,
  "topics": [
    { "module": "Accounting for Payables and Notes Payable", "weight": 3 },
    { "module": "Accounting for Investments", "weight": 3 },
    { "module": "Accounting for Inventory", "weight": 2 },
    { "module": "Accounting for Cash", "weight": 2 },
    { "module": "Cash to Accrual Adjustments", "weight": 2 },
    { "module": "Revenue Recognition", "weight": 2 },
    { "module": "Accounting for Equity", "weight": 1 },
    { "module": "Earnings Per Share", "weight": 1 },
    { "module": "Cash Flow Statement", "weight": 1, "from": "2026-11-19" },
    { "module": "Consolidation Method", "weight": 1, "from": "2026-11-20" },
    { "module": "Eliminating Entries", "weight": 1, "from": "2026-11-21" }
  ]
}
```

   `plan` is a note for you. The student never sees it. `size` defaults to 10.
6. **Push to main.** Netlify deploys in a minute or two. The next time they open the app, they get the quiz.
7. **After the exam, delete the entry.** They go back to the normal FAR app.

The email never goes in the file, only the slug.

---

### 6B. A custom version of the app (FAR)

Build this when a student needs the app cut a particular way, rather than weighted toward weak topics.

- **By blueprint** (`/far-blueprint`): for a student who studies from the AICPA blueprint. Every question shows its task code. You send links to the exact tasks they're weak on, e.g. `practice.maxwellstudy.com/far-blueprint?task=II-B1`.
- **A few topics with course links** (`/far-tbs-focus`): for a student who should only work certain topics. `focus-tbs.json` lists each topic's scenarios and the course quiz and simulation links that go with it.

To make another one like the TBS focus app:

1. Copy `focus-tbs.json` with different topics and scenarios.
2. Add a three-line `*App.js` that passes it to `OneShot`.
3. Register it in `src/topicApps.js`, and in `src/topics.js` with `unlisted: true`.

These are links, not logins. Anyone with the URL sees the same version.

---

### 6C. Seeding the picker with course history (REG today)

This is the older system, built in September for Isaac, Joe, Grace, Kavitha and others. You load a student's results before their first sign-in, so the picker skips the discovery sets and their first set already targets their weak lectures. Full design: `docs/two-student-paths.md`.

**Important:** since Oct 1, FAR and AUD students land on the one-shot betas, which don't use the picker. So a seed, focus pin or study plan only changes what a **REG** student sees today. To personalize for a FAR student now, use 6A or 6B.

**From a Maxwell course history export** (`student_exams_history.xlsx`):

1. In Question Tagging, build the student's practice feed JSON from the export. It matches each course question code to its app scenario.
2. Run the import. `--dry-run` first shows what it would write:

```bash
node scripts/import-course-history.cjs --email=<their email> --file=<name>_practice_feed.json --dry-run
```

**From a blueprint diagnostic** (misses per blueprint topic):

1. Write a profile in `students/<name>.json`. It holds:
   - exam and exam date
   - the source of the results
   - per content group: how many they attempted and how many they got wrong per blueprint topic (`students/kavitha.json` is the example)
2. Generate the SQL:

```bash
node scripts/seed-student.cjs students/<name>.json --out=students/<name>-seed.sql
```

   The script spreads the misses across easy, medium and hard questions (not just the hardest), and puts application questions before recall.
3. Read the SQL, then run it in Supabase.

Both routes write to the `course_history_items` table. On the student's first sign-in, the picker ranks lectures from it (importance × miss rate) and builds the first set from the top. Once they start answering, their in-app results overlay the seed:
- getting a scenario right retires it
- missing one keeps it in rotation

**Two related levers on the same picker:**

| Lever | Set in | Use it for | How it works |
|---|---|---|---|
| **Focus pin** | `students.focus_lectures`, `focus_until`, `focus_note` | "This week, only what we covered in tutoring" | One set of lectures until a date. See `docs/topic-focus.md`. |
| **Study plan windows** | `student_focus_windows`, from a plan file like `students/joe-plan.json` | Making the app follow a day-by-day written plan | Each day or date range names its lectures. A day with no window opens the whole section, and spaced review of earlier days still comes through. Windows override the flat pin. See `docs/study-plan-focus.md`. |

---

### 6D. Not the practice app: final review quizzes on the course site

The **"Final Review Material"** emails send custom quizzes too (Review Quiz 1 and 2, built from a student's most important misses). Those are built on **coursemaxwellcpareview.com**, not in this app. The `maxwell-final-review-email` skill runs that workflow.

A student in final review can have both:
- the course quizzes from the email
- a personal practice app quiz (6A) built from the same weak topics

---

## 7. Changing scenarios

1. Edit the scenario in its JSON file.
   - `legacy-topics.json` and `authored-new.json` are saved with 2-space indent and a trailing newline.
   - A new scenario needs a unique `id` and `num`, its `module` and `sectionCode`, and a blueprint task in the right `blueprint-area*.json`. Otherwise it won't appear in `/far-blueprint`.
2. Rebuild the journal entry index:

```bash
node scripts/build-far-journal-entries.cjs
```

3. Run the tests:

```bash
CI=true npx react-scripts test --watchAll=false
```

4. Run the answer bot against a local copy. It signs in with its own test account, answers every scenario in the topic in a real browser, and reports any it couldn't get right. See `docs/the-bot.md`.

```bash
node scripts/beta-browser-bot.cjs --url http://localhost:3049 --module "Accounting for Leases"
```

5. Push to `main`. Netlify deploys automatically.
   - A student with the app already open may see the old version until they reload.
   - Old deploy-preview links stay frozen at their PR. Always test at practice.maxwellstudy.com.

**House rules for scenarios** (from your reviews):
- Each scenario stands alone.
- Easiest first.
- Numbers you can do in your head: test the concept, not the arithmetic.
- The question names everything the entry records ("record the payment and amortization").
- Give only the figures needed.
- A yes/no per row is tick boxes.
- Never a multiple choice whose choices are journal entries.
- Leases are lessee only.
- Repetition with different numbers is the point, so don't cut drills just for being similar.

---

## 8. Reference

**FAR topic names** (use these exactly in a personal quiz). Count of scenarios in brackets:

| Topic | Scenarios |
|---|---|
| Accounting for Cash | 13 |
| Accounting for Accounts Receivable | 25 |
| Accounting for Inventory | 26 |
| Accounting for Investments | 17 |
| Accounting for Fixed Assets | 28 |
| Accounting for Payables and Notes Payable | 19 |
| Accounting for Leases | 30 |
| Accounting for Bonds | 26 |
| Accounting for Equity | 20 |
| Other Comprehensive Income | 2 |
| Consolidation Method | 20 |
| Eliminating Entries | 14 |
| Cash Flow Statement | 25 |
| Cash to Accrual Adjustments | 16 |
| Earnings Per Share | 12 |
| Accounting for Income Taxes | 12 |
| Revenue Recognition | 16 |
| Accounting Changes | 14 |
| Subsequent Events and Contingencies | 16 |
| Not-for-Profit Accounting | 19 |
| Ratio Analysis | 31 |
| Adjusting Journal Entries | 4 |
| Intro to Financial Statements | 3 |
| Prepaids and Accruals | 20 |

**Where things live:**

| What | Where |
|---|---|
| Routing, personal quiz check | `src/App.js`, `src/FrontDoor.js` |
| Sign-in and slug | `src/lib/student.js` |
| FAR app (all versions) | `src/topics/farbeta/sections/OneShot.js` |
| FAR scenarios | `src/data/far-beta/oneshot.json`, `legacy-topics.json`, `authored-new.json` |
| Blueprint mapping | `src/data/far-beta/blueprint-area1.json`, `-area2`, `-area3` |
| Personal quizzes | `src/data/far-beta/personal-quizzes.json`, `src/lib/personalQuiz.js` |
| AUD app | `src/topics/audbeta/`, `src/data/aud-beta/` |
| Picker (REG) | `netlify/functions/pick-next.js`, `docs/how-the-picker-works.md` |
| Seeding scripts | `scripts/import-course-history.cjs`, `scripts/seed-student.cjs`, profiles in `students/` |
| Analytics | Mixpanel, identified by slug, never email. See `docs/mixpanel-in-the-practice-app.md`. |

**Privacy:**
- Never put a student's email in the app's code or data files. Use the slug.
- Mixpanel identifies students by slug only.
- Personal quiz entries are slug-only for the same reason.
