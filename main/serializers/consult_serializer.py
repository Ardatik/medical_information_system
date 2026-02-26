from django.utils import timezone
from rest_framework import serializers
from main.models import Consultation
from main.serializers.doctor_serializer import DoctorSerializer
from main.serializers.patient_serializer import PatientSerializer
from main.serializers.clinic_serializer import ClinicSerializer
from main.models import Doctor, Patient, Clinic


class ConsultationReadSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(source="doctor", read_only=True)
    patient = PatientSerializer(source="patient", read_only=True)
    clinic = ClinicSerializer(source="clinic", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id",
            "created_at",
            "updated_at",
            "start_time",
            "end_time",
            "status",
            "doctor",
            "patient",
            "clinic",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ConsultationWriteSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.filter(is_deleted=False),
    )
    patient = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.filter(is_deleted=False),
    )
    clinic = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.filter(is_deleted=False),
    )

    class Meta:
        model = Consultation
        fields = ["start_time", "end_time", "status", "doctor", "patient", "clinic"]

    def validate(self, attrs):
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        doctor = attrs.get("doctor")
        clinic = attrs.get("clinic")
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    "Консультация не может закончиться раньше, чем начаться"
                )
            if start_time < timezone.now():
                raise serializers.ValidationError(
                    {"start_time": "Начало консультации не может быть в прошлом"}
                )
        if doctor and start_time and end_time:
            overlapping = Consultation.objects.filter(
                doctor=doctor,
                start_time__lt=end_time,
                end_time__gt=start_time,
                is_deleted=False,
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise serializers.ValidationError(
                    {"start_time": "У врача уже назначена консультация в это время"}
                )
        if clinic and doctor:
            if not doctor.clinics.filter(id=clinic.id).exists():
                raise serializers.ValidationError({
                    "doctor": "Доктор не работает в этой клинике"
                })
        return attrs
