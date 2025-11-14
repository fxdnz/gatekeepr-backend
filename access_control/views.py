from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated  # Ensures token authentication is enforced
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes  # Allow per-view permission control
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Resident, Visitor, AccessLog, ParkingSlot
from .serializers import (
    ResidentSerializer,
    VisitorSerializer,
    AccessLogSerializer,
    ParkingSlotSerializer
)

User = get_user_model()

# Resident Views
class ResidentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

class ResidentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

# Visitor Log Views
class VisitorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

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
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

# Parking Slot Views
class ParkingSlotListCreateAPIView(generics.ListCreateAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

class ParkingSlotRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

# Access Log Views (ReadOnly)
class AccessLogListAPIView(generics.ListAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

class AccessLogRetrieveAPIView(generics.RetrieveAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]  # Protect this view with authentication

# RFID Validation View (Add token validation via permission_classes)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Protect this view with token authentication
def validate_rfid(request, rfid_uid):
    try:
        resident = Resident.objects.get(rfid_uid=rfid_uid.upper().strip())
        last_action = AccessLog.objects.filter(resident=resident).order_by('-timestamp').first()

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

        access_log = AccessLog.objects.create(
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
        })

    except Resident.DoesNotExist:
        try:
            visitor = Visitor.objects.get(drivers_license=rfid_uid.upper().strip())
            access_log = AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
            )

            return Response({
                'status': 'success',
                'visitor': VisitorSerializer(visitor).data,
            })

        except Visitor.DoesNotExist:
            return Response({'status': 'error', 'message': 'RFID not registered'}, status=404)