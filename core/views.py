from django.shortcuts import render
from rest_framework.views import *

# Create your views here.
class IndexView(APIView):
    def get(self, request):
        return Response({'status': 'ok'})
    