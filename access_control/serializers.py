from rest_framework import serializers
from .models import Resident, Visitor, RFID, ParkingSlot, AccessLog

# -------------------
# Resident Serializer
# -------------------
class ResidentSerializer(serializers.ModelSerializer):
    rfid_uid_display = serializers.SerializerMethodField()
    rfid_id = serializers.SerializerMethodField()  # NEW: RFID ID
    name = serializers.SerializerMethodField()
    parking_slot_display = serializers.SerializerMethodField()
    parking_slot_id = serializers.SerializerMethodField()  # NEW: Parking Slot ID
    parking_slot_type = serializers.SerializerMethodField()
    
    # Fields for assigning RFID and parking slot (write-only)
    rfid_uid = serializers.PrimaryKeyRelatedField(
        queryset=RFID.objects.filter(is_temporary=False, active=True),
        required=False,
        allow_null=True,
        write_only=True
    )
    parking_slot = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSlot.objects.exclude(type='FREE'),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Resident
        fields = [
            'id', 'first_name', 'last_name', 'name', 'plate_number', 'unit_number', 'phone', 
            'rfid_uid', 'rfid_uid_display', 'rfid_id',  # Include rfid_id
            'parking_slot', 'parking_slot_display', 'parking_slot_id', 'parking_slot_type'
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_rfid_uid_display(self, obj):
        # Get RFID assigned to this resident
        rfid = RFID.objects.filter(issued_to=obj).first()
        return rfid.uid if rfid else "N/A"
    
    def get_rfid_id(self, obj):
        # Get RFID ID assigned to this resident
        rfid = RFID.objects.filter(issued_to=obj).first()
        return rfid.id if rfid else None
    
    def get_parking_slot_display(self, obj):
        # Get parking slot assigned to this resident
        parking = ParkingSlot.objects.filter(issued_to=obj).first()
        return parking.slot_number if parking else "N/A"
    
    def get_parking_slot_id(self, obj):
        # Get parking slot ID assigned to this resident
        parking = ParkingSlot.objects.filter(issued_to=obj).first()
        return parking.id if parking else None
    
    def get_parking_slot_type(self, obj):
        # Get parking slot type assigned to this resident
        parking = ParkingSlot.objects.filter(issued_to=obj).first()
        return parking.type if parking else "N/A"

    def validate(self, data):
        rfid = data.get('rfid_uid')
        parking = data.get('parking_slot')
        
        # Validate RFID
        if rfid is not None:
            if rfid.is_temporary:
                raise serializers.ValidationError({
                    'rfid_uid': ["Only permanent RFID can be assigned to residents."]
                })
            
            if rfid.issued_to and rfid.issued_to.id != (self.instance.id if self.instance else None):
                raise serializers.ValidationError({
                    'rfid_uid': ["This RFID is already assigned to another resident."]
                })
        
        # Validate parking slot
        if parking is not None:
            if parking.type == 'FREE':
                raise serializers.ValidationError({
                    'parking_slot': ["Free parking slots cannot be assigned to residents."]
                })
            
            if parking.issued_to and parking.issued_to.id != (self.instance.id if self.instance else None):
                raise serializers.ValidationError({
                    'parking_slot': ["This parking slot is already assigned to another resident."]
                })
        
        return data

    def create(self, validated_data):
        rfid = validated_data.pop('rfid_uid', None)
        parking = validated_data.pop('parking_slot', None)
        
        resident = Resident.objects.create(**validated_data)
        
        # Assign RFID if provided
        if rfid:
            rfid.issued_to = resident
            rfid.save()
        
        # Assign parking slot if provided
        if parking:
            parking.issued_to = resident
            parking.status = 'OCCUPIED'
            parking.save()
        
        return resident
    
    def update(self, instance, validated_data):
        # Get current assignments
        old_rfid = RFID.objects.filter(issued_to=instance).first()
        old_parking = ParkingSlot.objects.filter(issued_to=instance).first()
        
        new_rfid = validated_data.pop('rfid_uid', None)
        new_parking = validated_data.pop('parking_slot', None)
        
        # Update resident fields
        instance = super().update(instance, validated_data)
        
        # Handle RFID changes
        if old_rfid and new_rfid is None:
            old_rfid.issued_to = None
            old_rfid.save()
        elif new_rfid and new_rfid != old_rfid:
            if old_rfid:
                old_rfid.issued_to = None
                old_rfid.save()
            
            new_rfid.issued_to = instance
            new_rfid.save()
        
        # Handle parking slot changes
        if old_parking and new_parking is None:
            old_parking.issued_to = None
            old_parking.status = 'AVAILABLE'
            old_parking.save()
        elif new_parking and new_parking != old_parking:
            if old_parking:
                old_parking.issued_to = None
                old_parking.status = 'AVAILABLE'
                old_parking.save()
            
            new_parking.issued_to = instance
            new_parking.status = 'OCCUPIED'
            new_parking.save()
        
        return instance


# -------------------
# RFID Serializer
# -------------------
class RFIDSerializer(serializers.ModelSerializer):
    issued_to_details = serializers.SerializerMethodField()
    temporary_owner_details = serializers.SerializerMethodField()

    class Meta:
        model = RFID
        fields = '__all__'

    def get_issued_to_details(self, obj):
        if obj.issued_to:
            return {
                'id': obj.issued_to.id,
                'name': obj.issued_to.name,
                'first_name': obj.issued_to.first_name,
                'last_name': obj.issued_to.last_name,
                'unit_number': obj.issued_to.unit_number
            }
        return None

    def get_temporary_owner_details(self, obj):
        if obj.temporary_owner:
            return {
                'id': obj.temporary_owner.id,
                'name': obj.temporary_owner.name,
                'first_name': obj.temporary_owner.first_name,
                'last_name': obj.temporary_owner.last_name,
                'purpose': obj.temporary_owner.purpose
            }
        return None


# -------------------
# Parking Slot Serializer
# -------------------
class ParkingSlotSerializer(serializers.ModelSerializer):
    issued_to_details = serializers.SerializerMethodField()
    temporary_owner_details = serializers.SerializerMethodField()
    location_display = serializers.SerializerMethodField()

    class Meta:
        model = ParkingSlot
        fields = [
            'id', 'slot_number', 'status', 'type', 
            'issued_to', 'issued_to_details', 
            'temporary_owner', 'temporary_owner_details', 
            'location', 'location_display'
        ]
    
    def get_issued_to_details(self, obj):
        if obj.issued_to:
            return {
                'id': obj.issued_to.id,
                'name': obj.issued_to.name,
                'first_name': obj.issued_to.first_name,
                'last_name': obj.issued_to.last_name,
                'unit_number': obj.issued_to.unit_number
            }
        return None

    def get_temporary_owner_details(self, obj):
        if obj.temporary_owner:
            return {
                'id': obj.temporary_owner.id,
                'name': obj.temporary_owner.name,
                'first_name': obj.temporary_owner.first_name,
                'last_name': obj.temporary_owner.last_name,
                'purpose': obj.temporary_owner.purpose,
                'plate_number': obj.temporary_owner.plate_number
            }
        return None

    def get_location_display(self, obj):
        if not obj.location:
            return "N/A"
        
        location_map = {
            'BUILDING_A': 'Building A',
            'BUILDING_B': 'Building B', 
            'BUILDING_C': 'Building C',
            'BUILDING_D': 'Building D',
            'BUILDING_E': 'Building E',
            'BUILDING_F': 'Building F',
            'BUILDING_G': 'Building G',
            'ADMIN': 'Admin Building'
        }
        
        return location_map.get(obj.location, obj.location.replace('_', ' ').title())

# -------------------
# Visitor Serializer
# -------------------
class VisitorSerializer(serializers.ModelSerializer):
    # Display fields (read-only)
    rfid_details = serializers.SerializerMethodField()
    parking_slot_details = serializers.SerializerMethodField()
    
    # These will be write-only but we'll handle read values in to_representation
    rfid_id = serializers.PrimaryKeyRelatedField(
        queryset=RFID.objects.filter(is_temporary=True, active=True),
        required=False,
        allow_null=True,
        write_only=True
    )
    parking_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSlot.objects.filter(type='FREE'),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Visitor
        fields = [
            'id', 'first_name', 'last_name', 'drivers_license', 
            'address', 'plate_number', 'purpose', 'timestamp',
            'rfid_details', 'parking_slot_details',
            'rfid_id', 'parking_slot_id',
            'signed_out', 'signed_out_at'
        ]
        read_only_fields = ['timestamp', 'signed_out', 'signed_out_at']

    def get_rfid_details(self, obj):
        # Get RFID assigned to this visitor
        rfid = RFID.objects.filter(temporary_owner=obj).first()
        if rfid:
            return {
                'id': rfid.id,
                'uid': rfid.uid,
                'is_temporary': rfid.is_temporary,
                'active': rfid.active
            }
        return None
    
    def get_parking_slot_details(self, obj):
        # Get parking slot assigned to this visitor
        parking = ParkingSlot.objects.filter(temporary_owner=obj).first()
        if parking:
            return {
                'id': parking.id,
                'slot_number': parking.slot_number,
                'type': parking.type,
                'status': parking.status,
                'location': parking.location
            }
        return None

    def validate(self, data):
        rfid = data.get('rfid_id')
        parking_slot = data.get('parking_slot_id')
        
        # Validate RFID
        if rfid is not None:
            if not rfid.is_temporary:
                raise serializers.ValidationError({
                    'rfid_id': ["Only temporary RFID can be assigned to visitors."]
                })
            
            if rfid.temporary_owner and rfid.temporary_owner.id != (self.instance.id if self.instance else None):
                raise serializers.ValidationError({
                    'rfid_id': ["This RFID is already assigned to another visitor."]
                })
        
        # Validate parking slot
        if parking_slot is not None:
            if parking_slot.type != 'FREE':
                raise serializers.ValidationError({
                    'parking_slot_id': ["Only free parking slots can be assigned to visitors."]
                })
            
            if parking_slot.temporary_owner and parking_slot.temporary_owner.id != (self.instance.id if self.instance else None):
                raise serializers.ValidationError({
                    'parking_slot_id': ["This parking slot is already occupied by another visitor."]
                })
        
        return data

    def create(self, validated_data):
        rfid = validated_data.pop('rfid_id', None)
        parking_slot = validated_data.pop('parking_slot_id', None)
        
        visitor = Visitor.objects.create(**validated_data)
        
        # Assign RFID if provided
        if rfid:
            rfid.temporary_owner = visitor
            rfid.save()
        
        # Assign parking slot if provided
        if parking_slot:
            parking_slot.temporary_owner = visitor
            parking_slot.status = 'OCCUPIED'
            parking_slot.save()
        
        return visitor
    
    def update(self, instance, validated_data):
        # Get current assignments
        old_rfid = RFID.objects.filter(temporary_owner=instance).first()
        old_parking = ParkingSlot.objects.filter(temporary_owner=instance).first()
        
        new_rfid = validated_data.pop('rfid_id', None)
        new_parking = validated_data.pop('parking_slot_id', None)
        
        # Update visitor fields
        instance = super().update(instance, validated_data)
        
        # Handle RFID changes
        if old_rfid and new_rfid is None:
            old_rfid.temporary_owner = None
            old_rfid.save()
        elif new_rfid and new_rfid != old_rfid:
            if old_rfid:
                old_rfid.temporary_owner = None
                old_rfid.save()
            
            new_rfid.temporary_owner = instance
            new_rfid.save()
        
        # Handle parking slot changes
        if old_parking and new_parking is None:
            old_parking.temporary_owner = None
            old_parking.status = 'AVAILABLE'
            old_parking.save()
        elif new_parking and new_parking != old_parking:
            if old_parking:
                old_parking.temporary_owner = None
                old_parking.status = 'AVAILABLE'
                old_parking.save()
            
            new_parking.temporary_owner = instance
            new_parking.status = 'OCCUPIED'
            new_parking.save()
        
        return instance
    
    def to_representation(self, instance):
        """Custom representation to include IDs in response"""
        representation = super().to_representation(instance)
        
        # Add the current IDs to the response (for frontend to display)
        rfid = RFID.objects.filter(temporary_owner=instance).first()
        representation['rfid_id'] = rfid.id if rfid else None
        
        parking = ParkingSlot.objects.filter(temporary_owner=instance).first()
        representation['parking_slot_id'] = parking.id if parking else None
        
        return representation

# -------------------
# AccessLog Serializer
# -------------------
class AccessLogSerializer(serializers.ModelSerializer):
    resident_details = serializers.SerializerMethodField()
    visitor_log_details = serializers.SerializerMethodField()
    parking_details = serializers.SerializerMethodField()
    
    # Write-only fields for creating/updating
    resident_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        source='resident',
        write_only=True,
        required=False,
        allow_null=True
    )
    visitor_log_id = serializers.PrimaryKeyRelatedField(
        queryset=Visitor.objects.all(),
        source='visitor_log',
        write_only=True,
        required=False,
        allow_null=True
    )
    parking_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSlot.objects.all(),
        source='parking',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = AccessLog
        fields = [
            'id', 'timestamp', 'action', 'type', 
            'resident_details', 'visitor_log_details', 'parking_details',
            'resident_id', 'visitor_log_id', 'parking_id'
        ]
        read_only_fields = ['timestamp']

    def get_resident_details(self, obj):
        if obj.resident:
            return {
                'id': obj.resident.id,
                'name': obj.resident.name,
                'first_name': obj.resident.first_name,
                'last_name': obj.resident.last_name,
                'unit_number': obj.resident.unit_number,
                'plate_number': obj.resident.plate_number
            }
        return None

    def get_visitor_log_details(self, obj):
        if obj.visitor_log:
            return {
                'id': obj.visitor_log.id,
                'name': obj.visitor_log.name,
                'first_name': obj.visitor_log.first_name,
                'last_name': obj.visitor_log.last_name,
                'purpose': obj.visitor_log.purpose,
                'plate_number': obj.visitor_log.plate_number,
                'drivers_license': obj.visitor_log.drivers_license,
                'address': obj.visitor_log.address,
                'signed_out': obj.visitor_log.signed_out
            }
        return None

    def get_parking_details(self, obj):
        if obj.parking:
            return {
                'id': obj.parking.id,
                'slot_number': obj.parking.slot_number,
                'type': obj.parking.type,
                'status': obj.parking.status,
                'location': obj.parking.location
            }
        return None