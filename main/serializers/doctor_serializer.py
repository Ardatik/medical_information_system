from .base_person_serializer import PersonSerializer
from main.models import Doctor
from django.contrib.auth.hashers import make_password


class DoctorSerializer(PersonSerializer):
    class Meta(PersonSerializer.Meta):
        model = Doctor
        fields = PersonSerializer.Meta.fields + [
            "specialization",
            "date_start_work",
            "date_end_work",
            "experience",
        ]
        read_only_fields = PersonSerializer.Meta.read_only_fields + [
            "experience",
        ]

    def create(self, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().update(instance, validated_data)
