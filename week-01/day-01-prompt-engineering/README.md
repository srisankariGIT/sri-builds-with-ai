# Day 01 - Prompt Engineering: Employee REST API

**Goal:** see how prompt structure changes the quality of AI-generated code, using one task:
a Django REST Framework API for managing employees.

## What was built
A REST API (Python, Django, Django REST Framework, SQLite) with full CRUD:

| Method | URL | Purpose |
|---|---|---|
| GET | /api/employees/ | List all employees |
| POST | /api/employees/ | Add an employee |
| GET | /api/employees/<id>/ | Retrieve one employee |
| PUT | /api/employees/<id>/ | Full update |
| PATCH | /api/employees/<id>/ | Partial update |
| DELETE | /api/employees/<id>/ | Delete (hard delete) |

Features: email validation, unique email (case-insensitive), friendly error messages,
404 handling, and 27 automated tests.

## Contents
| File | What it is |
|---|---|
| [weak-prompt.md](weak-prompt.md) | A vague one-line prompt (baseline) |
| [structured-prompt.md](structured-prompt.md) | The structured prompts actually used |
| [experiment-observations.md](experiment-observations.md) | What I observed and learned |
| [screenshots/](screenshots/) | API calls and test results |
| [employee-api-project/](employee-api-project/) | The runnable Django project |

## Run the project
```bash
cd employee-api-project
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py test           # 27 tests should pass
python manage.py migrate
python manage.py runserver
```
Open http://127.0.0.1:8000/api/employees/ (the bare `/` address is intentionally a 404).

## Screenshots
Generated from real command output captured while running the project
(curl against the dev server, and the Django test runner). Replace them with your own
browser or terminal screenshots if you prefer.

| Screenshot | Shows |
|---|---|
| `api-get.png` | Listing employees |
| `api-post-success.png` | Creating an employee (201) |
| `api-duplicate-email.png` | Duplicate email rejected (400) |
| `api-update.png` | PATCH update (200) |
| `api-delete.png` | DELETE (204), then 404 on re-fetch |
| `test-results.png` | All 27 tests passing |

## Security note
The API has **no authentication**. Run it locally only. Authentication and permissions
are planned as a separate follow-up.
