from django.db import connection
from arches.app.models.graph import Graph
from arches.app.models.models import ResourceInstance


def create_resource_graph():
    return Graph.objects.create_graph("Resource Set Test Model", is_resource=True)


def create_resource_instance(graph):
    return ResourceInstance.objects.create(graph_id=graph.pk)


def immediate_constraints():
    # TestCase wraps tests in a transaction, deferring FK checks; production
    # autocommit enforces them per statement.
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
