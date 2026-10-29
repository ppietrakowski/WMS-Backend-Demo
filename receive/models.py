from django.db import models
from core.models import ProductCode
from django.contrib.auth.models import User

# Create your models here.
class InboundShipmentID(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    date_issued = models.DateField()


class InboundItemInShipment(models.Model):
    ship = models.ForeignKey(InboundShipmentID, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductCode, on_delete=models.CASCADE)
    available_count = models.IntegerField(default=1)
    # should be at start same as available_count
    total_count = models.IntegerField(default=1)
    damaged = models.BooleanField(default=False)


class ReceiveProblemSolveCode(models.Model):
    psr = models.CharField(max_length=12, primary_key=True)
    ship = models.ForeignKey(InboundShipmentID, on_delete=models.CASCADE)
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE)


class PSRCodePool(models.Model):
    psr = models.CharField(max_length=12, primary_key=True)