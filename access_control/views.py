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


# ---------------- RFID Validation ----------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_rfid(request, rfid_uid):
    """
    Validate an RFID UID using the RFIDTag model.
    Checks if it's active, linked to a resident, or registered as a visitor.
    """

    cleaned_uid = rfid_uid.upper().strip()

    try:
        # 1️⃣ Find RFID tag
        tag = RFIDTag.objects.get(uid=cleaned_uid)

        # 2️⃣ Check if active
        if not tag.is_active:
            return Response({
                'status': 'error',
                'message': f'RFID tag {cleaned_uid} is inactive. Please contact admin.'
            }, status=status.HTTP_403_FORBIDDEN)

        # 3️⃣ Find linked resident
        try:
            resident = Resident.objects.get(rfid_tag=tag)
        except Resident.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'No resident linked to RFID tag {cleaned_uid}.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 4️⃣ Determine ENTRY / EXIT
        last_action = AccessLog.objects.filter(resident=resident).order_by('-timestamp').first()

        with transaction.atomic():
            if last_action and last_action.action == 'ENTRY':
                action = 'EXIT'
                parking = ParkingSlot.objects.filter(resident=resident).first()
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

            # 5️⃣ Log the event
            AccessLog.objects.create(
                type='RESIDENT',
                action=action,
                resident=resident,
                parking=parking if parking else None,
            )

        return Response({
            'status': 'success',
            'action': action,
            'resident': ResidentSerializer(resident).data,
            'parking': parking.slot_number if parking else None
        }, status=status.HTTP_200_OK)

    except RFIDTag.DoesNotExist:
        # 6️⃣ Try to match Visitor
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
                'message': 'Visitor entry logged.'
            }, status=status.HTTP_200_OK)

        except Visitor.DoesNotExist:
            return Response({
                'status': 'error',
                'message': f'RFID UID {cleaned_uid} not registered as resident or visitor.'
            }, status=status.HTTP_404_NOT_FOUND)
