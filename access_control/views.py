import logging
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

# Setup logger
logger = logging.getLogger(__name__)


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
                visitor_log=visitor,  # ← Matches model
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
    logger.info(f"[RFID VALIDATE] UID: {rfid_uid}")

    # ---------- 1. Find RFID Card ----------
    try:
        rfid_card = RFIDCard.objects.select_related('resident', 'visitor').get(
            rfid_uid=rfid_uid,
            is_active=True
        )
        logger.info(f"[RFID] Found: {rfid_card}")
    except RFIDCard.DoesNotExist:
        logger.warning(f"[RFID] Not found or inactive: {rfid_uid}")
        return Response(
            {'status': 'error', 'message': 'RFID not registered or inactive'},
            status=404
        )

    # ---------- 2. RESIDENT (Permanent Card) ----------
    if rfid_card.resident:
        resident = rfid_card.resident
        logger.info(f"[RESIDENT] {resident.name} (Unit {resident.unit_number})")

        # Get last action
        last_log = AccessLog.objects.filter(resident=resident).order_by('-timestamp').first()
        action = 'EXIT' if (last_log and last_log.action == 'ENTRY') else 'ENTRY'
        logger.info(f"[RESIDENT] Last: {last_log.action if last_log else 'None'} → Next: {action}")

        parking = None

        with transaction.atomic():
            if action == 'EXIT' and resident.parking_slot:
                parking = resident.parking_slot
                parking.status = 'AVAILABLE'
                parking.save()
                resident.parking_slot = None
                resident.save()
                logger.info(f"[EXIT] Freed slot: {parking.slot_number}")

            elif action == 'ENTRY':
                parking = ParkingSlot.objects.filter(status='AVAILABLE').first()
                if parking:
                    parking.status = 'OCCUPIED'
                    parking.save()
                    resident.parking_slot = parking
                    resident.save()
                    logger.info(f"[ENTRY] Assigned: {parking.slot_number}")
                else:
                    logger.warning("[ENTRY] No available slot for resident")

            # Create log
            AccessLog.objects.create(
                type='RESIDENT',
                action=action,
                resident=resident,
                parking=parking
            )

        return Response({
            'status': 'success',
            'action': action,
            'resident': ResidentSerializer(resident).data,
            'parking': parking.slot_number if parking and parking.slot_number else None
        }, status=200)

    # ---------- 3. VISITOR (Temporary Card) ----------
    elif rfid_card.visitor and rfid_card.is_temporary:
        visitor = rfid_card.visitor
        logger.info(f"[VISITOR] {visitor.name} – {visitor.purpose}")

        fixed_slots = ['CP57', 'CP58', 'CP59', 'CP60', 'CP61']
        parking = ParkingSlot.objects.filter(
            slot_number__in=fixed_slots,
            status='AVAILABLE'
        ).first()

        if parking:
            parking.status = 'OCCUPIED'
            parking.save()
            logger.info(f"[VISITOR] Assigned: {parking.slot_number}")
        else:
            logger.warning("[VISITOR] No available visitor slot")

        with transaction.atomic():
            AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,  # ← Correct field name
                parking=parking
            )

        return Response({
            'status': 'success',
            'action': 'ENTRY',
            'visitor': VisitorSerializer(visitor).data,
            'parking': parking.slot_number if parking and parking.slot_number else None
        }, status=200)

    # ---------- 4. Invalid Card ----------
    else:
        logger.warning(f"[RFID] Unlinked card: {rfid_card}")
        return Response(
            {'status': 'error', 'message': 'RFID not linked to any person'},
            status=400
        )