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
            
