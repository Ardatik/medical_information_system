from django.db import models
from django.db.models.query import QuerySet
from typing import Any


class ActiveManager(models.Manager):
    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(is_deleted=False)