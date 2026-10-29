from django.test import TestCase
from .views import *
from .models import * 
from rest_framework.test import APITestCase
from django.urls import reverse

# Create your tests here.
class GetReceiveShipmentProductsTest(APITestCase):
    def setUp(self):
        return super().setUp()

    def test_fails_when_no_ship_id_passed(self):
        #self.client.get(reverse(self._product_page, 
            #kwargs={'product_id': 'X000000000'}))
        response = self.client.post(reverse('get_receive_products'))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_fails_when_invalid_ship_id_passed(self):
        #self.client.get(reverse(self._product_page, 
            #kwargs={'product_id': 'X000000000'}))
        response = self.client.post(reverse('get_receive_products'), {
            'ship_id': 'sz1234567891'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)