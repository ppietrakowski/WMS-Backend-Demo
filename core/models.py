from django.db import models
from django.core.validators import *
from django.db.models.functions import Upper
from django.db import transaction
from django.contrib.auth.models import User

# Create your models here.

class ProductCode(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition = models.Q(weight__gt=0),
                name = 'weight_greater_than_zero'    
            ),
        ]

    id = models.CharField(max_length = 10, null = False, primary_key = True)
    name = models.CharField(max_length = 100)
    weight = models.IntegerField(default = 10)

    def __str__(self):
        return f'{self.name}[{self.id}]'


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


class Dropzone(models.Model):
    id = models.CharField(max_length=12, primary_key=True)


class StorageUnit(models.Model):
    id = models.CharField(max_length=12, primary_key=True)

    max_weight = models.IntegerField(default=0)
    max_weight_per_product = models.IntegerField(default=0)
    code_capacity = models.IntegerField(default = 0)
    stores_damaged_items = models.BooleanField(default = False)
    blocked = models.BooleanField(default=False)
    dropzone = models.ForeignKey(Dropzone, on_delete=models.CASCADE, null=True, blank=True)

    location_x = models.IntegerField(default=1)
    location_y = models.IntegerField(default=1)
    floor = models.IntegerField(default=1)

    def can_stow_items(self, is_product_damaged: bool):
        return is_product_damaged != self.stores_damaged_items

    def has_reached_sku_limit(self):
        current_items_count = self.items.count()
        return (current_items_count >= self.code_capacity) if self.code_capacity > 0 else False

    def can_store_product_weight(self, product_weight: int):
        if self.max_weight_per_product > 0:
            if product_weight > self.max_weight_per_product:
                return False

        return True

    def can_store_weight(self, weight):
        if not self.can_store_product_weight(weight):
            return False
         
        current_weight = 0
        for i in self.items.all():
            current_weight += i.product.weight * i.count

        return (weight + current_weight) <= self.max_weight if self.max_weight > 0 else True
    

class ProductInContainer(models.Model):
    container = models.ForeignKey(StorageUnit, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(ProductCode, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    damaged = models.BooleanField(default=False)

    def move_to_container(self, to: StorageUnit, count: int):
        if self.count < count:
            raise RequestedToMoveMoreThanContainError()
       
        if to.has_reached_sku_limit():
            raise ReachedCodeCapacityError()

        if to.can_store_product_weight(count * self.product.weight):
            raise ProductTooHeavyToLocationError()
    
        if not to.can_store_weight(count * self.product.weight):
            raise WeightLimitReachedError()
    
        with transaction.atomic():
            self._try_move_to_location(to, count)

    def _try_move_to_location(self, to: StorageUnit, count: int):
        try:
            p = ProductInContainer.objects.get(container=to,product=self.product)
            p.count += count
            p.save()
        except ProductInContainer.DoesNotExist:
            ProductInContainer.objects.create(product_id=self.product, count=count, status=self.status, damaged=self.damaged, container_id=to)
        
        self.count -= count
        if self.count <= 0:
            self.delete()
        else:
            self.save()


class ProductCodeMapping(models.Model):
    product = models.ForeignKey(ProductCode, on_delete=models.CASCADE)
    code = models.CharField(max_length=13)


class DropzoneTime(models.Model):
    time = models.DateTimeField()
    container = models.ForeignKey(StorageUnit, on_delete=models.CASCADE)