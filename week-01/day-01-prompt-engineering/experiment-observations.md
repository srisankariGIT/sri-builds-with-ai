# Experiment Observations

> Draft based on what happened during this session. Edit it into your own words.

## Setup
- Task: Employee REST API (Django + DRF + SQLite)
- Compared: a vague one-line prompt vs structured prompts (see the prompt files)

## What the structured prompt produced
- Architecture explanation first, then code, then API test examples, in the order requested
- Model, serializer, views, URLs, validation and tests in one pass
- Beginner-friendly explanations of each layer

## What went wrong, and what it taught me

### 1. Version pin that did not match my machine
The generated `requirements.txt` pinned Django 6.1.3, but my Mac has Python 3.9.6, which
cannot install it. `pip` only showed versions up to 4.2.
- **Fix:** relaxed the pins to Django 4.2 LTS (`Django>=4.2,<5.0`) and retested.
- **Lesson:** state my environment (OS, Python version) in the prompt.

### 2. A claim in the explanation was wrong until tested
The first explanation said a negative salary would return the custom message
"Salary must be greater than zero." Running the code showed the model's built-in validator
fired first with a generic message.
- **Fix:** defined the salary field explicitly in the serializer with custom messages,
  and added tests for it.
- **Lesson:** never trust AI explanations without running the code. Tests caught this.

### 3. Missing setting caused a migration mismatch
Switching Django versions exposed a missing `DEFAULT_AUTO_FIELD` setting.
- **Fix:** set it explicitly in `settings.py`.
- **Lesson:** run `check` and `makemigrations --check` after changing versions.

### 4. A 404 at the root URL was expected
`http://127.0.0.1:8000/` returned 404 because only `/api/employees/` and `/admin/` exist.
- **Lesson:** read the 404 page; Django lists the valid routes.

## What worked well
- **Plan, then approve:** asking for a plan before any file changes let me make decisions
  (hard delete, authentication later, README update) before code was written.
- **"Do not rewrite working functionality":** the CRUD step changed only 3 files
  and left the model and serializer alone.
- **Tests as a safety net:** 8 tests became 27 and all passed after the CRUD change.

## Results
| Metric | Value |
|---|---|
| Endpoints | 6 (list, create, retrieve, PUT, PATCH, DELETE) |
| Automated tests | 27, all passing |
| Files modified for CRUD | `views.py`, `urls.py`, `tests.py`, plus README |
| Known limitation | No authentication; hard delete; no pagination |

## Weak vs structured (fill in after running the weak prompt)
| Criteria | Weak prompt | Structured prompt |
|---|---|---|
| Followed my intended fields | _?_ | Yes |
| Validation and error messages | _?_ | Yes |
| Automated tests | _?_ | Yes (27) |
| Beginner-friendly explanation | _?_ | Yes |
| Needed follow-up fixes | _?_ | 3 (all environment or testing related) |

## Next steps
- Add authentication and permissions (token or session auth, `IsAuthenticated`)
- Add pagination and filtering
- Run the weak prompt in a fresh chat and complete the comparison table
