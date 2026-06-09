import json

from django.db.models import JSONField
from django.utils.translation import gettext as _

from arches.app.datatypes.base import BaseDataType

try:
    import rest_framework.fields
except Exception:
    rest_framework = None
else:

    class JsonSerializer(rest_framework.fields.JSONField):
        def to_internal_value(self, data):
            return JsonDataType().transform_value_for_tile(data)


class JsonField(JSONField):
    pass


class JsonDataType(BaseDataType):
    model_field = JsonField(null=True)

    def validate(
        self,
        value,
        row_number=None,
        source="",
        node=None,
        nodeid=None,
        strict=False,
        **kwargs,
    ):
        if value in (None, ""):
            return []

        try:
            self.transform_value_for_tile(value)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return [
                self.create_error_message(
                    value=value,
                    source=source,
                    row_number=row_number,
                    message=str(exc),
                    title=_("Invalid JSON"),
                )
            ]

        return []

    def transform_value_for_tile(self, value, **kwargs):
        if value in (None, ""):
            return None

        if isinstance(value, str):
            return json.loads(value)

        if isinstance(value, (dict, list, int, float, bool)):
            return value

        raise TypeError(_("Value must be valid JSON"))

    def clean(self, tile, nodeid):
        super().clean(tile, nodeid)
        if tile.data[nodeid] == []:
            tile.data[nodeid] = None

    def transform_export_values(self, value, *args, **kwargs):
        if value is None:
            return None
        return json.dumps(value)

    def get_display_value(self, tile, node, **kwargs):
        data = self.get_tile_data(tile)
        if not data:
            return ""

        value = data.get(str(node.nodeid))
        if value in (None, ""):
            return ""

        try:
            return json.dumps(value, indent=2, sort_keys=True)
        except TypeError:
            return str(value)

    def append_to_document(self, document, nodevalue, nodeid, tile, provisional=False):
        if nodevalue in (None, ""):
            return

        if "strings" not in document:
            document["strings"] = []

        document["strings"].append(
            {
                "string": json.dumps(nodevalue, sort_keys=True),
                "nodegroup_id": tile.nodegroup_id,
                "provisional": provisional,
            }
        )