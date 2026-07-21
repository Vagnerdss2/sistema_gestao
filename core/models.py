from django.db import models


class TimeStampedModel(models.Model):
    """Mixin para rastrear criacao e ultima atualizacao."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
