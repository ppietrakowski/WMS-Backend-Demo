from .views import *
from django.urls import path, include

urlpatterns = [
    path('get_receive_products/', GetReceiveShipmentProducts.as_view(), name='get_receive_products'),
    path('has_container_same_damage_flag_as_next_product', GetToteHasSameModifierAsProduct.as_view(), name='has_container_same_damage_flag_as_next_product'),
    path('receive/ps-raise', ReceiveProblemSolveRaise.as_view(), name='problem_solve_raise'),
    path('get-product/<str:product_id>/', GetProductByCode.as_view(), name='get_product')
]