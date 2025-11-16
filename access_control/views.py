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
   # permission_classes = [IsAuthenticated]  # Protect this view with authentication

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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_rfid(request):
    """
    Accepts JSON: {'rfid_uid': 'ABC123', 'action': 'ENTRY' or 'EXIT'}
    Validates RFID via URL endpoint and uses action for parking/log creation
    """
    try:
        # Get data from JSON request
        rfid_uid = request.data.get('rfid_uid')
        action = request.data.get('action')

        # Validate required fields
        if not rfid_uid:
            return Response({
                'status': 'error',
                'message': 'rfid_uid is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not action:
            return Response({
                'status': 'error', 
                'message': 'action is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if action not in ['ENTRY', 'EXIT']:
            return Response({
                'status': 'error',
                'message': 'action must be ENTRY or EXIT'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate RFID by checking if resident exists
        try:
            resident = Resident.objects.get(rfid_uid=rfid_uid.upper().strip())
        except Resident.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'RFID not registered'
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle parking based on action
        parking = None
        parking_message = ""
        
        if action == 'ENTRY':
            # Find available parking slot for entry
            parking = ParkingSlot.objects.filter(status='AVAILABLE').first()
            if parking:
                parking.status = 'OCCUPIED'
                parking.resident = resident
                parking.save()
                parking_message = f"Assigned parking slot {parking.slot_number}"
            else:
                parking_message = "No parking available"
                
        elif action == 'EXIT':
            # Release parking slot on exit
            parking = ParkingSlot.objects.filter(resident=resident, status='OCCUPIED').first()
            if parking:
                parking.status = 'AVAILABLE'
                parking.resident = None
                parking.save()
                parking_message = f"Released parking slot {parking.slot_number}"
            else:
                parking_message = "No parking slot to release"

        # Create access log
        access_log = AccessLog.objects.create(
            type='RESIDENT',
            action=action,
            resident=resident,
            parking=parking,
        )

        # Return success response
        return Response({
            'status': 'success',
            'message': f'Access {action} recorded successfully',
            'data': {
                'resident': ResidentSerializer(resident).data,
                'action': action,
                'parking_slot': parking.slot_number if parking else None,
                'parking_message': parking_message,
                'access_log_id': access_log.id,
                'timestamp': access_log.timestamp
            }
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)