from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Resident, Visitor, AccessLog, ParkingSlot, RFIDTag
from .serializers import (
    ResidentSerializer,
    VisitorSerializer,
    AccessLogSerializer,
    ParkingSlotSerializer
)

User = get_user_model()


# ---------------- Resident Views ----------------
class ResidentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]

class ResidentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


# ---------------- Visitor Views ----------------
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            visitor = Visitor.objects.create(
                name=serializer.validated_data['name'],
                drivers_license=serializer.validated_data['drivers_license'],
                plate_number=serializer.validated_data.get('plate_number', ''),
                purpose=serializer.validated_data['purpose'],
            )

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


# ---------------- Parking Slot Views ----------------
class ParkingSlotListCreateAPIView(generics.ListCreateAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]

class ParkingSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


# ---------------- Access Log Views ----------------
class AccessLogListAPIView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]

class AccessLogRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


# ---------------- RFID Validation (Supports Entry & Exit Gates) ----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_rfid(request, rfid_uid):
    """
    Validate an RFID UID.
    Requires query parameter: ?action=ENTRY or ?action=EXIT
    Used by two separate RFID readers: Entry Gate & Exit Gate.
    """
    cleaned_uid = rfid_uid.upper().strip()
    action = request.query_params.get('action', '').upper()

    # Validate action
    if action not in ['ENTRY', 'EXIT']:
        return Response({
            'status': 'error',
            'message': 'Missing or invalid action. Use ?action=ENTRY or ?action=EXIT'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # === 1. Find RFID Tag ===
        tag = RFIDTag.objects.get(uid=cleaned_uid)

        # === 2. Check if Active ===
        if not tag.is_active:
            return Response({
                'status': 'error',
                'message': f'RFID tag {cleaned_uid} is inactive. Contact admin.'
            }, status=status.HTTP_403_FORBIDDEN)

        # === 3. Find Linked Resident ===
        try:
            resident = Resident.objects.get(rfid_tag=tag)
        except Resident.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'No resident linked to RFID {cleaned_uid}.'
            }, status=status.HTTP_404_NOT_FOUND)

        # === 4. Handle Parking & Logging ===
        with transaction.atomic():
            parking = None

            if action == 'ENTRY':
                # If resident already has a parking slot, update its status to 'OCCUPIED'
                if resident.parking_slot:
                    parking = resident.parking_slot
                    if parking.status == 'AVAILABLE':
                        parking.status = 'OCCUPIED'
                        parking.save()
                # If resident does not have a parking slot, do nothing

            elif action == 'EXIT':
                # Free resident's current parking if it's 'OCCUPIED'
                if resident.parking_slot and resident.parking_slot.status == 'OCCUPIED':
                    parking = resident.parking_slot
                    parking.status = 'AVAILABLE'
                    parking.resident = None  # Remove the resident from the parking slot
                    parking.save()

            # Log the access
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
            'parking_slot': parking.slot_number if parking else None
        }, status=status.HTTP_200_OK)

    except RFIDTag.DoesNotExist:
        # === Handle Visitor (Only ENTRY allowed via RFID) ===
        if action != 'ENTRY':
            return Response({
                'status': 'error',
                'message': 'Visitors cannot exit using RFID. Use driver\'s license at entry only.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            visitor = Visitor.objects.get(drivers_license=cleaned_uid)
            AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
            )
            return Response({
                'status': 'success',
                'visitor': VisitorSerializer(visitor).data,
                'message': 'Visitor entry logged successfully.'
            }, status=status.HTTP_200_OK)

        except Visitor.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'UID {cleaned_uid} not registered as resident or visitor.'
            }, status=status.HTTP_404_NOT_FOUND)
