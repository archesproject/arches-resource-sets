from json import JSONDecodeError
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet


class ResourceSetMembersBulkView(APIBase):
    def post(self, request, set_id):
        try:        
            request_body = JSONDeserializer().deserialize(request.body)
            resource_ids = request_body["resource_ids"] if "resource_ids" in request_body else ""
            operation = request_body["operation"] if "operation" in request_body else "add"
            set = ResourceSet.objects.get(id=set_id)

        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Resource set not found", "Check your resource set ID and try again", status=404)
        except JSONDecodeError:
            return JSONErrorResponse("Invalid request body", "Check your request body and try again", status=400)

        if operation == "add":
            return JSONResponse({"added": set.add_members(resource_ids)})
        elif operation == "remove":
            return JSONResponse({"removed": set.remove_members(resource_ids)})
        else: 
            return JSONErrorResponse("Bulk operation failed", "operation '{}' is invalid".format(operation), status=400)
