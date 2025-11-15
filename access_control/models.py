from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class RFIDCard(models.Model):
    """One RFID card – can belong to a resident (permanent) or a visitor (temporary)."""
    uid = models.CharField(max_length=100, unique=True)          # e.g. "A1B2C3D4"
    is_temporary = models.BooleanField(default=False)           # True → visitor card
    resident = models.OneToOneField(
        'Resident', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rfid_card'
    )
    visitor = models.OneToOneField(
        'Visitor', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='rfid_card'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # A card must be linked to exactly one of resident or visitor
        if self.resident and self.visitor:
            raise ValidationError("A card cannot belong to both a resident and a visitor.")
        if not self.resident and not self.visitor:
            raise ValidationError("A card must belong to either a resident or a visitor.")

        # Temporary flag must match the type of owner
        if self.is_temporary and self.resident:
            raise ValidationError("Resident cards cannot be temporary.")
        if not self.is_temporary and self.visitor:
            raise ValidationError("Visitor cards must be temporary.")

    def __str__(self):
        owner = self.resident.name if self.resident else (self.visitor.name if self.visitor else "—")
        return f"{self.uid} ({'temp' if self.is_temporary else 'perm'}) – {owner}"


class Resident(models.Model):
    name = models.CharField(max_length=100)
    # rfid_uid removed – now lives in RFIDCard
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

    def __str__(self):
        return f"{self.name} – {self.purpose[:20]}"


class ParkingSlot(models.Model):
    SLOT_TYPES = [
        ('OWNED', 'Owned'), ('RENTED', 'Rented'), ('PWD', 'PWD'),
        ('FREE', 'Free Parking'), ('OPEN', 'Open'),
    ]
    LOCATION_CHOICES = [
        ('BUILDING_A', 'Building A'), ('BUILDING_B', 'Building B'),
        ('BUILDING_C', 'Building C'), ('BUILDING_D', 'Building D'),
        ('BUILDING_E', 'Building E'), ('BUILDING_F', 'Building F'),
        ('BUILDING_G', 'Building G'), ('ADMIN', 'Admin'),
    ]

    slot_number = models.CharField(max_length=10, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied')],
        default='AVAILABLE'
    )
    type = models.CharField(max_length=10, choices=SLOT_TYPES, default='OPEN')
    resident = models.ForeignKey(
        Resident, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='parking_slots'
    )
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, null=True, blank=True)

    MAX_SLOTS = 78

    def clean(self):
        if not self.pk and ParkingSlot.objects.count() >= self.MAX_SLOTS:
            raise ValidationError(f"Cannot create more than {self.MAX_SLOTS} parking slots.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Slot {self.slot_number} – {self.status} – {self.get_type_display()}"


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
        return f"{self.type} – {self.action} – {self.timestamp}"