# Structured Prompts (what I actually used)

## Prompt 1 - Build the API

```text
Act as a senior Python Django developer.

I want to build a REST API for managing
employee information.

Technology:
- Python
- Django
- Django REST Framework
- SQLite for this experiment

Requirements:
1. Create an Employee model.
2. Fields: name, email, designation and salary.
3. Create an API to add an employee.
4. Create an API to list all employees.
5. Add email validation.
6. Handle invalid input with meaningful errors.
7. Explain the project structure.

Work step by step.
First explain the architecture.
Then generate the code.
Finally provide API test examples.

Keep the explanation beginner-friendly.
```

## Prompt 2 - Add full CRUD (plan first, then approve)

```text
Act as a senior Django REST Framework developer.

My Employee REST API currently supports:
- GET /api/employees/
- POST /api/employees/

I want to implement complete CRUD functionality.

Requirements:
1. GET /api/employees/<id>/ to retrieve a single employee.
2. PUT /api/employees/<id>/ to update all editable employee fields.
3. PATCH /api/employees/<id>/ to partially update employee details.
4. DELETE /api/employees/<id>/ to delete an employee.

Instructions:
- First inspect the existing project structure.
- Reuse the existing Employee model and serializer.
- Follow Django REST Framework best practices.
- Do not rewrite working functionality.
- Handle employee records that do not exist.
- Preserve existing validation.
- Add automated tests for all new operations.
- Explain every file you modify.

First explain your implementation plan. Wait for my approval before modifying files.
```

## Prompt 3 - Approval with decisions

```text
Approved! Proceed using these decisions:
1. Use hard delete for this learning project.
2. Keep authentication as a separate follow-up task.
3. Update the README with all CRUD endpoints and curl examples.

Preserve existing functionality, avoid unnecessary changes, run the complete
test suite, explain the changes per file, and share test results and limitations.
```

## Techniques used
| Technique | Where |
|---|---|
| Role assignment | "Act as a senior ... developer" |
| Explicit tech stack | Python, Django, DRF, SQLite |
| Numbered requirements | Both prompts |
| Ordered workflow | Architecture, then code, then tests |
| Audience setting | "beginner-friendly" |
| Plan-then-approve gate | Prompt 2 |
| Constraints | "Do not rewrite working functionality" |
| Decisions made explicit | Prompt 3 |
