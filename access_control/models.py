from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

class Resident(models.Model):
    # REMOVED foreign keys to RFID and ParkingSlot
    # These were causing circular references
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    plate_number = models.CharField(max_length=20)
    unit_number = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.name} (Apt {self.unit_number})"


class RFID(models.Model):
    uid = models.CharField(max_length=100, unique=True)
    issued_to = models.ForeignKey(
        Resident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfids'
    )
    temporary_owner = models.ForeignKey(
        'Visitor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rfids_temp'
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    is_temporary = models.BooleanField(default=False)

    def clean(self):
        # Ensure temporary RFID is only assigned to visitors
        if self.temporary_owner and not self.is_temporary:
            raise ValidationError("Only temporary RFID can be assigned to visitors.")
        
        # Ensure a RFID is not assigned to both resident and visitor
        if self.issued_to and self.temporary_owner:
            raise ValidationError("RFID cannot be assigned to both Resident and Visitor at the same time.")
        
        # Ensure temporary RFID is not assigned to a resident
        if self.is_temporary and self.issued_to:
            raise ValidationError("Temporary RFID cannot be assigned to residents.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        owner_str = "Unassigned"
        if self.issued_to:
            owner_str = f"Resident: {self.issued_to.name}"
        elif self.temporary_owner:
            owner_str = f"Visitor: {self.temporary_owner.name}"

        temp_str = "Temporary" if self.is_temporary else "Permanent"

        return f"{self.uid} - {owner_str} - {temp_str}"


class Visitor(models.Model):
    # REMOVED foreign keys to RFID and ParkingSlot
    # These were causing circular references
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    drivers_license = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Visitor checkout tracking
    signed_out = models.BooleanField(null=True, blank=True, default=False)
    signed_out_at = models.DateTimeField(null=True, blank=True)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        # Auto-set signed_out_at when signed_out is True
        if self.signed_out and not self.signed_out_at:
            self.signed_out_at = timezone.now()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = " (Signed Out)" if self.signed_out else ""
        return f"{self.name} - {self.purpose}{status}"


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
    status = models.CharField(
        max_length=10,
        choices=[('AVAILABLE', 'Available'), ('OCCUPIED', 'Occupied')],
        default='AVAILABLE'
    )
    type = models.CharField(max_length=10, choices=SLOT_TYPES, default='OPEN')
    issued_to = models.ForeignKey(
        Resident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parking_slots'
    )
    temporary_owner = models.ForeignKey(
        Visitor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parking_temp'
    )
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, null=True, blank=True)

    MAX_SLOTS = 78

    def clean(self):
        if not self.pk and ParkingSlot.objects.count() >= self.MAX_SLOTS:
            raise ValidationError(f"Cannot create more than {self.MAX_SLOTS} parking slots.")
        
        # Only free slots for temporary assignment
        if self.temporary_owner and self.type != 'FREE':
            raise ValidationError("Visitor can only be assigned a free parking slot.")
        
        # Ensure slot is not assigned to both resident and visitor
        if self.issued_to and self.temporary_owner:
            raise ValidationError("ParkingSlot cannot be assigned to both Resident and Visitor at the same time.")
        
        # Ensure free slots are not assigned to residents
        if self.type == 'FREE' and self.issued_to:
            raise ValidationError("Free parking slots cannot be assigned to residents.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        owner_str = "Unassigned"
        if self.issued_to:
            owner_str = f"Resident: {self.issued_to.name}"
        elif self.temporary_owner:
            owner_str = f"Visitor: {self.temporary_owner.name}"

        return f"Slot {self.slot_number} - {self.status} - {self.type} - {owner_str}"


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