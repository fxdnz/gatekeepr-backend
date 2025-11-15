from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Resident, Visitor, AccessLog, ParkingSlot, RFIDCard
from .serializers import (
    ResidentSerializer, VisitorSerializer,
    AccessLogSerializer, ParkingSlotSerializer, RFIDCardSerializer
)

User = get_user_model()


class RFIDCardListCreateAPIView(generics.ListCreateAPIView):
    queryset = RFIDCard.objects.all()
    serializer_class = RFIDCardSerializer
    permission_classes = [IsAuthenticated]

class RFIDCardRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RFIDCard.objects.all()
    serializer_class = RFIDCardSerializer
    permission_classes = [IsAuthenticated]

# -------------------------------------------------
# Resident views (unchanged except serializer)
# -------------------------------------------------
class ResidentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


class ResidentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------------------------
# Visitor views – now can receive optional rfid_uid
# -------------------------------------------------
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # 1. Create Visitor
            visitor = Visitor.objects.create(**serializer.validated_data)

            # 2. Optional temporary RFID card
            rfid_uid = request.data.get('rfid_uid')
            if rfid_uid:
                rfid_uid = rfid_uid.upper().strip()
                if RFIDCard.objects.filter(uid=rfid_uid).exists():
                    raise serializers.ValidationError(
                        {"rfid_uid": "This RFID UID is already in use."}
                    )
                RFIDCard.objects.create(
                    uid=rfid_uid,
                    is_temporary=True,
                    visitor=visitor
                )

            # 3. Log entry
            access_log = AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
            )

            return Response({
                'status': 'success',
                'visitor': VisitorSerializer(visitor).data,
                'access_log': AccessLogSerializer(access_log).data
            }, status=status.HTTP_201_CREATED)


class VisitorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------------------------
# ParkingSlot views (unchanged)
# -------------------------------------------------
class ParkingSlotListCreateAPIView(generics.ListCreateAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


class ParkingSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------------------------
# AccessLog views (read-only)
# -------------------------------------------------
class AccessLogListAPIView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


class AccessLogRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


# -------------------------------------------------
# RFID validation – now works with the new RFIDCard model
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_rfid(request, rfid_uid):
    rfid_uid = rfid_uid.upper().strip()
    try:
        card = RFIDCard.objects.select_related('resident', 'visitor').get(uid=rfid_uid)
    except RFIDCard.DoesNotExist:
        return Response(
            {'status': 'error', 'message': 'RFID not registered'},
            status=status.HTTP_404_NOT_FOUND
        )

    # ---------- RESIDENT CARD ----------
    if card.resident:
        resident = card.resident
        last = AccessLog.objects.filter(resident=resident).order_by('-timestamp').first()

        if last and last.action == 'ENTRY':
            action = 'EXIT'
            parking = ParkingSlot.objects.filter(resident=resident, status='OCCUPIED').first()
            if parking:
                parking.status = 'AVAILABLE'
                parking.resident = None
                parking.save()
        else:
            action = 'ENTRY'
            parking = ParkingSlot.objects.filter(status='AVAILABLE').first()
            if parking:
                parking.status = 'OCCUPIED'
                parking.resident = resident
                parking.save()

        log = AccessLog.objects.create(
            type='RESIDENT',
            action=action,
            resident=resident,
            parking=parking
        )

        return Response({
            'status': 'success',
            'action': action,
            'resident': ResidentSerializer(resident).data,
            'parking_slot': parking.slot_number if parking else None
        })

    # ---------- TEMPORARY VISITOR CARD ----------
    else:   # must be a visitor (temporary)
        visitor = card.visitor
        log = AccessLog.objects.create(
            type='VISITOR',
            action='ENTRY',
            visitor_log=visitor,
        )
        return Response({
            'status': 'success',
            'action': 'ENTRY',
            'visitor': VisitorSerializer(visitor).data,
        })