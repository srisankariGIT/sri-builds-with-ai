from rest_framework import generics

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/employees/  -> list all employees
    POST /api/employees/  -> create a new employee
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class EmployeeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/employees/<id>/  -> retrieve one employee
    PUT    /api/employees/<id>/  -> full update (all editable fields required)
    PATCH  /api/employees/<id>/  -> partial update (any subset of fields)
    DELETE /api/employees/<id>/  -> delete the employee (hard delete)
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
