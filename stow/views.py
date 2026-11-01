from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from core.models import *

from django.shortcuts import get_object_or_404
from functools import reduce
from rest_framework.permissions import IsAuthenticated
from .models import *

# Create your views here.

class StartStowSession(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        with transaction.atomic():
            containers = request.data['containers']

            for i in containers:
                StowSessionContainer.objects.get_or_create(defaults={
                    'container_id': i,
                    'user': request.user 
                })  

            return Response({'stow_containers': len(containers)})

        return Response(status=status.HTTP_403_FORBIDDEN)

class GetStowSession(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request: HttpRequest):
        containers =[i.container.id for i in StowSessionContainer.objects.filter(user=request.user)]
        return Response({'containers': containers})


class GetProductDetails(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest):

        product, container = request.data['product_code'], request.data['container']
        product = ProductCodeMapping.objects.get(code=product).product
        products = ProductInContainer.objects.filter(container_id=container, product=product)

        if not products.exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        p = products.first().product
        return Response({'product': {
            'id': p.id,
            'name': p.name,
            'weight': p.weight,
            'damaged': products.first().damaged
        }})

