from django.test import TestCase
from .views import *
from .models import * 
from rest_framework.test import APITestCase
from django.urls import reverse
import json

# Create your tests here.
class GetReceiveShipmentProductsTest(APITestCase):
    def setUp(self):
        self.ship = InboundShipmentID.objects.create(id='sz1234567892', date_issued='2026-10-29')
        self.p = ProductCode.objects.create(id='X123456789', name='test product')


        c = StorageUnit.objects.create(id=self.ship.id)
        ProductInContainer.objects.create(container=c, product=self.p)

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
            'ship_id': self.ship.id
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data['message'])
        result = response.json()
        products = ReceiveItemSerializer(data=result['products'], many=True)
        self.assertTrue(products.is_valid())
        self.assertEqual(len(products.validated_data), 1)
        self.assertEqual(products.validated_data[0]['code'], 'X123456789')


class GetToteHasSameModifierAsProductTestCase(APITestCase):
    def setUp(self):
        self.page = 'has_container_same_damage_flag_as_next_product'
        self.tote = StorageUnit.objects.create(id='tsXDD678912')
        self.product = ProductCode.objects.create(id='X123456789', name='test product')
        return super().setUp()

    def test_for_empty_tote_gives_always_true(self):
        response = self.client.post(reverse(self.page), data={
            'tote_id': self.tote.id,
            'damaged': False, 
        }, content_type='application/json')
        self.assertEqual(response.data, True)

        response = self.client.post(reverse(self.page), data={
                    'tote_id': self.tote.id,
                    'damaged': True, 
                }, content_type='application/json')
        self.assertEqual(response.data, True)


    def test_for_sellable_returns_true(self):
        ProductInContainer.objects.create(container=self.tote, product=self.product)

        response = self.client.post(reverse(self.page), data={
            'tote_id': self.tote.id,
            'damaged': False,  
        }, content_type='application/json')
    
        self.assertEqual(response.data, True)

    def test_for_damage_returns_false(self):
        ProductInContainer.objects.create(container=self.tote, product=self.product,damaged=True)
    
        response = self.client.post(reverse(self.page), data={
            'tote_id': self.tote.id,
            'damaged': False,
        }, content_type='application/json')
    
        self.assertEqual(response.data, False)