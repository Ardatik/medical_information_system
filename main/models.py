from django.db import models
import re
from django.core.exceptions import ValidationError
from datetime import datetime


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=12, unique=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.patronymic_name}"

    def get_full_name(self) -> str:
        return f"{self.last_name} {self.first_name} {self.patronymic_name}"

    def clean(self):
        super().clean()
        phone_regex = re.compile(r"^\+7\d{10}$")
        if self.phone_number and not phone_regex.match(
            self.phone_number.replace(" ", "")
        ):
            raise ValidationError(
                {"phone_number": "Телефон должен быть в формате +7XXXXXXXXXX"}
            )


class Doctor(Person):
    specialization = models.CharField(max_length=100)
    experience = models.IntegerField()

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"


class Patient(Person):
    date_of_birth = models.DateField()

    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"


class Admin(Person):
    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"


class Clinic(models.Model):
    name = models.CharField(max_length=100)
    registered_adress = models.CharField(max_length=150)
    actual_adress = models.CharField(max_length=150)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Клиника"
        verbose_name_plural = "Клиники"

    def __str__(self) -> str:
        return f"Клиника {self.name}, Юридический адрес: {self.registered_adress}, Фактический адрес: {self.actual_adress}"


class Consultation(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Подтверждена"),
        ("waited", "Ожидает"),
        ("started", "Начата"),
        ("completed", "Завершена"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="consultations")
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="consultations"
    )
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT, related_name="consultations")

    class Meta:
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"

    def clean(self):
        super().clean()
        if not self.start_time or not self.end_time:
            return
        if self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "Конец приема должен быть позже начала приема"}
            )
        if self.start_time < datetime.now(self.start_time.tzinfo):
            raise ValidationError(
                {"start_time": "Начало приема не может быть в прошлом"}
            )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
