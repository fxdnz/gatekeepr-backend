from rest_framework import serializers
from .models import Resident, Visitor, RFID, ParkingSlot, AccessLog

# -------------------
# Resident Serializer
# -------------------
class ResidentSerializer(serializers.ModelSerializer):
    rfid_uid = serializers.PrimaryKeyRelatedField(
        queryset=RFID.objects.all(),
        required=False,
        allow_null=True
    )
    rfid_uid_display = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    parking_slot_display = serializers.SerializerMethodField()
    parking_slot_type = serializers.SerializerMethodField()

    class Meta:
        model = Resident
        fields = ['id', 'first_name', 'last_name', 'rfid_uid', 'rfid_uid_display', 'name', 'plate_number', 'unit_number', 'phone', 'parking_slot', 'parking_slot_display', 'parking_slot_type']

    def get_rfid_uid_display(self, obj):
        return obj.rfid_uid.uid if obj.rfid_uid else "N/A"
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    def get_parking_slot_display(self, obj):
        return obj.parking_slot.slot_number if obj.parking_slot else "N/A"
    
    def get_parking_slot_type(self, obj):
        return obj.parking_slot.type if obj.parking_slot else "N/A"

    # REMOVE or FIX the update method - it's causing the error

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

    def update(self, instance, validated_data):
        issued_to = validated_data.get('issued_to')
        if issued_to:
            issued_to.rfid_uid = instance
            issued_to.save()
        elif instance.issued_to:
            instance.issued_to.rfid_uid = None
            instance.issued_to.save()
        return super().update(instance, validated_data)


# -------------------
# Parking Slot Serializer
# -------------------
class ParkingSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSlot
        fields = '__all__'

    def update(self, instance, validated_data):
        owner = validated_data.get('owner')
        if owner:
            owner.parking_slot = instance
            owner.save()
        elif instance.owner:
            instance.owner.parking_slot = None
            instance.owner.save()
        return super().update(instance, validated_data)


# -------------------
# Visitor Serializer
# -------------------
class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = '__all__'

    def validate(self, data):
        # Validate RFID
        rfid = data.get('rfid')
        if rfid:
            if not rfid.is_temporary:
                raise serializers.ValidationError("Only temporary RFID can be assigned to visitors.")
            if rfid.temporary_owner:
                raise serializers.ValidationError("This RFID is already assigned to another visitor.")

        # Validate Parking
        parking = data.get('parking_slot')
        if parking:
            if parking.type != 'FREE':
                raise serializers.ValidationError("Only free parking slots can be assigned to visitors.")
            if parking.temporary_owner:
                raise serializers.ValidationError("This parking slot is already occupied by another visitor.")

        return data

    def create(self, validated_data):
        visitor = super().create(validated_data)
        # Assign temporary RFID and parking
        rfid = validated_data.get('rfid')
        if rfid:
            rfid.temporary_owner = visitor
            rfid.save()
        parking = validated_data.get('parking_slot')
        if parking:
            parking.temporary_owner = visitor
            parking.status = 'OCCUPIED'
            parking.save()
        return visitor

# -------------------
# AccessLog Serializer
# -------------------
class AccessLogSerializer(serializers.ModelSerializer):
    resident = ResidentSerializer(read_only=True)
    visitor_log = VisitorSerializer(read_only=True)
    parking = ParkingSlotSerializer(read_only=True)

    class Meta:
        model = AccessLog
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Add null checks for all related objects
        if instance.type == 'VISITOR':
            if instance.visitor_log:
                representation['name'] = f"{instance.visitor_log.first_name} {instance.visitor_log.last_name}"
                representation['plate_number'] = instance.visitor_log.plate_number
                representation['purpose'] = instance.visitor_log.purpose
            else:
                representation['name'] = "Deleted Visitor"
                representation['plate_number'] = None
                representation['purpose'] = None
        else:
            if instance.resident:
                representation['name'] = f"{instance.resident.first_name} {instance.resident.last_name}"
                representation['plate_number'] = instance.resident.plate_number
                representation['purpose'] = None
            else:
                representation['name'] = "Deleted Resident"
                representation['plate_number'] = None
                representation['purpose'] = None

        representation['parking_slot'] = instance.parking.slot_number if instance.parking else None
        representation['timestamp'] = instance.timestamp.isoformat()
        
        return representation
