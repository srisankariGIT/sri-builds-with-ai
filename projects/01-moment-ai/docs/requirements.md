# MOMent AI — Requirements Specification

**Product:** MOMent AI — your personal motherhood assistant
**Document version:** 0.1 (planning) · **Date:** 24 Nov 2026
**Related documents:** `user-stories.md`, `architecture.md`, `database-design.md`

**How to read this document.** Every requirement has an ID (for example `NLP-04`). The other three documents refer to these IDs, so you can trace any feature from idea → story → design → table.
Priorities use MoSCoW: **Must** (MVP fails without it), **Should** (build if on schedule), **Could** (only if time remains), **Won't** (deliberately not in the MVP).

---

## 1. Product summary

MOMent AI is a web app where a parent types a normal sentence such as *"Remind me to take Mia to the dentist next Tuesday at 4 pm"* and the app turns it into a structured reminder. Before anything is saved, the app shows what it understood and asks the parent to confirm. If something is missing or unclear (for example, no time was given), the app asks a short follow-up question instead of guessing silently.

Saved reminders can repeat (daily, weekly, monthly, yearly), belong to a family-oriented category (school, health, home, bills, birthdays…), and are delivered on time by email and as in-app notifications.

### Why this product exists
Parents carry a heavy "mental load": school forms, vaccinations, bills, birthdays, activity pick-ups. Typing a sentence is far faster than filling a form, and an assistant that double-checks before saving is more trustworthy than one that guesses.

### The one idea that shapes the whole design
> **The AI proposes. The user confirms. The server decides.**
> The language model never writes to the database. It only turns text into a *proposal*. Your Django code validates the proposal, the user confirms it, and only then is a reminder created. This keeps the product safe, testable and cheap to debug.

---

## 2. Goals and non-goals

### MVP goals
1. A parent can sign up and create a correct reminder from one sentence in under 30 seconds (including confirmation).
2. Reminders fire on time (within 90 seconds of the due time) and never fire twice.
3. Every reminder is created only after explicit user confirmation.
4. The whole MVP can be built, tested and demoed by one developer in seven days.

### Non-goals (MVP)
- Sharing reminders between several accounts (shared household). *Won't.*
- Mobile apps, push notifications, SMS, WhatsApp. *Won't.* (Email + in-app only.)
- Voice input. *Won't.*
- Calendar sync (Google/Apple/Outlook). *Won't.*
- Editing or deleting reminders through natural language ("move my dentist reminder to Friday"). *Won't.* (Create-by-sentence only; edit/delete use normal screens.)
- Snooze, per-occurrence exceptions in a recurring series, attachments. *Won't.*
- Languages other than English for natural-language input. *Won't.* (Design leaves room; see §12.)

---

## 3. Users

**Primary persona — "The busy parent".** Manages school, health, home and money tasks for a family. Mostly uses a phone browser, often one-handed, often interrupted. Not technical. Wants speed and confidence that nothing is forgotten.

**Not in MVP — "The co-parent / household member".** Someone who should see or share reminders. The data model leaves a clean path to add this later (see `database-design.md`, §9), but no sharing features are built now.

---

## 4. MVP scope at a glance

| Area | Must | Should | Could |
|---|---|---|---|
| Accounts | Register, login/logout, email verification, profile (timezone, notification preferences), delete account | Password reset | Data export |
| Assistant | Sentence → proposal, extraction, clarification, confirmation card with editing, off-topic handling, fallback to manual form, rate limits | Show "assumptions" on the card | Family-member name matching |
| Reminders | Create/list/view/edit/delete/mark complete, validation | Filters by category | Text search |
| Categories | Default family categories, custom categories | Family members (lightweight profiles) | — |
| Recurrence | None/daily/weekly/monthly/yearly, whole-series edit/delete | "Every N" interval, end date | — |
| Notifications | Scheduler, email, in-app list + unread badge, no duplicates, retries, late/missed policy | Per-channel preferences | — |

---

## 5. Functional requirements

### 5.1 Authentication and account (AUTH)

| ID | Requirement | Priority |
|---|---|---|
| AUTH-01 | A visitor can register with email, password, display name and timezone. The timezone is pre-filled from the browser and can be changed. Terms/Privacy acceptance is required and timestamped. | Must |
| AUTH-02 | A registered user can log in and log out. Sessions expire after 14 days. | Must |
| AUTH-03 | Email addresses are verified through a time-limited link (24 h). Email notifications are sent only to verified addresses. | Must |
| AUTH-04 | A user can reset a forgotten password via an emailed, single-use, time-limited link (1 h). | Should |
| AUTH-05 | A user can edit display name, timezone, and notification preferences. Changing timezone recalculates upcoming fire times. | Must |
| AUTH-06 | A user can permanently delete their account and all their data. | Must |
| AUTH-07 | A user can download their data as JSON. | Could |

