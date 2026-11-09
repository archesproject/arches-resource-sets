import unittest
import uuid

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from arches_resource_sets.models import ResourceSet, ResourceSetMember
from tests.helpers import (
    create_resource_graph,
    create_resource_instance,
    immediate_constraints,
)


class ResourceSetModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("set_owner")
        graph = create_resource_graph()
        cls.resource_a = create_resource_instance(graph)
        cls.resource_b = create_resource_instance(graph)

    def setUp(self):
        immediate_constraints()
        self.resource_set = ResourceSet.objects.create(owner=self.user, name="Set")

    def member_ids(self, resource_set=None):
        resource_set = resource_set or self.resource_set
        return set(
            resource_set.resourcesetmember_set.values_list(
                "resource_instance_id", flat=True
            )
        )

    def test_add_members(self):
        ids = [self.resource_a.pk, self.resource_b.pk]
        added, errors = self.resource_set.add_members(ids)
        self.assertEqual(added, ids)
        self.assertEqual(errors, {})
        self.assertEqual(self.member_ids(), set(ids))

    # TODO: add_members needs a savepoint per member; a duplicate aborts the surrounding transaction.
    @unittest.expectedFailure
    def test_add_members_reports_duplicates_without_losing_valid_members(self):
        self.resource_set.add_members([self.resource_a.pk])
        added, errors = self.resource_set.add_members(
            [self.resource_a.pk, self.resource_b.pk]
        )
        self.assertEqual(added, [self.resource_b.pk])
        self.assertIn(self.resource_a.pk, errors)
        self.assertEqual(self.member_ids(), {self.resource_a.pk, self.resource_b.pk})

    # TODO: add_members needs a savepoint per member; an unknown ID aborts the surrounding transaction.
    @unittest.expectedFailure
    def test_add_members_reports_unknown_resources(self):
        missing = uuid.uuid4()
        added, errors = self.resource_set.add_members([missing, self.resource_a.pk])
        self.assertEqual(added, [self.resource_a.pk])
        self.assertIn(missing, errors)
        self.assertEqual(self.member_ids(), {self.resource_a.pk})

    def test_remove_members(self):
        self.resource_set.add_members([self.resource_a.pk, self.resource_b.pk])
        missing = uuid.uuid4()
        removed, errors = self.resource_set.remove_members(
            [self.resource_a.pk, missing]
        )
        self.assertEqual(removed, [self.resource_a.pk])
        self.assertIn(missing, errors)
        self.assertEqual(self.member_ids(), {self.resource_b.pk})

    def test_membership_is_scoped_to_set(self):
        other_set = ResourceSet.objects.create(owner=self.user)
        self.resource_set.add_members([self.resource_a.pk])
        other_set.add_members([self.resource_a.pk])

        removed, _ = other_set.remove_members([self.resource_a.pk])

        self.assertEqual(removed, [self.resource_a.pk])
        self.assertEqual(self.member_ids(), {self.resource_a.pk})
        self.assertEqual(self.member_ids(other_set), set())

    def test_member_is_unique_per_set(self):
        self.resource_set.add_members([self.resource_a.pk])
        with self.assertRaises(IntegrityError), transaction.atomic():
            ResourceSetMember.objects.create(
                resource_set=self.resource_set, resource_instance=self.resource_a
            )

    def test_deleting_set_deletes_members(self):
        self.resource_set.add_members([self.resource_a.pk])
        self.resource_set.delete()
        self.assertFalse(ResourceSetMember.objects.exists())

    def test_deleting_resource_removes_it_from_sets(self):
        self.resource_set.add_members([self.resource_a.pk, self.resource_b.pk])
        self.resource_a.delete()
        self.assertEqual(self.member_ids(), {self.resource_b.pk})

    def test_deleting_owner_deletes_sets(self):
        owner = User.objects.create_user("short_lived")
        ResourceSet.objects.create(owner=owner)
        owner.delete()
        self.assertFalse(ResourceSet.objects.filter(owner_id=owner.pk).exists())
