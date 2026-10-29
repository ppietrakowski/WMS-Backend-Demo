from .views import *
from django.urls import path, include

urlpatterns = [
    path('index/', IndexView.as_view()),
    path('product/<str:product_id>/', ProductCodeView.as_view(), name='product'),
    path('container_items/<str:container_id>/', ContainerItemsView.as_view(), name='container_items'),
    path('container_items/<str:container_id>/add-item/', AddItemToContainerView.as_view(), name='add_container_items'),
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh_view'),
    path('logout/', CookieLogoutView.as_view(), name='logout'),
    path('authuser/', CurrentUserView.as_view(), name='authuser'),
]