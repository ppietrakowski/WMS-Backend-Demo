from .views import *
from django.urls import path, include

urlpatterns = [
    path('index/', IndexView.as_view())
]