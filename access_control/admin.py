from django.contrib import admin
from .models import Resident, Visitor, AccessLog, ParkingSlot, RFIDTag

admin.site.register(Resident)
admin.site.register(Visitor)
admin.site.register(AccessLog)
admin.site.register(ParkingSlot)
admin.site.register(RFIDTag)