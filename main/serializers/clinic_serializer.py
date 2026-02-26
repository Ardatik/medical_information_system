from rest_framework import serializers
from main.models import Clinic
from .doctor_serializer import DoctorSerializer


class ClinicSerializer(serializers.ModelSerializer):
    doctors = DoctorSerializer(many=True, read_only=True)

    class Meta:
        model = Clinic
        fields = [
            "id",
            "name",
            "registered_address",
            "actual_address",
            "doctors",
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Название клиники не может быть пустым")
        return value
    
    def validate_registered_address(self, value):
        if not value:
            raise serializers.ValidationError("Юридический адрес клиники не может быть пустым")
        return value
    
    def validate_actual_address(self, value):
        if not value:
            raise serializers.ValidationError("Физический адрес клиники не может быть пустым")
        return value