### 5.2 Natural-language assistant (NLP)

| ID | Requirement | Priority |
|---|---|---|
| NLP-01 | The user can type a free-text request (1–500 characters) in an assistant box. | Must |
| NLP-02 | The system extracts: **task title**, optional **notes**, **date**, **time**, **category**, **recurrence** (type, interval, weekdays, end date) and, if enabled, **family member**. | Must |
| NLP-03 | Relative expressions ("tomorrow", "this Friday", "next Tuesday", "in 2 hours", "on the 5th") are resolved using the user's timezone and the server's current time. The resolved absolute date (with weekday name) is shown to the user. | Must |
| NLP-04 | If a required field (title, date, time) is missing or ambiguous, the assistant asks one short clarification question at a time, with up to 4 suggested answers. A maximum of 3 clarification rounds per request; after that, the manual form opens pre-filled with what is known. | Must |
| NLP-05 | **No reminder is created until the user presses Confirm.** The server enforces this; it is not only a UI rule. | Must |
| NLP-06 | On the confirmation card the user can edit every field before confirming, or cancel. | Must |
| NLP-07 | Requests that are not reminder requests (weather, jokes) or that try to manipulate the assistant receive a polite decline. No data is read or changed. | Must |
| NLP-08 | If the LLM service is slow (>15 s), failing, or returns an unusable answer twice, the user sees a friendly message and a one-click link to the manual form. The rest of the app keeps working. | Must |
| NLP-09 | Per-user limits: 10 assistant requests/minute and 100/day (configurable). | Must |
| NLP-10 | The confirmation card lists "assumptions" the assistant made (for example "I assumed 3:30 means 3:30 PM"). | Should |
| NLP-11 | If family members exist, the assistant can match names in the sentence to them. | Could |
| NLP-12 | Only one reminder per request. If the sentence contains several tasks, the assistant asks which to create first. | Must |

**Clarification rules (when to ask vs. when to assume).**

| Situation | Behaviour |
|---|---|
| No identifiable task ("remind me tomorrow") | Ask what to remind about. |
| Date missing and not inferable | Ask. |
| Time missing | Ask, offering likely choices. Exception: a time-of-day word is given — *morning* = 08:00, *afternoon* = 14:00, *evening* = 18:00, *night* = 21:00 — then assume and list it under assumptions. |
| 1–11 o'clock with no AM/PM | Infer only if context makes it obvious ("school pick-up at 3:30" → PM); flag as assumption. Otherwise ask. |
| Ambiguous numeric date ("12/11") | Always ask. |
| Date is in the past | Ask ("That time has passed — did you mean tomorrow?"). |
| Weekday name alone ("Friday") | The next such day in the future. |
| "next <weekday>" | That weekday in the following calendar week (Mon–Sun). The resolved date is displayed so the user can catch a different interpretation. |
| Category unclear | Choose the best match, or "Other"; never block on category. |
| Recurrence end not stated | Repeats forever; shown as an assumption. |
| Several tasks in one sentence | Ask which to create first (NLP-12). |

### 5.3 Reminders (REM)

| ID | Requirement | Priority |
|---|---|---|
| REM-01 | Create a reminder manually with: title, notes, date, time, category, recurrence. | Must |
| REM-02 | List reminders in two views — **Upcoming** (soonest first) and **Completed** — with a filter by category. Page size 25. | Must |
| REM-03 | View a reminder's details, including next occurrence and last time it fired. | Must |
| REM-04 | Edit any field. Editing a recurring reminder changes the whole series. | Must |
| REM-05 | Delete a reminder (permanent, with a confirmation dialog). | Must |
| REM-06 | Mark a reminder complete. For a recurring reminder this ends the series. | Must |
| REM-07 | Validation: title 1–120 chars; notes ≤ 500 chars; a one-time reminder must be at least 1 minute in the future; recurrence rules must be internally consistent (see database-design §4.4). | Must |
| REM-08 | Search reminders by text. | Could |

### 5.4 Categories and family (CAT)

| ID | Requirement | Priority |
|---|---|---|
| CAT-01 | At signup each user receives eight default categories: Kids & School, Health & Doctor, Home & Chores, Meals & Groceries, Bills & Money, Birthdays & Events, Personal, Other. | Must |
| CAT-02 | Users can add, rename, recolour and delete categories. Names are unique per user (case-insensitive), max 40 chars, max 30 categories. | Must |
| CAT-03 | Deleting a category does not delete reminders; they become "Uncategorized". | Must |
| CAT-04 | Users can keep a short list of family members (name + relation: child, partner, parent, other) and tag a reminder with one. Only first names/nicknames are stored — no birth dates. | Should |

