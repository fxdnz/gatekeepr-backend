from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Resident(models.Model):
    name = models.CharField(max_length=100)
    rfid_uid = models.CharField(max_length=100, unique=True)
    plate_number = models.CharField(max_length=20)
    unit_number = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name} (Apt {self.unit_number})"

class Visitor(models.Model):
    name = models.CharField(max_length=100)
    drivers_license = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk  # Check if this is a new creation
        super().save(*args, **kwargs)
        
        if is_new:
            AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=self,
            )

class ParkingSlot(models.Model):
    slot_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied')])
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Slot No: {self.slot_number} - {self.status}"

class AccessLog(models.Model):
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'
    ACTIONS = [(ENTRY, 'Entry'), (EXIT, 'Exit')]

    RESIDENT = 'RESIDENT'
    VISITOR = 'VISITOR'
    TYPES = [(RESIDENT, 'Resident'), (VISITOR, 'Visitor')]

    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    type = models.CharField(max_length=10, choices=TYPES)
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True)
    visitor_log = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, blank=True)
    parking = models.ForeignKey(ParkingSlot, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.action} - {self.timestamp}"