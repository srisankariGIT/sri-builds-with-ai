from rest_framework import status
from rest_framework.test import APITestCase

from .models import Employee

URL = "/api/employees/"
VALID = {"name": "Priya Raman", "email": "priya@example.com",
         "designation": "Backend Developer", "salary": "75000.00"}


class EmployeeAPITests(APITestCase):
    def test_create_employee(self):
        res = self.client.post(URL, VALID, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 1)

    def test_list_employees(self):
        self.client.post(URL, VALID, format="json")
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_invalid_email(self):
        res = self.client.post(URL, {**VALID, "email": "bad"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_duplicate_email_case_insensitive(self):
        self.client.post(URL, VALID, format="json")
        res = self.client.post(URL, {**VALID, "email": "PRIYA@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_salary(self):
        res = self.client.post(URL, {**VALID, "salary": "-5"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("salary", res.data)

    def test_missing_fields(self):
        res = self.client.post(URL, {"name": "Arun"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("email", "designation", "salary"):
            self.assertIn(field, res.data)

    def test_negative_salary_message(self):
        res = self.client.post(URL, {**VALID, "salary": "-5"}, format="json")
        self.assertEqual(res.data["salary"][0], "Salary must be greater than zero.")

    def test_non_numeric_salary(self):
        res = self.client.post(URL, {**VALID, "salary": "abc"}, format="json")
        self.assertEqual(res.data["salary"][0], "Salary must be a valid number.")


def detail_url(pk):
    return f"/api/employees/{pk}/"


class EmployeeDetailAPITests(APITestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            name="Priya Raman", email="priya@example.com",
            designation="Backend Developer", salary="75000.00",
        )
        self.other = Employee.objects.create(
            name="Arun Kumar", email="arun@example.com",
            designation="QA Engineer", salary="50000.00",
        )
        self.url = detail_url(self.emp.pk)
        self.missing = detail_url(99999)
        self.full = {"name": "Priya R", "email": "priya.r@example.com",
                     "designation": "Senior Developer", "salary": "90000.00"}

    # ---- Retrieve ----
    def test_retrieve_employee(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.emp.pk)
        self.assertEqual(res.data["email"], "priya@example.com")

    def test_retrieve_missing_employee_returns_404(self):
        res = self.client.get(self.missing)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", res.data)

    def test_non_numeric_id_returns_404(self):
        res = self.client.get("/api/employees/abc/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ---- PUT ----
    def test_put_updates_all_fields(self):
        res = self.client.put(self.url, self.full, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.name, "Priya R")
        self.assertEqual(self.emp.email, "priya.r@example.com")
        self.assertEqual(self.emp.designation, "Senior Developer")
        self.assertEqual(str(self.emp.salary), "90000.00")

    def test_put_missing_fields_returns_400(self):
        res = self.client.put(self.url, {"name": "Only Name"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("email", "designation", "salary"):
            self.assertIn(field, res.data)

    def test_put_invalid_email_returns_400(self):
        res = self.client.put(self.url, {**self.full, "email": "bad"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_put_keeping_own_email_is_allowed(self):
        res = self.client.put(self.url, {**self.full, "email": "priya@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_put_duplicate_email_of_other_employee_returns_400(self):
        res = self.client.put(self.url, {**self.full, "email": "ARUN@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["email"][0], "An employee with this email already exists.")

    def test_put_missing_employee_returns_404(self):
        res = self.client.put(self.missing, self.full, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_ignores_read_only_id(self):
        original_id = self.emp.pk
        res = self.client.put(self.url, {**self.full, "id": 12345}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], original_id)
        self.assertTrue(Employee.objects.filter(pk=original_id).exists())
        self.assertFalse(Employee.objects.filter(pk=12345).exists())

    # ---- PATCH ----
    def test_patch_updates_only_given_fields(self):
        res = self.client.patch(self.url, {"salary": "80000.00"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.emp.refresh_from_db()
        self.assertEqual(str(self.emp.salary), "80000.00")
        self.assertEqual(self.emp.name, "Priya Raman")
        self.assertEqual(self.emp.email, "priya@example.com")
        self.assertEqual(self.emp.designation, "Backend Developer")

    def test_patch_negative_salary_returns_friendly_400(self):
        res = self.client.patch(self.url, {"salary": "-5"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data["salary"][0], "Salary must be greater than zero.")

    def test_patch_invalid_email_returns_400(self):
        res = self.client.patch(self.url, {"email": "nope"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_patch_duplicate_email_case_insensitive_returns_400(self):
        res = self.client.patch(self.url, {"email": "Arun@Example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_patch_email_is_normalised_to_lowercase(self):
        res = self.client.patch(self.url, {"email": "New.Mail@Example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "new.mail@example.com")

    def test_patch_missing_employee_returns_404(self):
        res = self.client.patch(self.missing, {"salary": "1000"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ---- DELETE ----
    def test_delete_employee(self):
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(pk=self.emp.pk).exists())
        self.assertTrue(Employee.objects.filter(pk=self.other.pk).exists())

    def test_delete_twice_returns_404_second_time(self):
        self.client.delete(self.url)
        res = self.client.delete(self.url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_missing_employee_returns_404(self):
        res = self.client.delete(self.missing)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
