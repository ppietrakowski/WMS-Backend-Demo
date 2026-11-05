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
from django.db.models import Sum
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


class MoveStowContainers(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        containers, dropzone = request.data['containers'], request.data['dropzone']
        StowSessionContainer.objects.filter(container_id__in=containers).delete()
        cnts = StorageUnit.objects.filter(id__in=containers).select_for_update()
        for c in cnts:
            c.dropzone = Dropzone.objects.get(pk=dropzone)
            c.save()

        return Response()


class StowItem(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        with transaction.atomic():
            return self._stow_item(request)
        

    def _stow_item(self, request):
        source_container, product, destination_container_id = request.data['container'], request.data['item'], request.data['target_bin']
        pr = ProductCode.objects.filter(id=product)

        if not pr.exists():
            return Response({'reason': 'product-not-available'}, status=status.HTTP_403_FORBIDDEN)
        
        count = int(request.data['count'])

        source_container_objects = self.get_container_items(container=source_container, product=product)

        if source_container_objects.count < count:
            return Response({'reason': 'count-more-than-available'},status=status.HTTP_403_FORBIDDEN)

        dest_container = StorageUnit.objects.get(pk=destination_container_id)
        
  
        if not dest_container.can_store_weight(count * pr.first().weight):
            return Response({'reason': 'weight-limit-reached'},status=status.HTTP_403_FORBIDDEN)

        if source_container_objects.damaged != dest_container.stores_damaged_items:
            return Response({'reason': 'mismatch-damage-location'},status=status.HTTP_403_FORBIDDEN)


        try:
            p = self.get_container_items(container=destination_container_id, product=product)
            p.count += count
            p.save()
        except ProductInContainer.DoesNotExist:
            if dest_container.has_reached_sku_limit():
                return Response({'reason': 'reach-sku-limit'},status=status.HTTP_403_FORBIDDEN)
            
            ProductInContainer.objects.create(product_id=product, count=count, damaged=source_container_objects.damaged, container_id=destination_container_id)

        source_container_objects.count -= count
        if source_container_objects.count <= 0:
            source_container_objects.delete()
        else:
            source_container_objects.save()

        return Response(status=status.HTTP_200_OK)
        
    def get_container_items(self, container: str, product: str):
        return ProductInContainer.objects.get(product_id=product, container_id=container)


class EndStowSession(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            count_missing = 0
            objs = StowSessionContainer.objects.filter(user=request.user)

            for o in objs:
                products = ProductInContainer.objects.filter(container = o.container)

                if not products.exists():
                    continue

                count_missing = products.aggregate(count=   Sum("count", outputField=models.IntegerField(), default=0))['count']

                if count_missing >= 4:
                    return Response({'reason': 'Too many products not stowed'}, status=status.HTTP_400_BAD_REQUEST)

                print(len(products))
                location = StorageUnit.objects.get(pk='LOCAMNESTYDE')

                if products.first().damaged:
                    location = StorageUnit.objects.get('LOCAMNESTYUN')

                for p in products:
                    loc = location.items.all().filter(product=p.product)

                    print(loc.exists())
                    if loc.exists():
                        loc.count += p.count
                        p.delete()
                        loc.save()
                    else:
                        p.container = location
                        p.save()

            objs.delete()

        return Response(status=status.HTTP_200_OK)