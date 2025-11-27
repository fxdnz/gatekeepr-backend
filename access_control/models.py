from django.core.exceptions import ValidationError
from django.db import models


class Resident(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    rfid_uid = models.ForeignKey(
        'RFID',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resident_assigned'
    )
    plate_number = models.CharField(max_length=20)
    unit_number = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    parking_slot = models.ForeignKey(
        'ParkingSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resident_assigned'
    )

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Sync resident <-> RFID
        if self.rfid_uid:
            if self.rfid_uid.issued_to != self:
                self.rfid_uid.issued_to = self
                self.rfid_uid.temporary_owner = None
                self.rfid_uid.save()
        # Remove old RFID if cleared
        elif self.rfid_uid is None:
            RFID.objects.filter(issued_to=self).update(issued_to=None)

        # Sync resident <-> ParkingSlot
        if self.parking_slot:
            if self.parking_slot.issued_to != self:
                self.parking_slot.issued_to = self
                self.parking_slot.temporary_owner = None
                self.parking_slot.save()
        elif self.parking_slot is None:
            ParkingSlot.objects.filter(issued_to=self).update(issued_to=None)

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

    def save(self, *args, **kwargs):
        self.clean()
        old_instance = None
        if self.pk:
            old_instance = RFID.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)

        # Remove old resident reference if changed
        if old_instance and old_instance.issued_to and old_instance.issued_to != self.issued_to:
            if old_instance.issued_to.rfid_uid == self:
                old_instance.issued_to.rfid_uid = None
                old_instance.issued_to.save()

        # Remove old visitor reference if changed
        if old_instance and old_instance.temporary_owner and old_instance.temporary_owner != self.temporary_owner:
            if old_instance.temporary_owner.rfid == self:
                old_instance.temporary_owner.rfid = None
                old_instance.temporary_owner.save()

        # Sync current resident
        if self.issued_to:
            if self.issued_to.rfid_uid != self:
                self.issued_to.rfid_uid = self
                self.issued_to.save()

        # Sync current visitor
        if self.temporary_owner:
            if self.temporary_owner.rfid != self:
                self.temporary_owner.rfid = self
                self.temporary_owner.save()

    def __str__(self):
        owner_str = "Unassigned"
        if self.issued_to:
            owner_str = f"Resident: {self.issued_to.name}"
        elif self.temporary_owner:
            owner_str = f"Visitor: {self.temporary_owner.name}"

        temp_str = "Temporary" if self.is_temporary else "Permanent"

        return f"{self.uid} - {owner_str} - {temp_str}"


class Visitor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    drivers_license = models.CharField(max_length=50)
    address = models.CharField(max_length=255, blank=True)
    plate_number = models.CharField(max_length=20, blank=True)
    purpose = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    rfid = models.ForeignKey(
        RFID,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitors'
    )
    parking_slot = models.ForeignKey(
        'ParkingSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='visitors_temp'
    )

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        # Only temporary RFIDs
        if self.rfid and not self.rfid.is_temporary:
            raise ValidationError("Visitor can only be assigned a temporary RFID.")

        # Only free parking slots
        if self.parking_slot and self.parking_slot.type != 'FREE':
            raise ValidationError("Visitor can only be assigned a free parking slot.")

        # Ensure the RFID and parking slot are not already used
        if self.rfid and (self.rfid.temporary_owner or self.rfid.issued_to):
            raise ValidationError("This RFID is already assigned.")
        if self.parking_slot and (self.parking_slot.temporary_owner or self.parking_slot.issued_to):
            raise ValidationError("This parking slot is already assigned.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

        # Sync RFID
        if self.rfid:
            if self.rfid.temporary_owner != self:
                self.rfid.temporary_owner = self
                self.rfid.issued_to = None
                self.rfid.save()
        elif self.rfid is None:
            RFID.objects.filter(temporary_owner=self).update(temporary_owner=None)

        # Sync ParkingSlot
        if self.parking_slot:
            if self.parking_slot.temporary_owner != self:
                self.parking_slot.temporary_owner = self
                self.parking_slot.issued_to = None
                self.parking_slot.save()
        elif self.parking_slot is None:
            ParkingSlot.objects.filter(temporary_owner=self).update(temporary_owner=None)

    def __str__(self):
        return f"{self.name} - {self.purpose}"


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

        # Ensure slot is not already used
        if self.issued_to and self.temporary_owner:
            raise ValidationError("ParkingSlot cannot be assigned to both Resident and Visitor at the same time.")

    def save(self, *args, **kwargs):
        self.clean()
        old_instance = None
        if self.pk:
            old_instance = ParkingSlot.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)

        # Remove old resident
        if old_instance and old_instance.issued_to and old_instance.issued_to != self.issued_to:
            if old_instance.issued_to.parking_slot == self:
                old_instance.issued_to.parking_slot = None
                old_instance.issued_to.save()

        # Remove old visitor
        if old_instance and old_instance.temporary_owner and old_instance.temporary_owner != self.temporary_owner:
            if old_instance.temporary_owner.parking_slot == self:
                old_instance.temporary_owner.parking_slot = None
                old_instance.temporary_owner.save()

        # Sync resident
        if self.issued_to:
            if self.issued_to.parking_slot != self:
                self.issued_to.parking_slot = self
                self.issued_to.save()

        # Sync visitor
        if self.temporary_owner:
            if self.temporary_owner.parking_slot != self:
                self.temporary_owner.parking_slot = self
                self.temporary_owner.save()

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
