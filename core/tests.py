from django.test import TestCase
from .models import * 

# Create your tests here.
class ObjectInContainerTestCase(TestCase):
    def setUp(self):
        self._startup_container_count = 5
        self._test_product_id   = 'X000000000'
        self._test_container_id = 'cs0000000000'

        container = Container.objects.create(id=self._test_container_id)

        for i in range(6):
            code = 'X00000000' + str(i)
            p = ProductCode.objects.create(id=code, name='Test product', weight=100)
            ObjectInContainer.objects.create(container=container, product=p, count=self._startup_container_count)


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
