import uuid

from django.http import Http404

from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet
from arches.app.utils.response import JSONResponse
from arches.app.utils.betterJSONSerializer import JSONDeserializer, JSONSerializer


class ResourceSetObjectView(APIBase):
    def get(self, request, set_id):
        set = ResourceSet.objects.filter(id=set_id).values().first()
        return JSONResponse({"resource_set": set})

    def post(self, request, set_id):
        request_body = JSONDeserializer().deserialize(request.body)
        description = request_body["description"] if "description" else ""

        set = ResourceSet.objects.get(id=set_id)
        set.description = description
        set.save()

        return JSONResponse({"resource_set": {"id": str(set_id)}})

    def delete(self, request, set_id):
        try:
            set_obj = ResourceSet.objects.get(id=set_id)
        except ResourceSet.DoesNotExist:
            raise Http404

        set_obj.delete()
        return JSONResponse({"resource_set": set_id})


class ResourceSetView(APIBase):
    action = "list"

    def get(self, request):
        sets = ResourceSet.objects.all()
        return JSONResponse({"resource_sets": sets})

    def post(self, request):
        set_id = uuid.uuid4()
        request_body = JSONDeserializer().deserialize(request.body)
        description = request_body["description"] if "description" else ""
        set = ResourceSet.objects.create(id=set_id, owner=request.user, description=description)

        return JSONResponse({"resource_set": {"id": str(set_id)}}, status=201)
