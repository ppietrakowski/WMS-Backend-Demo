from django.db import models
from django.db import models
from core.models import ProductCode, StorageUnit
from django.contrib.auth.models import User

# Create your models here.

class StowSessionContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    container = models.ForeignKey(StorageUnit, on_delete=models.CASCADE)

