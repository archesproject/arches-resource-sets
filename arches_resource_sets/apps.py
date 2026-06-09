from django.apps import AppConfig, apps


class ArchesResourceSetsConfig(AppConfig):
    name = "arches_resource_sets"
    verbose_name = "Arches Resource Sets"
    is_arches_application = True

    def ready(self):
        if apps.get_app_config("arches_querysets"):
            from arches_querysets.rest_framework.serializers import (
                TileAliasedDataSerializer,
            )

            from arches_resource_sets.datatypes.datatypes import (
                JsonField,
                JsonSerializer,
            )

            TileAliasedDataSerializer.register_custom_datatype_field(
                JsonField, JsonSerializer
            )
