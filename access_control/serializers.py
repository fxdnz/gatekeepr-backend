from rest_framework import serializers
from .models import Resident, Visitor, ParkingSlot, AccessLog, RFIDCard


class RFIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDCard
        fields = '__all__'
        read_only_fields = ('created_at',)


class ResidentSerializer(serializers.ModelSerializer):
    # Show the RFID UID (if any)
    rfid_uid = serializers.CharField(source='rfid_card.uid', read_only=True, allow_null=True)
    # Show all owned parking slots
    parking_slots = serializers.SerializerMethodField()

    class Meta:
        model = Resident
        fields = '__all__'

    def get_parking_slots(self, obj):
        return [slot.slot_number for slot in obj.parking_slots.filter(status='OCCUPIED')]


class VisitorSerializer(serializers.ModelSerializer):
    rfid_uid = serializers.CharField(source='rfid_card.uid', read_only=True, allow_null=True)

    class Meta:
        model = Visitor
        fields = '__all__'
        read_only_fields = ('timestamp',)


class ParkingSlotSerializer(serializers.ModelSerializer):
    resident_name = serializers.CharField(source='resident.name', read_only=True, allow_null=True)

    class Meta:
        model = ParkingSlot
        fields = '__all__'


class AccessLogSerializer(serializers.ModelSerializer):
    resident = ResidentSerializer(read_only=True)
    visitor_log = VisitorSerializer(read_only=True)
    parking = ParkingSlotSerializer(read_only=True)

    class Meta:
        model = AccessLog
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if instance.type == 'VISITOR':
            rep['name'] = instance.visitor_log.name
            rep['plate_number'] = instance.visitor_log.plate_number
            rep['purpose'] = instance.visitor_log.purpose
            rep['parking_slot'] = None
        else:
            rep['name'] = instance.resident.name
            rep['plate_number'] = instance.resident.plate_number
            rep['purpose'] = None
            rep['parking_slot'] = instance.parking.slot_number if instance.parking else None

        rep['timestamp'] = instance.timestamp.isoformat()
        return rep