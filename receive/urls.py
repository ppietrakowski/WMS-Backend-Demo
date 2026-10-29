from .views import *
from django.urls import path, include

urlpatterns = [
    path('get_receive_products/', GetReceiveShipmentProducts.as_view(), name='get_receive_products'),
]