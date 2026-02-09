from django.db import models
import re
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=12, unique=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.get_full_name()

    def get_full_name(self) -> str:
        if self.patronymic_name:
            return f"{self.last_name} {self.first_name} {self.patronymic_name}"
        return f"{self.last_name} {self.first_name}"

    def clean(self):
        super().clean()
        if self.phone_number:
            phone = self.phone_number.replace(" ", "")
            phone_regex = re.compile(r"^\+7\d{10}$")
            if not phone_regex.match(phone):
                raise ValidationError(
                    {"phone_number": "Телефон должен быть в формате +7XXXXXXXXXX"}
                )
            self.phone_number = phone


class Doctor(Person):
    specialization = models.CharField(max_length=100)
    experience = models.PositiveIntegerField()

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctors = models.ManyToManyField(
        Doctor,
        related_name="clinics"
    )
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
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Подтверждена"
        WAITED = "waited", "Ожидает"
        STARTED = "started", "Начата"
        COMPLETED = "completed", "Завершена"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status, default="waited")
    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="consultations"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="consultations"
    )
    clinic = models.ForeignKey(
        Clinic, on_delete=models.PROTECT, related_name="consultations"
    )

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
        if self.start_time < timezone.now():
            raise ValidationError(
                {"start_time": "Начало приема не может быть в прошлом"}
            )
        overlapping = Consultation.objects.filter(
            doctor=self.doctor,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("У врача уже есть консультация в это время")
        if self.clinic and self.doctor:
            if not self.clinic.doctors.filter(id=self.doctor.id).exists():
                raise ValidationError("Этот врач не работает в выбранной клинике")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
