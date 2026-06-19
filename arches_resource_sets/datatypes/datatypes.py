import ast
import json

from django.db.models import JSONField
from django.utils.translation import gettext as _

from arches.app.datatypes.base import BaseDataType

class JsonDataType(BaseDataType):
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
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            return [
                self.create_error_message(
                    value=value,
                    source=source,
                    row_number=row_number,
                    message=str(e),
                    title=_("Invalid JSON"),
                )
            ]

        return []

    def transform_value_for_tile(self, value, **kwargs):
        if value in (None, ""):
            return None

        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                try:
                    return ast.literal_eval(value)
                except Exception:
                    return value

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

    def append_to_document(self, document, nodevalue, nodeid, tile, provisional=False):
        if nodevalue is None:
            return

        if isinstance(nodevalue, str):
            indexed_value = nodevalue
        else:
            try:
                indexed_value = json.dumps(nodevalue, sort_keys=True)
            except (TypeError, ValueError):
                indexed_value = str(nodevalue)

        document["strings"].append(
            {
                "string": indexed_value,
                "nodegroup_id": tile.nodegroup_id,
                "provisional": provisional,
            }
        )

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