### 5.5 Recurrence (REC)

| ID | Requirement | Priority |
|---|---|---|
| REC-01 | Supported types: none (one-time), daily, weekly (one or more weekdays), monthly (same day number), yearly (same month and day). | Must |
| REC-02 | "Every N" interval (for example every 2 weeks), N from 1 to 52. | Should |
| REC-03 | Optional end date. Default: never ends. | Should |
| REC-04 | A monthly reminder on day 29–31 fires on the last day of shorter months. A yearly reminder on 29 Feb fires on 28 Feb in non-leap years. | Must |
| REC-05 | Edits and deletion apply to the whole series. Per-occurrence exceptions are out of scope. | Must |
| REC-06 | After each firing, the system computes the next future occurrence. When the end date passes, the reminder becomes completed. | Must |

### 5.6 Notifications (NOT)

| ID | Requirement | Priority |
|---|---|---|
| NOT-01 | A background job checks for due reminders every minute. | Must |
| NOT-02 | When a reminder is due, an **email** is sent (to verified emails only) and an **in-app notification** is created. | Must |
| NOT-03 | The app shows a bell with an unread count (refreshed every 60 s while the tab is open) and a notification list with "mark as read" and "mark all as read". | Must |
| NOT-04 | **Exactly-once creation:** the same occurrence of the same reminder never produces two notifications, even if the scheduler runs twice or a worker restarts. | Must |
| NOT-05 | Failed emails retry up to 3 times (after 1, 5, then 15 minutes), then are marked failed. | Must |
| NOT-06 | **Late/missed policy:** if the system was down, overdue reminders still fire if they are ≤ 24 hours late; beyond that they are marked *skipped*. A recurring reminder that missed several occurrences sends at most one catch-up notification, then moves to the next future occurrence. | Must |
| NOT-07 | Users can switch email and in-app notifications on/off separately. | Should |
| NOT-08 | Notification text uses the reminder's title only (no notes) in email subject lines. | Must |

---

## 6. LLM behaviour requirements (LLM)

| ID | Requirement |
|---|---|
| LLM-01 | The model is called with **function calling** and must answer with exactly one of three functions: `propose_reminder`, `ask_clarification`, `decline_request`. Free-text answers are not accepted. |
| LLM-02 | The model has **no function that reads or writes stored data.** Its only inputs are the user's current sentence, the current conversation for this one draft, the current date/time, the user's timezone, and the names of the user's own categories (and family members). |
| LLM-03 | Every model output is validated by server-side code before being shown. An invalid proposal triggers one automatic retry with the validation error; a second failure triggers NLP-08. |
| LLM-04 | The model must not invent information. Missing facts → `ask_clarification`. |
| LLM-05 | Prompts and model responses are not written to application logs. Only metadata is logged (model, token counts, latency, outcome). |
| LLM-06 | The LLM provider is chosen so that API data is **not used to train models** and has a defined retention period. The provider sits behind a small internal interface so it can be swapped. |
| LLM-07 | **Quality targets**, measured on a fixed evaluation set of ≥ 40 phrases (seeded in `user-stories.md`, Appendix A): ≥ 90 % of unambiguous phrases produce all fields correctly with no clarification; ≥ 80 % of ambiguous phrases trigger a clarification instead of a guess; 100 % of manipulation attempts are declined; 0 reminders created without confirmation. |
| LLM-08 | Cost guard: input limited to 500 characters; at most 7 messages of history per draft; a small, fast model tier is used. Target cost ≤ US$0.01 per completed reminder (to be verified against current provider pricing). |

---

## 7. Non-functional requirements (NFR)

| ID | Requirement | Target |
|---|---|---|
| NFR-01 | Assistant response time (parse step) | p95 ≤ 6 s; hard timeout 15 s |
| NFR-02 | List/CRUD API response time with ≤ 500 reminders | p95 ≤ 300 ms |
| NFR-03 | Scheduler lateness (due time → notification created) | p95 ≤ 90 s |
| NFR-04 | Availability of the core app (excluding the LLM) | 99 % monthly for MVP |
| NFR-05 | Supported browsers | Last 2 versions of Chrome, Safari, Edge, Firefox; mobile Safari/Chrome |
| NFR-06 | Layout | Mobile-first responsive; usable at 360 px width |
| NFR-07 | Accessibility | Keyboard operable, visible focus, labelled form fields, colour contrast WCAG 2.1 AA for text |
| NFR-08 | Observability | Structured JSON logs with request ID; scheduler logs "N due, N sent, max lateness"; error tracking enabled |
| NFR-09 | Testability | Time is injectable (code never calls "now" directly in business logic); LLM is mockable; ≥ 80 % test coverage on recurrence, validation and permission code |
| NFR-10 | Capacity assumed for MVP | ≤ 1,000 users, ≤ 100 reminders each, ≤ 5 notifications/user/day |
| NFR-11 | Recoverability | Daily database backups with a tested restore; Redis is treated as disposable (no reminder is lost if Redis is wiped) |

