from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *

from django.shortcuts import get_object_or_404

# Create your views here.
class GetReceiveShipmentProducts(APIView):
    def post(self, request: HttpRequest):
        return Response('ok')