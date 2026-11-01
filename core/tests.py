from django.test import TestCase
from .models import * 
from .views import * 
from rest_framework.test import APITestCase
from django.urls import reverse
            
class ProductViewTest(APITestCase):
    def setUp(self):
        ProductCode.objects.create(id='X000000001', name='Test-Product', weight=100)
        self._product_page = 'product'

    def test_raises_error_when_empty_product_id(self):
        response = self.client.get(reverse(self._product_page, 
            kwargs={'product_id': 'X000000000'}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_raises_error_when_retrieving_not_existing_product(self):
        response = self.client.get(reverse(self._product_page, 
            kwargs={'product_id': 'X000000000'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_object_when_passing_valid_code(self):
        response = self.client.get(reverse(self._product_page, 
            kwargs={'product_id': 'X000000001'}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['id'], 'X000000001')
        self.assertEqual(response_data['name'], 'Test-Product')


class ContainerItemViewTestCase(APITestCase):
    def setUp(self):
        self.product = ProductCode.objects.create(id='X000000001', name='Test-Product', weight=100)
        ProductCode.objects.create(id='X000000002', name='Test-Product', weight=100)
        self.tote = Tote.objects.create(id='ts00000000100')
        self._product_page = 'container_items'
        return super().setUp()

    def test_raises_error_when_empty_product_id(self):
        response = self.client.get(reverse(self._product_page, 
            kwargs={'container_id': self.tote.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_tote_objects(self):
        ObjectInContainer.objects.create(tote=self.tote, product=self.product)
        ObjectInContainer.objects.create(tote=self.tote, product_id='X000000002', count=3)
        response = self.client.get(reverse(self._product_page, 
            kwargs={'container_id': self.tote.id}))

        result = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['container'], self.tote.id)

        products = [i['product'] for i in result['products']]
        self.assertTrue('X000000002' in products)
        self.assertTrue('X000000001' in products)

    def test_add_item_endpoints_validates_data(self):
        response = self.client.post(reverse('add_container_items', 
                    kwargs={'container_id': self.tote.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_item_endpoint_adds_item_to_location(self):
        response = self.client.post(reverse('add_container_items', 
                    kwargs={'container_id': self.tote.id}), data = {
                        'product': self.product.id,
                        'count': 4,
                        'damaged': True,
                    })

        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
            
    def test_add_item_endpoint_cannot_mismatch_damaged_item_with_sellable(self):
        ObjectInContainer.objects.create(tote=self.tote, product=self.product)
        response = self.client.post(reverse('add_container_items', 
                        kwargs={'container_id': self.tote.id}), data = {
                            'product': self.product.id,
                            'count': 4,
                            'damaged': True,
                        })
    
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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