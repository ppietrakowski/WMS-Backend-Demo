from django.test import TestCase
from .views import *
from .models import * 
from rest_framework.test import APITestCase
from django.urls import reverse

# Create your tests here.
class GetReceiveShipmentProductsTest(APITestCase):
    def setUp(self):

        ship_id = InboundShipmentID.objects.create(id='sz1234567892', date_issued='2026-10-29')
        p = ProductCode.objects.create(id='X123456789', name='test product')
        InboundItemInShipment.objects.create(ship = ship_id, product = p, available_count=3, total_count=3)

        return super().setUp()

    def test_fails_when_no_ship_id_passed(self):
        response = self.client.post(reverse('get_receive_products'))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_fails_when_invalid_ship_id_passed(self):
        response = self.client.post(reverse('get_receive_products'), {
            'ship_id': 'sz1234567891'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_valid_product_in_shipment(self):
        response = self.client.post(reverse('get_receive_products'), {
            'ship_id': 'sz1234567892'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        products = ReceiveItemSerializer(data=result['products'], many=True)
        self.assertTrue(products.is_valid())
        self.assertEqual(len(products.validated_data), 1)
        self.assertEqual(products.validated_data[0]['code'], 'X123456789')

    def test_returns_valid_collection_of_products_in_shipment(self):
        p = ProductCode.objects.create(id='X123456781', name='test product')
        InboundItemInShipment.objects.create(ship_id = 'sz1234567892', product = p,available_count=3, total_count=3)
        response = self.client.post(reverse('get_receive_products'), {
            'ship_id': 'sz1234567892'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        products = ReceiveItemSerializer(data=result['products'], many=True)
        self.assertTrue(products.is_valid())
        self.assertEqual(len(products.validated_data), 2)
        data = products.validated_data
        self.assertEqual(data[0]['code'], 'X123456789')
        self.assertEqual(data[1]['code'], 'X123456781')

