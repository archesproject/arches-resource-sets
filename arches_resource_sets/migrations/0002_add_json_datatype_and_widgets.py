import textwrap

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_resource_sets", "0001_initial"),
    ]

    add_json_datatype_and_widgets = textwrap.dedent(
        """
        INSERT INTO d_data_types(
            datatype,
            iconclass,
            modulename,
            classname,
            defaultconfig,
            configcomponent,
            configname,
            isgeometric,
            defaultwidget,
            issearchable
        ) VALUES (
            'json',
            'fa fa-code',
            'datatypes.py',
            'JsonDataType',
            '{}',
            'views/components/datatypes/json',
            'json-datatype-config',
            FALSE,
            'd7e72695-fcea-4cf5-92cf-0e404f96cace',
            FALSE
        )
        ON CONFLICT DO NOTHING;

        INSERT INTO widgets(
            widgetid,
            name,
            component,
            datatype,
            defaultconfig
        ) VALUES (
            'd7e72695-fcea-4cf5-92cf-0e404f96cace',
            'resourceset-select-widget',
            'views/components/widgets/resourceset-select',
            'json',
            '{"placeholder": "Select a resource set", "defaultValue": null, "multiValue": false, "i18n_properties": ["placeholder"]}'
        )
        ON CONFLICT DO NOTHING;
        """
    )

    operations = [
        migrations.RunSQL(add_json_datatype_and_widgets, migrations.RunSQL.noop),
    ]