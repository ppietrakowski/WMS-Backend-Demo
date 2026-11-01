from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(ProductCode)
admin.site.register(Tote)
admin.site.register(Location)
admin.site.register(Container)
admin.site.register(ObjectInContainer)
admin.site.register(ShipId)
admin.site.register(ProductInContainer)
admin.site.register(StorageUnit)