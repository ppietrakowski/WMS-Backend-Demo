from django.test import TestCase
from .models import * 
from .views import * 
from rest_framework.test import APITestCase
from django.urls import reverse
        
class MoveDropzoneTestCase(APITestCase):
    def setUp(self):
        container = StorageUnit.objects.create(id='tsTest000000')
        self.containers = [container.id]
        self.valid_dropzone = Dropzone.objects.create(id='dz-P1-Trans1')

    def test_fails_when_dropzone_does_not_exist(self):
        try:
            response = self.client.post(reverse('move-dropzone'), data = {
                'containers': self.containers,
                'dropzone': 'dz-P1-Trans2'
            })

            self.assertNotEqual(response.status_code, status.HTTP_200_OK)
        except Dropzone.DoesNotExist:
            self.fail('Should not raise internal server error')


class AddContainerItemTestCase(APITestCase):
    def setUp(self):
        self._page = 'add-items-container'
        self._valid_container = StorageUnit.objects.create(id='tsDMGabcXYZ0')

    def test_creates_container_when_noexistent(self):
        response = self.client.put(reverse(self._page), data = {
            'products': [],
            'container': 'tsDMGabcXYZ1'
        })

        self.assertEqual(response.status, status.HTTP_200_OK)

    def test_returns_fail_reason_when_provide_unexisting_product_code(self):
        response = self.client.put(reverse(self._page), data = {
            'products': [{'product': 'X00123456789', 'count': 1}],
            'container': self._valid_container.id,
        })

        self.assertEqual(response.status, status.HTTP_400_FORBIDDEN)
        self.assertEqual(response.data['reason'], 'invalid-product-code')


