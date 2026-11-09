import uuid
from types import SimpleNamespace

from django.test import SimpleTestCase

from arches_resource_sets.datatypes.datatypes import JsonDataType


class JsonDataTypeTests(SimpleTestCase):
    def setUp(self):
        self.datatype = JsonDataType()
        self.nodeid = str(uuid.uuid4())

    def make_tile(self, value):
        return SimpleNamespace(data={self.nodeid: value}, provisionaledits=None)

    def test_transform_parses_json_string(self):
        self.assertEqual(
            self.datatype.transform_value_for_tile('{"a": [1, 2]}'), {"a": [1, 2]}
        )

    def test_transform_parses_python_literal_string(self):
        self.assertEqual(
            self.datatype.transform_value_for_tile("{'a': True, 'b': None}"),
            {"a": True, "b": None},
        )

    def test_transform_passes_through_json_compatible_values(self):
        for value in (None, {"a": 1}, [1, "two"], 3, 4.5, False):
            with self.subTest(value=value):
                self.assertEqual(self.datatype.transform_value_for_tile(value), value)

    def test_transform_rejects_unparseable_string(self):
        with self.assertRaises(TypeError):
            self.datatype.transform_value_for_tile("{not json")

    def test_transform_rejects_non_json_types(self):
        for value in (object(), {1, 2}, b"bytes"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    self.datatype.transform_value_for_tile(value)

    def test_validate_accepts_valid_values(self):
        self.assertEqual(self.datatype.validate('{"a": 1}'), [])
        self.assertEqual(self.datatype.validate({"a": 1}), [])

    def test_validate_reports_invalid_value(self):
        errors = self.datatype.validate("{not json", row_number=3, source="file.csv")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["type"], "ERROR")
        self.assertEqual(errors[0]["title"], "Invalid JSON")
        self.assertIn("file.csv 3", errors[0]["message"])

    def test_clean_nulls_empty_values(self):
        for value in ("", [], {}):
            with self.subTest(value=value):
                tile = self.make_tile(value)
                self.datatype.clean(tile, self.nodeid)
                self.assertIsNone(tile.data[self.nodeid])

    def test_clean_keeps_falsy_scalars(self):
        for value in (0, False, {"a": 1}):
            with self.subTest(value=value):
                tile = self.make_tile(value)
                self.datatype.clean(tile, self.nodeid)
                self.assertEqual(tile.data[self.nodeid], value)

    def test_transform_export_values(self):
        self.assertIsNone(self.datatype.transform_export_values(None))
        self.assertEqual(
            self.datatype.transform_export_values({"a": [1]}), '{"a": [1]}'
        )

    def test_display_value_is_pretty_printed_and_sorted(self):
        node = SimpleNamespace(nodeid=self.nodeid)
        tile = self.make_tile({"b": 1, "a": 2})
        self.assertEqual(
            self.datatype.get_display_value(tile, node),
            '{\n  "a": 2,\n  "b": 1\n}',
        )

    def test_display_value_is_empty_for_empty_data(self):
        node = SimpleNamespace(nodeid=self.nodeid)
        for value in (None, "", [], {}):
            with self.subTest(value=value):
                tile = SimpleNamespace(
                    data={self.nodeid: value, "other": "x"}, provisionaledits=None
                )
                self.assertEqual(self.datatype.get_display_value(tile, node), "")
