from rest_framework import serializers
from .models import Resident, Visitor, ParkingSlot, AccessLog

class ResidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resident
        fields = '__all__'

class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = '__all__'
        read_only_fields = ('timestamp',)

class ParkingSlotSerializer(serializers.ModelSerializer):
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
        representation = super().to_representation(instance)

        if instance.type == 'VISITOR':
            representation['name'] = instance.visitor_log.name
            representation['plate_number'] = instance.visitor_log.plate_number
            representation['purpose'] = instance.visitor_log.purpose
            representation['parking_slot'] = None
        else:
            representation['name'] = instance.resident.name
            representation['plate_number'] = instance.resident.plate_number
            representation['purpose'] = None
            representation['parking_slot'] = instance.parking.slot_number if instance.parking else None

        representation['timestamp'] = instance.timestamp.isoformat()
        return representation