from .views import *
from django.urls import path, include

urlpatterns = [
    path('index/', IndexView.as_view()),
    path('product/<str:product_id>/', ProductCodeView.as_view(), name='product')
]