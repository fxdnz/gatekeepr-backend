from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from .models import Resident, Visitor, RFID, ParkingSlot, AccessLog
from .serializers import (
    ResidentSerializer,
    VisitorSerializer,
    RFIDSerializer,
    ParkingSlotSerializer,
    AccessLogSerializer
)

# -------------------
# Resident Views
# -------------------
class ResidentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]

class ResidentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]


# -------------------
# RFID Views
# -------------------
class RFIDListCreateAPIView(generics.ListCreateAPIView):
    queryset = RFID.objects.all()
    serializer_class = RFIDSerializer
    permission_classes = [IsAuthenticated]

class RFIDRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RFID.objects.all()
    serializer_class = RFIDSerializer
    permission_classes = [IsAuthenticated]


# -------------------
# Parking Slot Views
# -------------------
class ParkingSlotListCreateAPIView(generics.ListCreateAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]

class ParkingSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]


# -------------------
# Visitor Views
# -------------------
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            visitor = serializer.save()

            access_log = AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
                parking=visitor.parking_slot
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


# -------------------
# AccessLog Views
# -------------------
class AccessLogListAPIView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]

class AccessLogRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]


# -------------------
# Validate RFID
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_rfid(request):
    rfid_uid = request.data.get('rfid_uid')
    action = request.data.get('action')

    if not rfid_uid or not action or action not in ['ENTRY', 'EXIT']:
        return Response({'status': 'error', 'message': 'Invalid request'}, status=400)

    try:
        rfid = RFID.objects.get(uid=rfid_uid)
    except RFID.DoesNotExist:
        return Response({'status': 'error', 'message': 'RFID not registered'}, status=404)

    # Determine owner
    if rfid.issued_to:
        user_type = 'RESIDENT'
        user = rfid.issued_to
        parking = user.parking_slot
    elif rfid.temporary_owner:
        user_type = 'VISITOR'
        user = rfid.temporary_owner
        parking = user.parking_slot
    else:
        return Response({'status': 'error', 'message': 'RFID not assigned'})

    # Handle parking
    parking_message = ''
    if parking:
        if action == 'ENTRY':
            if parking.status == 'AVAILABLE':
                parking.status = 'OCCUPIED'
                parking.save()
                parking_message = f"Parking {parking.slot_number} occupied"
            else:
                parking_message = f"Parking {parking.slot_number} already occupied"
        else:
            if parking.status == 'OCCUPIED':
                parking.status = 'AVAILABLE'
                parking.save()
                parking_message = f"Parking {parking.slot_number} freed"

    # Create access log
    access_log = AccessLog.objects.create(
        type=user_type,
        action=action,
        resident=user if user_type=='RESIDENT' else None,
        visitor_log=user if user_type=='VISITOR' else None,
        parking=parking
    )

    return Response({
        'status': 'success',
        'user_type': user_type,
        'name': user.name,
        'plate_number': user.plate_number,
        'parking_slot': parking.slot_number if parking else None,
        'parking_status': parking.status if parking else 'NO_SLOT',
        'parking_message': parking_message,
        'access_log_id': access_log.id,
        'timestamp': access_log.timestamp
    })
