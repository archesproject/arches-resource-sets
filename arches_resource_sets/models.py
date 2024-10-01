import uuid
from django.db import IntegrityError, models
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
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        managed = True
        db_table = "resource_set"

    def add_members(self, members):
        added = []
        for member in members:
            try:
                ResourceSetMember.objects.create(resource_set_id=self.id, resource_instance_id=member)
                added.append(member)
            except IntegrityError:
                pass
        return added

    def remove_members(self, members):
        removed = []
        for member in members:
            try:
                ResourceSetMember.objects.get(resource_set_id=self.id, resource_instance_id=member).delete()
                removed.append(member)
            except ResourceSetMember.DoesNotExist:
                pass
        return removed


class ResourceSetMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_set = models.ForeignKey(ResourceSet, on_delete=models.CASCADE, blank=False, null=False)
    resource_instance = models.ForeignKey(ResourceInstance, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = "resource_set_member"
        unique_together = ["resource_set", "resource_instance"]
