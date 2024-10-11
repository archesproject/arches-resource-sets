import uuid

from django.http import Http404

from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.utils.betterJSONSerializer import JSONDeserializer, JSONSerializer


class ResourceSetView(APIBase):
    def get(self, request, set_id=None):
        if set_id is None:
            return JSONResponse({"resource_sets": ResourceSet.objects.all()})
        set = ResourceSet.objects.filter(id=set_id).values().first()
        return JSONResponse({"resource_set": set})

    def put(self, request, set_id):
        try:
            set = ResourceSet.objects.get(id=set_id)
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Could not update resource set", "Resource set id '{}' not found".format(set_id), status=404)
        
        request_body = JSONDeserializer().deserialize(request.body)
        description = request_body["description"] if "description" else ""
        set.description = description
        set.save()

        return JSONResponse({"resource_set": {"id": str(set_id)}})


    def post(self, request):
        set_id = uuid.uuid4()
        set = ResourceSet.objects.create(id=set_id, owner=request.user)

        request_body = JSONDeserializer().deserialize(request.body)
        description = request_body["description"] if "description" else ""
        set.description = description
        set.save()

        return JSONResponse({"resource_set": {"id": str(set_id)}})

    def delete(self, request, set_id):
        try:
            set_obj = ResourceSet.objects.get(id=set_id)
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Could not delete resource set", "Resource set id '{}' not found".format(set_id), status=404)   

        set_obj.delete()
        return JSONResponse({"resource_set": set_id})
