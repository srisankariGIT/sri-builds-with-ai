from decimal import Decimal

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=Employee.objects.all(),
                lookup="iexact",  # Ali@x.com and ali@x.com count as the same
                message="An employee with this email already exists.",
            )
        ],
        error_messages={
            "invalid": "Enter a valid email address, e.g. name@example.com.",
            "required": "Email is required.",
            "blank": "Email cannot be blank.",
        },
    )

    salary = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        error_messages={
            "required": "Salary is required.",
            "invalid": "Salary must be a valid number.",
            "min_value": "Salary must be greater than zero.",
            "max_digits": "Salary is too large (max 10 digits in total).",
            "max_decimal_places": "Salary can have at most 2 decimal places.",
        },
    )

    class Meta:
        model = Employee
        fields = ["id", "name", "email", "designation", "salary", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "name": {"error_messages": {"required": "Name is required.",
                                        "blank": "Name cannot be blank."}},
            "designation": {"error_messages": {"required": "Designation is required.",
                                               "blank": "Designation cannot be blank."}},
        }

    # DRF calls validate_<fieldname> automatically.
    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value

    def validate_email(self, value):
        return value.lower()  # store emails in a consistent format
