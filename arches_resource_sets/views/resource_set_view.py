from json import JSONDecodeError
import logging
import uuid

from django.http import Http404

from arches.app.views.api import APIBase
from arches_resource_sets.models import ResourceSet
from arches.app.utils.response import JSONErrorResponse, JSONResponse
from arches.app.utils.betterJSONSerializer import JSONDeserializer, JSONSerializer

logger = logging.getLogger(__name__)

class ResourceSetView(APIBase):
    def get(self, request, set_id=None):
        if set_id is None:
            return JSONResponse({"resource_sets": ResourceSet.objects.all()})
        resource_set = ResourceSet.objects.filter(id=set_id).values().first()
        return JSONResponse({"resource_set": resource_set})

    def put(self, request, set_id):
        try:
            resource_set = ResourceSet.objects.get(id=set_id)
            request_body = JSONDeserializer().deserialize(request.body)
            description = request_body["description"] if "description" else ""
            resource_set.description = description
            resource_set.save()
            return JSONResponse({"resource_set": resource_set})
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Could not update resource set", "Resource set id '{}' not found".format(set_id), status=404)
        except JSONDecodeError:
            return JSONErrorResponse("Could not update resource set", "Invalid request body: '{}'".format(request.body), status=400) 
        except Exception as e:
            logger.error(e)
            return JSONErrorResponse("Unspecified error", "Contact an Administrator", status=500)



    def post(self, request):
        description = ""
        set_id = uuid.uuid4()
        try:
            if request.body:
                request_body = JSONDeserializer().deserialize(request.body)
                description = request_body["description"] if "description" in request_body else ""

            resource_set = ResourceSet.objects.create(id=set_id, owner=request.user, description=description)
            return JSONResponse({"resource_set": resource_set})
        except JSONDecodeError:
            return JSONErrorResponse("Request was malformed", "Ensure the request body is valid json", status=400)
        except Exception as e:
            logger.error(e)
            return JSONErrorResponse("Unspecified error", "Contact an Administrator", status=500)



    def delete(self, request, set_id):
        try:
            set_obj = ResourceSet.objects.get(id=set_id)
            set_obj.delete()
            return JSONResponse({"resource_set": set_obj})
        except ResourceSet.DoesNotExist:
            return JSONErrorResponse("Could not delete resource set", "Resource set id '{}' not found".format(set_id), status=404)   
        except Exception as e:
            logger.error(e)
            return JSONErrorResponse("Unspecified error", "Contact an Administrator", status=500)

