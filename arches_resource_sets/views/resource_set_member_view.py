from django.db import IntegrityError
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSetMember
from arches.app.utils.response import JSONResponse, JSONErrorResponse


class ResourceSetMemberView(APIBase):
    def get(self, request, set_id):
        """Returns either a flat representation (?flat=true) or a tree (default)."""
        set = ResourceSetMember.objects.filter(resource_set_id=set_id).values_list("resource_instance_id", flat=True)

        return JSONResponse({"resource_set_members": set})

    def post(self, request, set_id):
        request_body = JSONDeserializer().deserialize(request.body)
        resource_id = request_body["resource_id"] if "resource_id" else ""
        try:
            ResourceSetMember.objects.create(resource_set_id=set_id, resource_instance_id=resource_id)
            return JSONResponse({"resource_set_id": set_id, "resource_instance_id": resource_id})
        except IntegrityError as e:
            if(len(e.args) > 0 and "is not present in table" in e.args[0]):
                return JSONErrorResponse("Could not add resource to set", "Invalid Resource ID '{}'".format(resource_id), status=400)
            else:
                return JSONErrorResponse("Could not add resource to set", "Set resource '{}' would be duplicative".format(resource_id), status=400)

    def delete(self, request, set_id, resource_id):
        members = ResourceSetMember.objects.filter(resource_set_id=set_id, resource_instance_id=resource_id)
        if len(members) == 0:
            return JSONErrorResponse("Could not delete resource set member", "Resource set member '{}' not found.".format(resource_id), status=404)

        members.delete()

        return JSONResponse({"resource_set_id": set_id, "resource_instance_id": resource_id})
