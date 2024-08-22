import uuid
from django.db import models
from django.conf import settings

from arches.app.models.models import ResourceInstance
from arches.app.models.models import I18n_TextField


class ResourceSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        db_column="userid",
        null=False,
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
    )
    description = I18n_TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_created=True)
    date_updated = models.DateTimeField(auto_now_add=True)


class ResourceSetMember(models.Model):
    resourcesetid = models.ForeignKey(
        ResourceSet, on_delete=models.CASCADE, blank=False, null=False
    )
    resourceid = models.ForeignKey(ResourceInstance, on_delete=models.CASCADE)
