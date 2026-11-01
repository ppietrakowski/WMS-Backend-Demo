from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(ProductCode)
admin.site.register(ProductInContainer)
admin.site.register(StorageUnit)
admin.site.register(Dropzone)
admin.site.register(ProductCodeMapping)