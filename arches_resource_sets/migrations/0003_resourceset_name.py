import arches.app.models.fields.i18n
import arches.app.utils.betterJSONSerializer
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_resource_sets", "0002_add_json_datatype_and_widgets"),
    ]

    operations = [
        migrations.AddField(
            model_name="resourceset",
            name="name",
            field=arches.app.models.fields.i18n.I18n_TextField(
                blank=True,
                default="",
                encoder=arches.app.utils.betterJSONSerializer.JSONSerializer,
                null=True,
            ),
        ),
    ]