---

## 8. Security requirements (SEC)

| ID | Requirement |
|---|---|
| SEC-01 | All traffic uses HTTPS. HSTS enabled in production. |
| SEC-02 | Passwords are hashed with a modern, salted algorithm (Django's hashers; Argon2 recommended). Minimum 10 characters; common/numeric-only passwords rejected. |
| SEC-03 | Browser sessions use `HttpOnly`, `Secure`, `SameSite=Lax` cookies. CSRF protection is enabled for all state-changing requests. |
| SEC-04 | **Object-level authorization on every endpoint:** a user can only read or change their own categories, family members, reminders, notifications and drafts. Another user's object ID returns 404 (not 403) so IDs cannot be probed. Covered by automated tests. |
| SEC-05 | Public identifiers are random UUIDs, never sequential integers. |
| SEC-06 | Login throttling: 5 failed attempts per account + IP within 15 minutes triggers a temporary lock. Registration and password-reset endpoints are throttled. |
| SEC-07 | The assistant is protected against prompt injection by design (LLM-01, LLM-02, LLM-03). User text is always treated as data, never as instructions to the application. |
| SEC-08 | All user-generated text (titles, notes, category names) is rendered as plain text in the UI and escaped in emails. No raw HTML rendering. |
| SEC-09 | Secrets (database URL, LLM key, email key, Django secret key) live in environment variables / a secrets manager. Never in the repository. `.env` is git-ignored. |
| SEC-10 | CORS is limited to the frontend origin; Django `DEBUG` is off in production; `ALLOWED_HOSTS` is set; security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy`) are enabled. |
| SEC-11 | Dependencies are pinned and scanned (for example `pip-audit`, `npm audit`, Dependabot) before release. |
| SEC-12 | Email-sending endpoints cannot be abused to email third parties: emails go only to the account's own verified address. |
| SEC-13 | Postgres and Redis are not exposed to the public internet; credentials are unique per environment; backups are encrypted. |
| SEC-14 | Basic audit logging for sensitive events (login success/failure, password reset, account deletion, email change) without logging passwords or message content. |

---

## 9. Data privacy requirements (PRV)

This product may store information about **children and health appointments**, which deserves extra care.

| ID | Requirement |
|---|---|
| PRV-01 | **Data minimisation.** Collect only: email, display name, timezone, reminders, categories, optional family first names. No birth dates, school names, photos, location or phone numbers in MVP. |
| PRV-02 | **Purpose limitation.** Data is used only to provide reminders. No advertising, no selling, no use for model training. |
| PRV-03 | **Transparency.** A plain-language privacy page states what is stored, that reminder text is sent to an LLM provider to be interpreted, who that provider is, and how long data is kept. Consent (terms + privacy) is recorded with a timestamp (AUTH-01). |
| PRV-04 | **Minimal LLM context.** Only the current sentence, current draft conversation, date/time, timezone and the user's category/family-member names are sent to the LLM. Never the email address, other reminders, or other users' data. |
| PRV-05 | **Retention.** Assistant drafts (which hold raw sentences) are deleted 7 days after creation. LLM call logs (metadata only) 90 days. Notifications 90 days after delivery. Completed reminders are kept until the user deletes them. |
| PRV-06 | **Right to deletion.** Account deletion removes all user data from the live database immediately and from backups within the backup retention window (≤ 30 days). |
| PRV-07 | **No sensitive data in logs or error reports.** Request bodies, reminder text and LLM prompts are scrubbed. |
| PRV-08 | **Children's data.** The account holder is the adult (parent/guardian). Children do not have accounts in MVP. Before public launch, review obligations for children's personal data in every market you serve (for example India's DPDP Act, GDPR, COPPA) with a qualified adviser. *(This document is not legal advice.)* |
| PRV-09 | **Vendor review.** Before launch, confirm the LLM, email and hosting providers' data-processing terms (retention, region, sub-processors) and record the choice. |

---

## 10. Assumptions, constraints and risks

### Assumptions
- One developer, about 7 working days, using AI-assisted coding.
- Reminder volume is small, so a once-a-minute database check is more than enough.
- English-only input for MVP.
- Users have a reachable email address; email is the primary "reach me when the app is closed" channel.

### Constraints
- Stack is fixed: Next.js, Django REST Framework, PostgreSQL, an LLM API with function calling, Celery + Redis.
- Only planning documents are produced now: no application code, no migrations.

### Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM misreads a date or time | Wrong reminder time → loss of trust | Server-side validation, resolved date shown with weekday, mandatory confirmation, editable card |
| LLM outage or slowness | Assistant unusable | Timeout, retry once, manual form always available |
| Duplicate or missed notifications | Core promise broken | Database as source of truth, row locking, unique constraint per occurrence, retry policy, late/missed rules |
| Timezone and recurrence bugs | Subtle wrong times | Store local date/time + user timezone, use `zoneinfo` and `dateutil` instead of hand-written calendar math, heavy unit tests |
| Scope creep (sharing, push, calendar) | Misses 7 days | Fixed "Won't" list and a pre-agreed cut order (§11) |
| Email lands in spam | Reminders missed | Use a transactional email provider; configure SPF/DKIM; in-app channel as backup |
| Children's data regulation | Legal exposure at launch | PRV-01 minimisation, PRV-08/09 review before public launch |

---

## 11. Seven-day delivery plan

The plan builds the reliable core first (accounts → reminders → scheduler) and adds the AI layer on top. If the AI layer is late, you still have a working reminder app.

| Day | Focus | Done when |
|---|---|---|
| **1** | Environment and accounts. Local Postgres + Redis, Django project with a **custom user model**, session auth, register/login/logout/profile API, Next.js skeleton with login/register pages and API proxy. | You can register and log in from the browser; cross-user access tests exist. |
| **2** | Categories and reminders API. Default-category seeding at signup, categories CRUD, reminders CRUD with validation, recurrence fields, `next_fire_at` calculation (unit-tested). | API tests pass, including "user A cannot see user B". |
| **3** | Reminders UI. Upcoming/Completed lists, create/edit form with recurrence, category management, mark complete, delete. | A parent can manage reminders without the AI. |
| **4** | Scheduler and notifications. Celery worker + beat, `dispatch_due_reminders`, notification rows, email sending (console backend locally), email verification, bell + notification list. | A reminder due in 2 minutes arrives once, on time, by email and in-app. |
| **5** | Assistant backend. LLM client interface, system prompt, three function schemas, validation layer, drafts table, clarification loop, rate limits, mock LLM for tests. | Evaluation script runs the 40-phrase set and prints a score. |
| **6** | Assistant UI. Assistant box, clarification chips, confirmation card with editing and assumptions, confirm/cancel, error/fallback states. | The full journey "sentence → question → confirm → reminder → notification" works end to end. |
| **7** | Hardening and release. Security checklist (§8), privacy page, retention cleanup job, README, backups, deploy to a staging environment, bug-fix buffer. | Exit criteria in §12 are met. |

**Cut order if you fall behind** (cut from the top): 1) family members (CAT-04, NLP-11) · 2) password reset (AUTH-04) · 3) data export (AUTH-07) · 4) every-N interval and end date (REC-02/03) · 5) per-channel notification preferences (NOT-07) · 6) category filter (REM-02 filter).
**Never cut:** confirmation before creation (NLP-05), object-level permissions (SEC-04), exactly-once notifications (NOT-04), manual fallback (NLP-08).

---

## 12. MVP exit criteria (Definition of Done)

1. Every **Must** requirement is implemented, and each user story's acceptance criteria pass (manually or by test).
2. Automated tests pass for: recurrence calculation, validation, permissions (cross-user access), scheduler idempotency, and assistant flow with a mocked LLM.
3. The LLM evaluation set meets LLM-07 targets (or the gaps are documented).
4. The SEC and PRV checklists are reviewed item by item.
5. A fresh clone can be set up from the README in under 30 minutes.
6. A 10-minute demo runs without manual database edits.

## 13. Open questions (decide early; none block Day 1)

1. **LLM provider and model tier** — which provider, and is a small model accurate enough on the evaluation set?
2. **Email provider** for transactional mail (verification, reminders).
3. **Hosting** for Next.js, Django, Celery worker + beat, Postgres and Redis.
4. **Launch market(s)** — affects privacy obligations (PRV-08).
5. **Future languages** (for example Tamil, Hindi) — the prompt and evaluation set would need extending; the architecture does not block it.
