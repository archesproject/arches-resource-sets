from json import JSONDecodeError
import logging

from django.forms import ValidationError
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet

logger = logging.getLogger(__name__)
class ResourceSetMembersBulkView(APIBase):
    def post(self, request, set_id):
        try:        
            request_body = JSONDeserializer().deserialize(request.body)
            resource_instance_ids = request_body["resource_instance_ids"] if "resource_instance_ids" in request_body else ""
            operation = request_body["operation"] if "operation" in request_body else "add"
            resource_set = ResourceSet.objects.get(id=set_id)
            if operation == "add":
                added, errors = resource_set.add_members(resource_instance_ids)
                return JSONResponse({"added": added, "errors": errors})
            elif operation == "remove":
                removed, errors = resource_set.remove_members(resource_instance_ids)
                return JSONResponse({"removed": removed, "errors": errors})
            else: 
                return JSONErrorResponse("Bulk operation failed", "operation '{}' is invalid".format(operation), status=400)
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Resource set not found", "Check your resource set ID and try again", status=404)
        except JSONDecodeError:
            return JSONErrorResponse("Invalid request body", "Check your request body and try again", status=400)
        except Exception as e:
            logger.error(e)
            return JSONErrorResponse("Unspecified error", "Contact an Administrator", status=500)

