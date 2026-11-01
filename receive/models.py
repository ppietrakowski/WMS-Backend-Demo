from django.db import models
from core.models import ProductCode, StorageUnit
from django.contrib.auth.models import User

# Create your models here.
class InboundShipmentID(models.Model):
    id = models.CharField(max_length=12, primary_key=True)
    date_issued = models.DateField()



class ReceiveProblemSolveCode(models.Model):
    class Reason(models.IntegerChoices):
        DAMAGED = 0
        DAMAGED_CODE = 1
        OVERFLOW = 2

    psr = models.CharField(max_length=12, primary_key=True)
    ship = models.ForeignKey(InboundShipmentID, on_delete=models.CASCADE)
    by_whom = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.IntegerField(choices=Reason, default=Reason.DAMAGED)


class PSRCodePool(models.Model):
    psr = models.CharField(max_length=12, primary_key=True)