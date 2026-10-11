from django.test import TestCase
from .models import * 
from .views import * 
from rest_framework.test import APITestCase
from django.urls import reverse

# Create your tests here.
class ObjectInContainerTestCase(TestCase):
    def setUp(self):
        self._startup_container_count = 5
        self._test_product_id   = 'X000000000'
        self._test_container_id = 'cs0000000000'

        self.container = Container.objects.create(id=self._test_container_id)

        for i in range(6):
            code = 'X00000000' + str(i)
            p = ProductCode.objects.create(id=code, name='Test product', weight=100)
            ObjectInContainer.objects.create(container=self.container, product=p, count=self._startup_container_count)


        Tote.objects.create(id='tsXDD0000000')

    def test_transfer_to_tote_has_ok_count(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        tote = Tote.objects.get(pk='tsXDD0000000')

        objects.transfer_to_tote(tote, 2)
        tote_objects = ObjectInContainer.objects.filter(tote=tote)
        self.assertTrue(tote_objects.exists())
        self.assertTrue(tote_objects.first().count == 2)
        self.assertTrue(objects.count == 3)


    def test_transfer_all_items_remove_objects_entry(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        tote = Tote.objects.get(pk='tsXDD0000000')
    
        objects.transfer_to_tote(tote, self._startup_container_count)
        tote_objects = ObjectInContainer.objects.filter(tote=tote)
        self.assertTrue(tote_objects.exists())
        self.assertTrue(tote_objects.first().count == self._startup_container_count)
        self.assertFalse(ObjectInContainer.objects.filter(container_id=self._test_container_id, product_id=self._test_product_id).exists())

    def test_transfer_to_tote_with_exitsting_items_doesnt_remove_rest_items(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        tote = Tote.objects.get(pk='tsXDD0000000')
            
        ObjectInContainer.objects.create(tote=tote, product_id=self._test_product_id, count=5)
        objects.transfer_to_tote(tote, 2)

        o = ObjectInContainer.objects.get(tote=tote, product_id=self._test_product_id)
        self.assertEqual(o.count, 7)

    def test_cannot_transfer_mixed_damaged_and_sellable(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        tote = Tote.objects.get(pk='tsXDD0000000')
            
        ObjectInContainer.objects.create(tote=tote, product_id=self._test_product_id, count=5, damaged=True)
        try:
            objects.transfer_to_tote(tote, 2)
            self.fail('Should not accept items with mismatched conditions to avoid weird stow issues')
        except ProductConditionMismatchError:
            pass

    def test_transfer_to_location_has_ok_count(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000, max_weight_per_product=120)
    
        objects.transfer_to_location(location, 2)
        location_objects = ObjectInContainer.objects.filter(location=location)
        self.assertTrue(location_objects.exists())
        self.assertTrue(location_objects.first().count == 2)
        self.assertTrue(objects.count == 3) 

    def test_cannot_transfer_to_location_over_max_weight_from_start(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        objects.count = 11
        objects.save()

        location = Location.objects.create(id='lo-4A100B100', max_weight=1000, max_weight_per_product=120)

        try:
            objects.transfer_to_location(location, 11)
            self.fail('Should raise WeightLimitReachedError')
        except WeightLimitReachedError:
            pass

    def test_cannot_transfer_to_location_over_max_weight_from_existing(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        objects.save()
    
        location = Location.objects.create(id='lo-4A100B100', max_weight=300,max_weight_per_product=120)
        ObjectInContainer.objects.create(location=location, product=objects.product, count=1)

        try:
            objects.transfer_to_location(location, 3)
            self.fail('Should raise WeightLimitReachedError when inserting item to location when already something is inside')
        except WeightLimitReachedError:
            pass

    def test_transfer_fails_if_reached_code_capacity(self):
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000,max_weight_per_product=120, code_capacity=5)

        try:
            for i in range(6):
                code = 'X00000000' + str(i)
                objects = ObjectInContainer.objects.get(product_id=code)
                objects.transfer_to_location(location, 1)

            self.fail('Should fail because code capacity is reached')
        except ReachedCodeCapacityError:
            pass

    def test_cannot_insert_too_heavy_product_to_location(self):
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000,max_weight_per_product=99, code_capacity=5)
        
        try:
            code = 'X000000000'
            objects = ObjectInContainer.objects.get(product_id=code)
            objects.transfer_to_location(location, 1)
    
            self.fail('Should fail because max weight per product is reached')
        except ProductTooHeavyToLocationError:
            pass


    def test_transfer_fails_if_doesnt_have_more_than_requested_products(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        tote = Tote.objects.get(pk='tsXDD0000000')

        try:
            objects.transfer_to_tote(tote, self._startup_container_count + 1)
            self.fail(f"Should fail because it has {self._startup_container_count} products, but requested {self._startup_container_count + 1}")
        except RequestedToMoveMoreThanContainError:
            pass

    def test_transfer_fail_if_trying_to_stow_sellable_item_in_damage_location(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000,max_weight_per_product=110, code_capacity=5, stores_damaged_items=True)

        try:
            objects.transfer_to_location(location, self._startup_container_count)
            self.fail('Should fail, because stowing sellable item in damage location is illegal')
        except ProductConditionMismatchError:
            pass

    def test_transfer_fail_if_trying_to_stow_damaged_item_in_sellable_location(self):
        objects = ObjectInContainer.objects.get(product_id=self._test_product_id)
        objects.damaged = True
        objects.save()
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000,max_weight_per_product=110, code_capacity=5, stores_damaged_items=False)
    
        try:
            objects.transfer_to_location(location, self._startup_container_count)
            self.fail('Should fail, because stowing damaged item in sellable location is illegal')
        except ProductConditionMismatchError:
            pass

    def test_transfer_fail_if_trying_to_stow_damaged_item_in_sellable_location(self):
        
        location = Location.objects.create(id='lo-4A100B100', max_weight=1000,max_weight_per_product=110, code_capacity=3, stores_damaged_items=False)

        ObjectInContainer.objects.create(product_id=self._test_product_id, status=ObjectInContainer.Status.Inbound, location=location, count=3)
        ObjectInContainer.objects.create(product_id=self._test_product_id, status=ObjectInContainer.Status.Reserved, location=location, count=3)
        ObjectInContainer.objects.create(product_id=self._test_product_id, status=ObjectInContainer.Status.Available, location=location, count=3)

        try:
            o = ObjectInContainer.objects.filter(container=self.container, product='X000000005', count=self._startup_container_count).first()
            o.transfer_to_location(location, 1)
        except ReachedCodeCapacityError:
            self.fail('Should add normally, as other items are some, just flagged different (for example for shipping)')
            
            
        


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
     