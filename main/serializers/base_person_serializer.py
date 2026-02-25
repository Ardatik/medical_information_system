import datetime
from rest_framework import serializers
from main.models import Doctor, Patient, Admin
import re


class PersonSerializer(serializers.ModelSerializer):
    sex_display = serializers.CharField(source="get_sex_display", read_only=True)

    class Meta:
        fields = [
            "id",
            "first_name",
            "last_name",
            "patronymic_name",
            "date_birth",
            "sex",
            "sex_display",
            "age",
            "email",
            "phone_number",
        ]
        read_only_fields = ["id", "age"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate_phone_number(self, value):
        phone = value.replace(" ", "")
        if not re.match(r"^\+7\d{10}$", phone):
            raise serializers.ValidationError(
                "Телефон должен быть в формате +7XXXXXXXXXX"
            )
        instance = self.instance
        instance_id = instance.id if instance else None
        if (
            Patient.all_objects.filter(phone_number=phone)
            .exclude(id=instance_id)
            .exists()
        ):
            raise serializers.ValidationError(
                "Пользователь с таким номером телефона уже существует"
            )
        if (
            Doctor.all_objects.filter(phone_number=phone)
            .exclude(id=instance_id)
            .exists()
        ):
            raise serializers.ValidationError(
                "Пользователь с таким номером телефона уже существует"
            )
        if (
            Admin.all_objects.filter(phone_number=phone)
            .exclude(id=instance_id)
            .exists()
        ):
            raise serializers.ValidationError(
                "Пользователь с таким номером телефона уже существует"
            )
        return phone

    def validate_date_birth(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("Дата рождения не может быть в будущем")
        if value.year < 1900:
            raise serializers.ValidationError(
                "Дата рождения не может быть раньше 1900 года"
            )
        return value

    def validate_email(self, value):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise serializers.ValidationError(
                "Email должен быть в формате example@example.com"
            )
        instance = self.instance
        instance_id = instance.id if instance else None
        if Patient.all_objects.filter(email=value).exclude(id=instance_id).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        if Doctor.all_objects.filter(email=value).exclude(id=instance_id).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        if Admin.all_objects.filter(email=value).exclude(id=instance_id).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует"
            )
        return value

    def validate_password(self, value):
        errors = []
        if len(value) < 8:
            errors.append("Пароль должен быть не менее 8 символов")
        if not any(char.isdigit() for char in value):
            errors.append("Пароль должен содержать хотя бы одну цифру")
        if not any(char.isupper() for char in value):
            errors.append("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(char.islower() for char in value):
            errors.append("Пароль должен содержать хотя бы одну строчную букву")
        if errors:
            raise serializers.ValidationError(errors)
        return value
