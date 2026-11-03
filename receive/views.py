from django.shortcuts import render
from rest_framework.views import *
from rest_framework.request import HttpRequest
from rest_framework.serializers import ModelSerializer
from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from core.models import *
from rest_framework.permissions import IsAuthenticated

class ReceiveItem:
    code = ''
    current_count = 1
    total_count = 1
    damaged = False

    def __init__(self, code, current_count, total_count, damaged):
        self.code = code
        self.current_count = current_count
        self.total_count = total_count
        self.damaged = damaged

class ReceiveItemSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12, min_length=10)
    current_count = serializers.IntegerField(min_value=1)
    total_count = serializers.IntegerField(min_value=1)
    damaged = serializers.BooleanField()


# Create your views here.
class GetReceiveShipmentProducts(APIView):
    def post(self, request: HttpRequest):

        if 'ship_id' not in request.data:
            return Response({'message': 'Provide ship_id', 
                             'type': 'error'}, status.HTTP_404_NOT_FOUND) 

        try:
            ship_id = request.data['ship_id']
            InboundShipmentID.objects.get(id=ship_id)

            products = ProductInContainer.objects.filter(container_id=ship_id)

            p = []
            for i in products:
                p.append(ReceiveItem(i.product.id, i.count, i.count, i.damaged))

            if not products.exists():
                return Response({'message': 'Empty shipment id', 
                                             'type': 'error'}, status.HTTP_400_BAD_REQUEST) 

            s = ReceiveItemSerializer(p, many=True)

            return Response({'message': f'Selected shipment "{ship_id}"',
                             'type': 'info',
                             'products': s.data})
        except InboundShipmentID.DoesNotExist:
            return Response({'message': 'Invalid shipment id', 
                             'type': 'error'}, status.HTTP_400_BAD_REQUEST) 


class GetToteHasSameModifierAsProduct(APIView):
    # to prevent caching by browser
    def post(self, request: HttpRequest):
        if 'damaged' not in request.data:
            return Response({'message': 'Invalid request', 
                                         'type': 'error'}, status.HTTP_400_BAD_REQUEST)   
        if 'tote_id' not in request.data:
            return Response({'message': 'Invalid request', 
                                                 'type': 'error'}, status.HTTP_400_BAD_REQUEST)   

        damaged = bool(request.data['damaged'])
        tote_id = request.data['tote_id']

        objects = ProductInContainer.objects.filter(container_id=tote_id)

        if not objects.exists():
            return Response(True)

        container_damage = objects.first().damaged
        return Response(container_damage == damaged)


class ReceiveProblemSolveRaise(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        psr, ship, reason = request.data['psr_id'], request.data['ship_id'], int(request.data['reason'])

        ReceiveProblemSolveCode.objects.create(psr=psr,ship_id=ship,by_whom=request.user,reason=reason)
        return Response(status=status.HTTP_201_CREATED)

class GetProductByCode(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        p = ProductCodeMapping.objects.get(code=product_id).product
        return Response({'product': {
            'id': p.id,
            'name': p.name,
            'weight': p.weight,
        }})
