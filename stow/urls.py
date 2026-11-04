from .views import *
from django.urls import path, include

urlpatterns = [
    path('start-stow-session/', StartStowSession.as_view(), name='start-stow-session'),
    path('get-stow-session/', GetStowSession.as_view(), name='get-stow-session'),
    path('stow-get-product/', GetProductDetails.as_view(), name='stow-get-product'),
    path('stow-move-containers/', MoveStowContainers.as_view(), name='stow-move-containers'),
    path('stow-item/', StowItem.as_view(), name='stow-item'),
    path('end-stow-session/', EndStowSession.as_view(), name='end-stow-session'),
]