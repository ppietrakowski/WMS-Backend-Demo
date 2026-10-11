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
    stores_damaged_items = models.BooleanField(default=False)

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

class RequestedToMoveMoreThanContainError(Exception):
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
        objects_in_location = ObjectInContainer.objects.filter(location=location)
        
        self._run_location_checks(location, count, objects_in_location)

        if count > self.count:
            raise RequestedToMoveMoreThanContainError()

        if location.stores_damaged_items != self.damaged:
            raise ProductConditionMismatchError()
        
        with transaction.atomic():
            objects, created = ObjectInContainer.objects.get_or_create(
                            product = self.product,
                            location=location,
                            status=ObjectInContainer.Status.Available,
                            defaults={'count': count}
                        )
                        
            if not created:
                if objects.damaged != self.damaged:
                    raise ProductConditionMismatchError()
                objects.count += count
                objects.save()
            else:
                already_checked_products = []
                num_products = 0
                for i in objects_in_location:
                    if i.product.id not in already_checked_products:
                        num_products += 1
                        already_checked_products.append(i.product.id)

                if num_products == location.code_capacity:
                    # after this raise, db will revert back to state before 'with' block
                    raise ReachedCodeCapacityError()
                
            self._transfer_out_self(count)

    def _transfer_to_new_container(self, count, **find_container_kwargs):
        if count > self.count:
            raise RequestedToMoveMoreThanContainError()
        
        with transaction.atomic():
            objects, created = ObjectInContainer.objects.get_or_create(
                product = self.product,
                **find_container_kwargs,
                defaults={'count': count}
            )

            if not created:
                if objects.damaged != self.damaged:
                    raise ProductConditionMismatchError()
                objects.count += count
                objects.save()

            self._transfer_out_self(count)

    def _run_location_checks(self, location, count, objects_in_location):
        transfered_items_weight = count * self.product.weight
        weights = [i.count * i.product.weight for i in objects_in_location]
        current_products_weight = sum(weights)

        if transfered_items_weight + current_products_weight > location.max_weight:
            raise WeightLimitReachedError()

        if self.product.weight > location.max_weight_per_product:
            raise ProductTooHeavyToLocationError()

    def _transfer_out_self(self, count):
        self.count -= count

        if self.count > 0:
            self.save()
        else:
            self.delete()

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