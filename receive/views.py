from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *

from django.shortcuts import get_object_or_404

# Create your views here.
class GetReceiveShipmentProducts(APIView):
    def post(self, request: HttpRequest):

        if 'ship_id' not in request.data:
            return Response('Provide ship_id to get products', status.HTTP_404_NOT_FOUND) 

        return Response('Invalid shipment id', status.HTTP_400_BAD_REQUEST) 