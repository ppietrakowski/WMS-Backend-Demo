from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *

from django.shortcuts import get_object_or_404

# Create your views here.
class IndexView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})

class ProductCodeSerializer(ModelSerializer):
    class Meta:
        model = ProductCode
        fields = '__all__'

class ProductCodeView(APIView):
    def get(self, request: HttpRequest, product_id: str):
        o = ProductCode.objects.filter(pk = product_id)

        if not o.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(ProductCodeSerializer(o.first(), many=False).data)
            
class ObjectInContainerSerializer(ModelSerializer):
    class Meta:
        model = ObjectInContainer
        fields = ['product', 'status', 'count', 'ship', 'damaged']

class ContainerItemsView(APIView):
    def get(self, request: HttpRequest, container_id: str):
        objects_in_container = None

        if container_id.startswith('ts'):
            objects_in_container = ObjectInContainer.objects.filter(tote_id=container_id)
        elif container_id.startswith('cs'):
            objects_in_container = ObjectInContainer.objects.filter(container_id=container_id)
        elif container_id.startswith('lo'):
            objects_in_container = ObjectInContainer.objects.filter(location_id=container_id)

        if not objects_in_container or not objects_in_container.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = ObjectInContainerSerializer(objects_in_container, many=True).data

        return_data = {}
        return_data['products'] = data
        return_data['container'] = container_id

        return Response(return_data, status=status.HTTP_200_OK)


class AddItemToContainerView(APIView):
    def post(self, request: HttpRequest, container_id: str):
        objects, created = None, False

        if 'damaged' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'product' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if 'count' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if container_id.startswith('ts'):
            objects, created = ObjectInContainer.objects.get_or_create(product_id=request.data['product'], tote_id=container_id, defaults={'count': int(request.data['count']), 'damaged': request.data['damaged']})

        elif container_id.startswith('cs'):
            objects, created = ObjectInContainer.objects.get_or_create(product_id=request.data['product'], container_id=container_id, defaults={'count': int(request.data['count']), 'damaged': request.data['damaged']})
        elif container_id.startswith('lo'):
            objects, created = ObjectInContainer.objects.get_or_create(product_id=request.data['product'], location_id=container_id, defaults={'count': int(request.data['count']), 'damaged': request.data['damaged']})

        if not created:
            if request.data['damaged'] != objects.damaged:
               return Response(status=status.HTTP_403_FORBIDDEN)
            objects.count += int(request.data['count'])
            objects.save()

        return Response('ok', status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class RemoveItemFromContainer(APIView):
    def delete(self, request: HttpRequest, container_id: str):
        if 'product' not in request.data:
            return Response(status=status.HTTP_403_FORBIDDEN)

        count = 1
        if 'count' in request.data:
            count = int(request.data['count'])

        objects = []

        if container_id.startswith('ts'):
            objects = ObjectInContainer.objects.filter(tote_id=container_id)

        return Response(status=status.HTTP_200_OK)