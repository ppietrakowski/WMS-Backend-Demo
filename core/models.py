from django.db import models
from django.core.validators import *
from django.db.models.functions import Upper
from django.db import transaction

# Create your models here.

class ProductCode(models.Model):
    id = models.CharField(max_length=10, null=False, primary_key=True)
    name = models.CharField(max_length=100)
    weight = models.IntegerField(default=10)

    def __str__(self):
        return self.id

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(weight__gt=0),
                name='weight_greater_than_zero'    
            ),
        ]


class ShipId(models.Model):
    id = models.CharField(max_length=12, primary_key=True)


class Tote(models.Model):
    """
    Starts with ts
    """
    id = models.CharField(max_length=12, primary_key=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id__startswith='ts'),
                name='id_starts_with_ts'    
            ),
        ]


class Container(models.Model):
    """
    Starts with cs
    """
    id = models.CharField(max_length=12, primary_key=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id__startswith='cs'),
                name='id_starts_with_cs'    
            ),
        ]

class Location(models.Model):
    # starts with lo
    id = models.CharField(max_length=12, primary_key=True)
    max_weight = models.IntegerField(validators=[MinValueValidator(1000)])
    max_weight_per_product = models.IntegerField(validators=[MinValueValidator(1000)])
    code_capacity = models.IntegerField(default=5)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id__startswith='lo'),
                name='id_starts_with_lo'    
            ),
            models.CheckConstraint(
                condition=models.Q(max_weight__gte=models.F('max_weight_per_product')),
                name='max_weigth_gte_max_weight_per_product'
            )
        ]


class ProductConditionMismatchError(Exception):
    pass

class WeightLimitReachedError(Exception):
    pass

class ProductTooHeavyToLocationError(Exception):
    pass

class ReachedCodeCapacityError(Exception):
    pass

class ObjectInContainer(models.Model):
    class Status(models.IntegerChoices):
        Inbound = 0
        Available = 1
        # SHIP_ID must be valid then
        Reserved = 2
        Shipped = 3

    product = models.ForeignKey(ProductCode, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status, default=Status.Inbound)
    count = models.IntegerField(default=1)

    tote = models.ForeignKey(Tote, blank=True, null=True, default=None, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, blank=True, null=True, default=None,on_delete=models.CASCADE)
    container = models.ForeignKey(Container, blank=True, null=True, default=None,on_delete=models.CASCADE)

    ship = models.ForeignKey(ShipId, blank=True, null=True, default=None,on_delete=models.CASCADE)
    damaged = models.BooleanField(default=False)

    def transfer_to_tote(self, tote: Tote, count: int):
        self._transfer_to_new_container(count, tote=tote)

    def transfer_to_container(self, container: Container, count: int):
        self._transfer_to_new_container(count, container=container)

    def transfer_to_location(self, location: Location, count: int):
        objects = ObjectInContainer.objects.filter(product=self.product, 
                                                           location=location)
        objects_in_location = ObjectInContainer.objects.filter(location=location)
        self._run_location_checks(location, count, objects_in_location)

        with transaction.atomic():
            self._transactioned_move_objects_to_location(location=location, count=count, objects=objects, objects_in_location=objects_in_location)

    def _transfer_to_new_container(self, count, **find_container_kwargs):
        objects = ObjectInContainer.objects.filter(product=self.product, 
                                                   **find_container_kwargs)
        with transaction.atomic():
            if not objects.exists():
                self._create_new_container_with_objects(count, **find_container_kwargs)
            else:
                self._transfer_to_existing_tote(count, tote_objects=objects.first())

            self._transfer_out_self(count)

    def _run_location_checks(self, location, count, objects_in_location):
        transfered_items_weight = count * self.product.weight
        weights = [i.count * i.product.weight for i in objects_in_location]
        current_products_weight = sum(weights)

        if transfered_items_weight + current_products_weight > location.max_weight:
            raise WeightLimitReachedError()

        if self.product.weight > location.max_weight_per_product:
            raise ProductTooHeavyToLocationError()

    def _transactioned_move_objects_to_location(self, **kwargs):
        location = kwargs['location']
        count = kwargs['count']
        objects = kwargs['objects']
        objects_in_location = kwargs['objects_in_location']

        if not objects.exists():
            if len(objects_in_location) == location.code_capacity:
                raise ReachedCodeCapacityError()

            # now len(objects_in_location) += 1 
            self._create_new_container_with_objects(count, location=location)

        self._transfer_out_self(count)
    
    def _create_new_container_with_objects(self, count, **kwargs):
        ObjectInContainer.objects.create(product=self.product, count=count, **kwargs)

    def _transfer_out_self(self, count):
        self.count -= count

        if self.count > 0:
            self.save()
        else:
            self.delete()

    def _transfer_to_existing_tote(self, count, tote_objects):
        if tote_objects.damaged != self.damaged:
            raise ProductConditionMismatchError()
            
        tote_objects.count += count
        tote_objects.save()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(count__gte=0),
                name='count_at_least_zero'
            )
        ]

class ReceiveShipment(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    # cheat container system to better transfer data between containers
    container = models.ForeignKey(Container, on_delete=models.CASCADE)