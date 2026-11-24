# Employee REST API (Django + DRF + SQLite)

Works on Python 3.9+ (Django 4.2 LTS). Inside the activated venv, `python` works as well as `python3`.

> **Security warning:** this API has NO authentication or permissions yet.
> Anyone who can reach it can read, change and delete salary data.
> Run it locally only. Add authentication and permissions before exposing it anywhere.

## Run it
```bash
python3 -m venv venv            # Windows: python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Then open http://127.0.0.1:8000/api/employees/ (the bare `/` address is intentionally a 404).

## Endpoints
| Method | URL | Purpose | Success |
|---|---|---|---|
| GET    | /api/employees/        | List all employees | 200 |
| POST   | /api/employees/        | Add an employee | 201 |
| GET    | /api/employees/<id>/   | Retrieve one employee | 200 |
| PUT    | /api/employees/<id>/   | Full update (all 4 fields required) | 200 |
| PATCH  | /api/employees/<id>/   | Partial update (any subset of fields) | 200 |
| DELETE | /api/employees/<id>/   | Delete an employee (hard delete, permanent) | 204 |

Fields: `name`, `email` (unique, case-insensitive, stored lowercase), `designation`, `salary` (> 0, max 2 decimals).
`id` and `created_at` are read-only.

## curl examples
```bash
# Create
curl -X POST http://127.0.0.1:8000/api/employees/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Priya Raman","email":"priya@example.com","designation":"Backend Developer","salary":"75000.00"}'

# List
curl http://127.0.0.1:8000/api/employees/

# Retrieve one
curl http://127.0.0.1:8000/api/employees/1/

# Full update (PUT): every editable field is required
curl -X PUT http://127.0.0.1:8000/api/employees/1/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Priya Raman","email":"priya@example.com","designation":"Senior Developer","salary":"90000.00"}'

# Partial update (PATCH): send only what changes
curl -X PATCH http://127.0.0.1:8000/api/employees/1/ \
  -H "Content-Type: application/json" \
  -d '{"salary":"95000.00"}'

# Delete (returns 204 with an empty body)
curl -i -X DELETE http://127.0.0.1:8000/api/employees/1/
```

## Error responses
| Case | Status | Example body |
|---|---|---|
| Employee does not exist (GET/PUT/PATCH/DELETE) | 404 | `{"detail": "No Employee matches the given query."}` |
| Invalid email | 400 | `{"email": ["Enter a valid email address, e.g. name@example.com."]}` |
| Email already used by another employee | 400 | `{"email": ["An employee with this email already exists."]}` |
| Negative or zero salary | 400 | `{"salary": ["Salary must be greater than zero."]}` |
| PUT with missing fields | 400 | `{"email": ["Email is required."], ...}` |

An employee can be saved with their own unchanged email; only another employee's email is rejected.

## Tests
```bash
python manage.py test
```

## Structure
- `config/` - project settings and root URLs
- `employees/models.py` - Employee table
- `employees/serializers.py` - validation and JSON conversion (used by every endpoint)
- `employees/views.py` - list/create view and retrieve/update/delete view
- `employees/urls.py` - app routes
- `employees/tests.py` - automated tests

## Known limitations
- No authentication or permissions (planned as a separate task).
- Hard delete: deleted employees cannot be recovered.
- No pagination, filtering or search on the list endpoint.
- SQLite is for learning only; use PostgreSQL or MySQL for real deployments.
