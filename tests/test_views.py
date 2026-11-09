import json
import unittest
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from arches_resource_sets.models import ResourceSet, ResourceSetMember
from tests.helpers import (
    create_resource_graph,
    create_resource_instance,
    immediate_constraints,
)


class ResourceSetApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("api_user")
        graph = create_resource_graph()
        cls.resource_a = create_resource_instance(graph)
        cls.resource_b = create_resource_instance(graph)

    def setUp(self):
        immediate_constraints()
        self.client.force_login(self.user)
        self.resource_set = ResourceSet.objects.create(
            owner=self.user, name="Original", description="Original description"
        )

    def send(self, method, url, body=None):
        data = body if isinstance(body, str) or body is None else json.dumps(body)
        return getattr(self.client, method)(
            url, data=data, content_type="application/json"
        )

    def member_ids(self, resource_set=None):
        resource_set = resource_set or self.resource_set
        return set(
            ResourceSetMember.objects.filter(resource_set=resource_set).values_list(
                "resource_instance_id", flat=True
            )
        )


class ResourceSetViewTests(ResourceSetApiTestCase):
    def test_list(self):
        other = ResourceSet.objects.create(owner=self.user)
        response = self.client.get(reverse("resource_sets"))
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json()["resource_sets"]}
        self.assertEqual(ids, {str(self.resource_set.pk), str(other.pk)})

    def test_get(self):
        response = self.client.get(reverse("resource_set", args=[self.resource_set.pk]))
        self.assertEqual(response.status_code, 200)
        body = response.json()["resource_set"]
        self.assertEqual(body["id"], str(self.resource_set.pk))
        self.assertEqual(body["owner_id"], self.user.pk)

    def test_get_unknown_set_returns_null(self):
        response = self.client.get(reverse("resource_set", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["resource_set"])

    def test_create(self):
        response = self.send(
            "post", reverse("resource_sets"), {"name": "New", "description": "Desc"}
        )
        self.assertEqual(response.status_code, 200)
        created = ResourceSet.objects.get(pk=response.json()["resource_set"]["id"])
        self.assertEqual(created.owner, self.user)
        self.assertEqual(str(created.name), "New")
        self.assertEqual(str(created.description), "Desc")

    def test_create_without_body(self):
        response = self.client.generic("POST", reverse("resource_sets"))
        self.assertEqual(response.status_code, 200)
        created = ResourceSet.objects.get(pk=response.json()["resource_set"]["id"])
        self.assertEqual(created.owner, self.user)

    def test_create_with_malformed_body(self):
        count = ResourceSet.objects.count()
        response = self.send("post", reverse("resource_sets"), "{not json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ResourceSet.objects.count(), count)

    def test_update_changes_only_supplied_fields(self):
        response = self.send(
            "put",
            reverse("resource_set", args=[self.resource_set.pk]),
            {"name": "Renamed"},
        )
        self.assertEqual(response.status_code, 200)
        self.resource_set.refresh_from_db()
        self.assertEqual(str(self.resource_set.name), "Renamed")
        self.assertEqual(str(self.resource_set.description), "Original description")

    def test_update_unknown_set(self):
        response = self.send(
            "put", reverse("resource_set", args=[uuid.uuid4()]), {"name": "x"}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_with_malformed_body(self):
        response = self.send(
            "put", reverse("resource_set", args=[self.resource_set.pk]), "{not json"
        )
        self.assertEqual(response.status_code, 400)
        self.resource_set.refresh_from_db()
        self.assertEqual(str(self.resource_set.name), "Original")

    def test_delete(self):
        ResourceSetMember.objects.create(
            resource_set=self.resource_set, resource_instance=self.resource_a
        )
        response = self.client.delete(
            reverse("resource_set", args=[self.resource_set.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["resource_set"]["id"], str(self.resource_set.pk)
        )
        self.assertFalse(ResourceSet.objects.filter(pk=self.resource_set.pk).exists())
        self.assertFalse(ResourceSetMember.objects.exists())

    def test_delete_unknown_set(self):
        response = self.client.delete(reverse("resource_set", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)


class ResourceSetMemberViewTests(ResourceSetApiTestCase):
    def members_url(self, set_id=None):
        return reverse("resource_set_members", args=[set_id or self.resource_set.pk])

    def member_url(self, resource_id, set_id=None):
        return reverse(
            "resource_set_member", args=[set_id or self.resource_set.pk, resource_id]
        )

    def test_list_members(self):
        self.resource_set.add_members([self.resource_a.pk, self.resource_b.pk])
        response = self.client.get(self.members_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.json()["resource_instance_ids"]),
            {str(self.resource_a.pk), str(self.resource_b.pk)},
        )

    def test_list_members_of_unknown_set(self):
        response = self.client.get(self.members_url(uuid.uuid4()))
        self.assertEqual(response.status_code, 404)

    def test_add_member(self):
        response = self.send(
            "post", self.members_url(), {"resource_id": str(self.resource_a.pk)}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.member_ids(), {self.resource_a.pk})

    # TODO: member POST needs a savepoint; a duplicate aborts the surrounding transaction.
    @unittest.expectedFailure
    def test_add_existing_member(self):
        self.resource_set.add_members([self.resource_a.pk])
        response = self.send(
            "post", self.members_url(), {"resource_id": str(self.resource_a.pk)}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.member_ids(), {self.resource_a.pk})

    # TODO: member POST needs a savepoint; an unknown resource aborts the surrounding transaction.
    @unittest.expectedFailure
    def test_add_unknown_resource(self):
        response = self.send(
            "post", self.members_url(), {"resource_id": str(uuid.uuid4())}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.member_ids(), set())

    # TODO: member POST needs a savepoint; an unknown set aborts the surrounding transaction.
    @unittest.expectedFailure
    def test_add_member_to_unknown_set(self):
        response = self.send(
            "post",
            self.members_url(uuid.uuid4()),
            {"resource_id": str(self.resource_a.pk)},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ResourceSetMember.objects.exists())

    # TODO: member POST 500s on bad JSON (UnboundLocalError on resource_id).
    @unittest.expectedFailure
    def test_add_member_with_malformed_body(self):
        response = self.send("post", self.members_url(), "{not json")
        self.assertEqual(response.status_code, 400)

    # TODO: member POST 500s when resource_id is missing (KeyError).
    @unittest.expectedFailure
    def test_add_member_without_resource_id(self):
        response = self.send("post", self.members_url(), {})
        self.assertEqual(response.status_code, 400)

    def test_remove_member(self):
        self.resource_set.add_members([self.resource_a.pk, self.resource_b.pk])
        response = self.client.delete(self.member_url(self.resource_a.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.member_ids(), {self.resource_b.pk})

    def test_remove_non_member(self):
        response = self.client.delete(self.member_url(self.resource_a.pk))
        self.assertEqual(response.status_code, 404)

    def test_remove_member_of_unknown_set(self):
        response = self.client.delete(
            self.member_url(self.resource_a.pk, set_id=uuid.uuid4())
        )
        self.assertEqual(response.status_code, 404)


class ResourceSetMembersBulkViewTests(ResourceSetApiTestCase):
    def bulk_url(self, set_id=None):
        return reverse(
            "resource_set_members_bulk", args=[set_id or self.resource_set.pk]
        )

    def test_bulk_add(self):
        ids = [str(self.resource_a.pk), str(self.resource_b.pk)]
        response = self.send("post", self.bulk_url(), {"resource_instance_ids": ids})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"added": ids, "errors": {}})
        self.assertEqual(self.member_ids(), {self.resource_a.pk, self.resource_b.pk})

    # TODO: bulk add inherits the add_members savepoint bug.
    @unittest.expectedFailure
    def test_bulk_add_reports_failures(self):
        self.resource_set.add_members([self.resource_a.pk])
        missing = str(uuid.uuid4())
        response = self.send(
            "post",
            self.bulk_url(),
            {
                "resource_instance_ids": [
                    str(self.resource_a.pk),
                    missing,
                    str(self.resource_b.pk),
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["added"], [str(self.resource_b.pk)])
        self.assertEqual(set(body["errors"]), {str(self.resource_a.pk), missing})
        self.assertEqual(self.member_ids(), {self.resource_a.pk, self.resource_b.pk})

    def test_bulk_remove(self):
        self.resource_set.add_members([self.resource_a.pk, self.resource_b.pk])
        response = self.send(
            "post",
            self.bulk_url(),
            {"operation": "remove", "resource_instance_ids": [str(self.resource_a.pk)]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), {"removed": [str(self.resource_a.pk)], "errors": {}}
        )
        self.assertEqual(self.member_ids(), {self.resource_b.pk})

    def test_bulk_invalid_operation(self):
        response = self.send(
            "post",
            self.bulk_url(),
            {"operation": "merge", "resource_instance_ids": [str(self.resource_a.pk)]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.member_ids(), set())

    def test_bulk_unknown_set(self):
        response = self.send(
            "post",
            self.bulk_url(uuid.uuid4()),
            {"resource_instance_ids": [str(self.resource_a.pk)]},
        )
        self.assertEqual(response.status_code, 404)

    def test_bulk_malformed_body(self):
        response = self.send("post", self.bulk_url(), "{not json")
        self.assertEqual(response.status_code, 400)

    def test_bulk_create_set_with_members(self):
        response = self.send(
            "post",
            reverse("resource_set_members_bulk_create"),
            {
                "name": "Bulk",
                "description": "Bulk description",
                "resource_instance_ids": [str(self.resource_a.pk)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["added"], [str(self.resource_a.pk)])
        created = ResourceSet.objects.exclude(pk=self.resource_set.pk).get()
        self.assertEqual(created.owner, self.user)
        self.assertEqual(str(created.name), "Bulk")
        self.assertEqual(self.member_ids(created), {self.resource_a.pk})
