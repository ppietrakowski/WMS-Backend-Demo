from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(InboundShipmentID)
admin.site.register(InboundItemInShipment)
admin.site.register(PSRCodePool)
admin.site.register(ReceiveProblemSolveCode)