from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONResponse
from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet


class ResourceSetMembersBulkView(APIBase):
    def post(self, request, set_id):
        request_body = JSONDeserializer().deserialize(request.body)
        resource_ids = request_body["resource_ids"] if "resource_ids" in request_body else ""
        operation = request_body["operation"] if "operation" in request_body else "add"

        try:
            set = ResourceSet.objects.get(id=set_id)

        except ResourceSet.DoesNotExist:
            return JSONResponse({"error": "Resource set not found"}, status=404)

        if operation == "add":
            return JSONResponse({"added": set.add_members(resource_ids)})
        elif operation == "remove":
            return JSONResponse({"removed": set.remove_members(resource_ids)})
