from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# ---------------------------
# RFID Tag Model
# ---------------------------
class RFIDTag(models.Model):
    uid = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    issued_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.uid} ({'Active' if self.is_active else 'Inactive'})"


# ---------------------------
# Resident Model
# ---------------------------
class Resident(models.Model):
    name = models.CharField(max_length=100)
    rfid_tag = models.ForeignKey(
        RFIDTag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residents"
    )
    plate_number = models.CharField(max_length=20)
    unit_number = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    parking_slot = models.ForeignKey(
        'ParkingSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='residents_parking_slot'  # Add a related_name here to avoid reverse name clash
    )

    def __str__(self):
        return f"{self.name} (Apt {self.unit_number})"


# ---------------------------
# Visitor Model
# ---------------------------
class Visitor(models.Model):
    name = models.CharField(max_length=100)
    drivers_license = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.drivers_license}"


# ---------------------------
# Parking Slot Model
# ---------------------------
class ParkingSlot(models.Model):
    SLOT_TYPES = [
        ('OWNED', 'Owned'),
        ('RENTED', 'Rented'),
        ('PWD', 'PWD'),
        ('FREE', 'Free Parking'),
        ('OPEN', 'Open'),
    ]

    LOCATION_CHOICES = [
        ('BUILDING_A', 'Building A'),
        ('BUILDING_B', 'Building B'),
        ('BUILDING_C', 'Building C'),
        ('BUILDING_D', 'Building D'),
        ('BUILDING_E', 'Building E'),
        ('BUILDING_F', 'Building F'),
        ('BUILDING_G', 'Building G'),
        ('ADMIN', 'Admin'),
    ]

    slot_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied')])
    type = models.CharField(max_length=10, choices=SLOT_TYPES, default='OPEN')
    resident = models.ForeignKey('Resident', on_delete=models.SET_NULL, null=True, blank=True, related_name="parking_slot_reverse")  # Add related_name here
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, null=True, blank=True)

    MAX_SLOTS = 78  # Limit to 78 slots for Familia Apartments

    def clean(self):
        if not self.pk and ParkingSlot.objects.count() >= self.MAX_SLOTS:
            raise ValidationError(f"Cannot create more than {self.MAX_SLOTS} parking slots.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Slot No: {self.slot_number} - {self.status} - {self.get_type_display()}"


# ---------------------------
# Access Log Model
# ---------------------------
class AccessLog(models.Model):
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'
    ACTIONS = [
        (ENTRY, 'Entry'),
        (EXIT, 'Exit'),
    ]

    RESIDENT = 'RESIDENT'
    VISITOR = 'VISITOR'
    TYPES = [
        (RESIDENT, 'Resident'),
        (VISITOR, 'Visitor'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=10, choices=ACTIONS)
    type = models.CharField(max_length=10, choices=TYPES)
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True)
    visitor_log = models.ForeignKey(Visitor, on_delete=models.SET_NULL, null=True, blank=True)
    parking = models.ForeignKey(ParkingSlot, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.type} - {self.action} - {self.timestamp}"
