from django.test import TestCase
from .models import * 
from .views import * 
from rest_framework.test import APITestCase
from django.urls import reverse
        
            
class MoveEndpointTestCase(APITestCase):
    def setUp(self):
        self.base_container = StorageUnit.objects.create(id='tsXDD0000000')
        self.destination_container = StorageUnit.objects.create(id='tsXDD0000001')
        ProductCode.objects.create(id='X000000002', name='Test-Product', weight=100)
        self.objects = ProductInContainer.objects.create(product_id='X000000002', container=self.base_container, count=3)
        self._product_page = 'move_container_products'

        return super().setUp()

    def test_cannot_move_unexisting_item(self):
        response = self.client.post(reverse('move_container_products'), 
                        data = {
                            'source_container': self.base_container.id,
                            'destination_container': self.destination_container.id,
                            'product': 'X000000003',
                            'count': 3,
                        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_moves_existing_item(self):
        response = self.client.post(reverse('move_container_products'), 
                        data = {
                            'source_container': self.base_container.id,
                            'destination_container': self.destination_container.id,
                            'product': 'X000000002',
                            'count': 3,
                        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProductInContainer.objects.get(container=self.destination_container, product='X000000002').count, 3)
        self.assertFalse(ProductInContainer.objects.filter(container=self.base_container).exists())

    def test_fails_to_move_when_reached_weight_limit(self):
        self.destination_container.max_weight=300
        self.destination_container.save()
        ProductInContainer.objects.create(container=self.destination_container, product_id='X000000002', count=2)

        response = self.client.post(reverse('move_container_products'), 
                        data = {
                            'source_container': self.base_container.id,
                            'destination_container': self.destination_container.id,
                            'product': 'X000000002',
                            'count': 3,
                        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fails_to_move_when_reached_weight_limit_per_product(self):
        self.destination_container.max_weight_per_product=50
        self.destination_container.save()
        ProductInContainer.objects.create(container=self.destination_container,product_id='X000000002', count=2)
    
        response = self.client.post(reverse('move_container_products'), 
                        data = {
                            'source_container': self.base_container.id,
                            'destination_container': self.destination_container.id,
                            'product': 'X000000002',
                            'count': 3,
                        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fails_to_move_when_reached_code_limit(self):
        self.destination_container.code_capacity = 1
        self.destination_container.save()
        ProductInContainer.objects.create(container=self.destination_container, product_id='X000000002', count=2)
        ProductInContainer.objects.create(container=self.base_container, product_id='X000000003', count=3)
        ProductCode.objects.create(id='X000000003', name='Test-Product', weight=100)
        
        response = self.client.post(reverse('move_container_products'), 
                        data = {
                            'source_container': self.base_container.id,
                            'destination_container': self.destination_container.id,
                            'product': 'X000000003',
                            'count': 3,
                        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)