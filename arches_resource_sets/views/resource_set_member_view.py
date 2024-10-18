from json import JSONDecodeError
from django.db import IntegrityError
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet, ResourceSetMember
from arches.app.utils.response import JSONResponse, JSONErrorResponse


class ResourceSetMemberView(APIBase):
    def get(self, request, set_id):
        """Returns either a flat representation (?flat=true) or a tree (default)."""
        try:
            set = ResourceSet.objects.get(pk=set_id).resourcesetmember_set.all().values_list("resource_instance_id", flat=True)
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Resource Set not found", "Resource Set with ID '{}' not found".format(set_id), status=404)
        
        return JSONResponse({"resource_set_members": set})

    def post(self, request, set_id):
        try:
            request_body = JSONDeserializer().deserialize(request.body)
            resource_id = request_body["resource_id"] if "resource_id" else ""
            ResourceSetMember.objects.create(resource_set_id=set_id, resource_instance_id=resource_id)
            return JSONResponse({"resource_set_id": set_id, "resource_instance_id": resource_id})
        except IntegrityError as e:
            if(len(e.args) > 0 and 'is not present in table "resource_set"' in e.args[0]):
                return JSONErrorResponse("Resource set not found", "Resource Set with ID '{}' was not found".format(resource_id), status=400)
            elif(len(e.args) > 0 and 'is not present in table "resource_instances"' in e.args[0]):
                return JSONErrorResponse("Could not add resource to set", "Invalid Resource ID '{}'".format(resource_id), status=400)
            else:
                return JSONErrorResponse("Resource in set", "Resource instance '{}' is already in this set".format(resource_id), status=400)
        except JSONDecodeError:
            return JSONErrorResponse("Invalid Resource ID", "Ensure the arches resource IDs in the request body are valid".format(resource_id), status=400)
        
    def delete(self, request, set_id, resource_id):
        try:
            ResourceSet.objects.get(pk=set_id) # throwaway to check if set exists
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Resource Set not found", "Resource Set with ID '{}' not found".format(set_id), status=404)
        
        members = ResourceSetMember.objects.filter(resource_set_id=set_id, resource_instance_id=resource_id)
        if len(members) == 0:
            return JSONErrorResponse("Could not delete resource set member", "Resource set member '{}' not found.".format(resource_id), status=404)

        members.delete()

        return JSONResponse({"resource_set_id": set_id, "resource_instance_id": resource_id})
