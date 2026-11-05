from .views import *
from django.urls import path, include

urlpatterns = [
    path('container/move-product/', MoveProductToNewContainer.as_view(), name='move_container_products'),
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh_view'),
    path('logout/', CookieLogoutView.as_view(), name='logout'),
    path('authuser/', CurrentUserView.as_view(), name='authuser'),
    path('move-dropzone/', MoveDropzone.as_view(), name='move_dropzone'),
    path('add-items-container/', AddItemsContainer.as_view(), name='add-items-container'),
    path('get-container-products/', ContainerProducts.as_view(), name='get_receive_products'),
]