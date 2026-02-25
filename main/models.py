from django.db import models
import re
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from .manager import ActiveManager


class Person(models.Model):
    class SexChoices(models.TextChoices):
        MALE = "male", "Мужской"
        FEMALE = "female", "Женский"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic_name = models.CharField(max_length=100, blank=True, null=True)
    date_birth = models.DateField()
    sex = models.CharField(max_length=10, choices=SexChoices.choices)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=12, unique=True)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.get_full_name()

    def get_full_name(self) -> str:
        if self.patronymic_name:
            return f"{self.last_name} {self.first_name} {self.patronymic_name}"
        return f"{self.last_name} {self.first_name}"

    @property
    def age(self) -> int:
        today = timezone.now().date()
        return (
            today.year
            - self.date_birth.year
            - ((today.month, today.day) < (self.date_birth.month, self.date_birth.day))
        )

    def clean(self):
        super().clean()
        if self.date_birth:
            if self.date_birth > timezone.now().date():
                raise ValidationError(
                    {"date_birth": "Дата рождения не может быть в будущем"}
                )
            if self.date_birth.year < 1900:
                raise ValidationError({"date_birth": "Некорректная дата рождения"})
        if self.phone_number:
            phone = self.phone_number.replace(" ", "")
            phone_regex = re.compile(r"^\+7\d{10}$")
            if not phone_regex.match(phone):
                raise ValidationError(
                    {"phone_number": "Телефон должен быть в формате +7XXXXXXXXXX"}
                )
            self.phone_number = phone

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Doctor(Person):
    specialization = models.CharField(max_length=100)
    date_start_work = models.DateField()
    date_end_work = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    @property
    def experience(self) -> int:
        end_date = self.date_end_work or timezone.now().date()
        return end_date.year - self.date_start_work.year

    def clean(self):
        super().clean()
        if self.date_start_work and self.date_end_work:
            if self.date_end_work < self.date_start_work:
                raise ValidationError(
                    {"date_end_work": "Дата окончания не может быть раньше начала"}
                )
        if self.date_start_work > timezone.now().date():
            raise ValidationError(
                {"date_start_work": "Дата начала работы не может быть в будущем"}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Patient(Person):
    class Meta:
        verbose_name = "Пациент"
        verbose_name_plural = "Пациенты"


class Admin(Person):
    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"


class Clinic(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    doctors = models.ManyToManyField(Doctor, related_name="clinics")
    name = models.CharField(max_length=100)
    registered_adress = models.CharField(max_length=150)
    actual_adress = models.CharField(max_length=150)
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

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

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.WAITED
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="consultations"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="consultations"
    )
    clinic = models.ForeignKey(
        Clinic, on_delete=models.CASCADE, related_name="consultations"
    )
    is_deleted = models.BooleanField(default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "start_time"], name="unique_doctor_time"
            )
        ]
        verbose_name = "Консультация"
        verbose_name_plural = "Консультации"

    def clean(self):
        super().clean()
        if not self.start_time:
            raise ValidationError({"start_time": "Укажите время начала"})
        if not self.end_time:
            raise ValidationError({"end_time": "Укажите время окончания"})

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


class DoctorEducation(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="educations", null=True, blank=True
    )
    university = models.CharField(max_length=100, null=True, blank=True)
    faculty = models.CharField(max_length=100, null=True, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Образование врача"
        verbose_name_plural = "Образования врачей"

    def clean(self):
        super().clean()
        if self.date_start and self.date_end:
            if self.date_start >= self.date_end:
                raise ValidationError(
                    {"date_end": "Дата окончания должна быть позже начала."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
