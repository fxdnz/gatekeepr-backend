from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Resident, Visitor, AccessLog, ParkingSlot, RFIDCard
from .serializers import (
    ResidentSerializer, VisitorSerializer,
    AccessLogSerializer, ParkingSlotSerializer
)

User = get_user_model()


# ------------------- Resident Views -------------------
class ResidentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


class ResidentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


# ------------------- Visitor Views -------------------
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            visitor = Visitor.objects.create(**serializer.validated_data)

            AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
            )

            return Response({
                'status': 'success',
                'visitor': VisitorSerializer(visitor).data,
            }, status=status.HTTP_201_CREATED)


class VisitorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]


# ------------------- Parking Views -------------------
class ParkingSlotListCreateAPIView(generics.ListCreateAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


class ParkingSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


# ------------------- Access Log Views -------------------
class AccessLogListAPIView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


class AccessLogRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


# ------------------- RFID Validation -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_rfid(request, rfid_uid):
    rfid_uid = rfid_uid.upper().strip()

    try:
        rfid_card = RFIDCard.objects.select_related('resident', 'visitor').get(
            rfid_uid=rfid_uid, is_active=True
        )
    except RFIDCard.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'RFID not registered or inactive'},
            status=404
        )

    # ---------- RESIDENT (permanent) ----------
    if rfid_card.resident:
        resident = rfid_card.resident
        last_log = AccessLog.objects.filter(resident=resident).order_by('-timestamp').first()

        if last_log and last_log.action == 'ENTRY':
            action = 'EXIT'
            parking = resident.parking_slot
            if parking:
                parking.status = 'AVAILABLE'
                parking.save()
        else:
            action = 'ENTRY'
            parking = ParkingSlot.objects.filter(status='AVAILABLE').first()
            if parking:
                parking.status = 'OCCUPIED'
                parking.save()
                resident.parking_slot = parking
                resident.save()

        access_log = AccessLog.objects.create(
            type='RESIDENT',
            action=action,
            resident=resident,
            parking=parking
        )

        return Response({
            'status': 'success',
            'action': action,
            'resident': ResidentSerializer(resident).data,
            'parking': parking.slot_number if parking else None
        })

    # ---------- VISITOR (temporary) ----------
    elif rfid_card.visitor and rfid_card.is_temporary:
        visitor = rfid_card.visitor
        # Temporary visitors use fixed slots CP57-CP61
        fixed_slots = ['CP57', 'CP58', 'CP59', 'CP60', 'CP61']
        parking = ParkingSlot.objects.filter(
            slot_number__in=fixed_slots, status='AVAILABLE'
        ).first()

        if parking:
            parking.status = 'OCCUPIED'
            parking.save()

        access_log = AccessLog.objects.create(
            type='VISITOR',
            action='ENTRY',
            visitor_log=visitor,
            parking=parking
        )

        return Response({
            'status': 'success',
            'action': 'ENTRY',
            'visitor': VisitorSerializer(visitor).data,
            'parking': parking.slot_number if parking else None
        })

    # ---------- Fallback ----------
    return Response(
        {'status': 'error', 'message': 'RFID not linked to any person'},
        status=400
    )