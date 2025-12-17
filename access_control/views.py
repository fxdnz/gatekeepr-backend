from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.utils import timezone
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

            # Create access log for visitor entry
            access_log = AccessLog.objects.create(
                type='VISITOR',
                action='ENTRY',
                visitor_log=visitor,
                parking=ParkingSlot.objects.filter(temporary_owner=visitor).first()
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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            self.perform_update(serializer)
            
            return Response({
                'status': 'success',
                'visitor': serializer.data,
                'message': 'Visitor updated successfully'
            })


# -------------------
# AccessLog Views
# -------------------
class AccessLogListCreateAPIView(generics.ListCreateAPIView):
    queryset = AccessLog.objects.all()
    serializer_class = AccessLogSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        access_log = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Access log created successfully',
            'access_log': AccessLogSerializer(access_log).data
        }, status=status.HTTP_201_CREATED)

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
        # Get resident's parking slot
        parking = ParkingSlot.objects.filter(issued_to=user).first()
    elif rfid.temporary_owner:
        user_type = 'VISITOR'
        user = rfid.temporary_owner
        # Get visitor's parking slot
        parking = ParkingSlot.objects.filter(temporary_owner=user).first()
        
        # Mark visitor as signed out on EXIT
        if action == 'EXIT':
            user.signed_out = True
            user.signed_out_at = timezone.now()
            user.save()
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
        'timestamp': access_log.timestamp,
        'signed_out': user.signed_out if user_type == 'VISITOR' else False
    })


# -------------------
# Sign Out Visitor
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sign_out_visitor(request):
    visitor_id = request.data.get('visitor_id')
    
    if not visitor_id:
        return Response({'status': 'error', 'message': 'Visitor ID is required'}, status=400)
    
    try:
        visitor = Visitor.objects.get(id=visitor_id)
    except Visitor.DoesNotExist:
        return Response({'status': 'error', 'message': 'Visitor not found'}, status=404)
    
    # Check if visitor is already signed out
    if visitor.signed_out:
        return Response({
            'status': 'error', 
            'message': 'Visitor is already signed out'
        }, status=400)
    
    # Check if visitor has assigned resources
    has_rfid = RFID.objects.filter(temporary_owner=visitor).exists()
    has_parking = ParkingSlot.objects.filter(temporary_owner=visitor).exists()
    
    if has_rfid or has_parking:
        return Response({
            'status': 'error', 
            'message': 'Visitor has assigned RFID or parking slot. Please unassign first.'
        }, status=400)
    
    with transaction.atomic():
        # Mark visitor as signed out
        visitor.signed_out = True
        visitor.signed_out_at = timezone.now()
        visitor.save()
        
        # Create exit access log
        access_log = AccessLog.objects.create(
            type='VISITOR',
            action='EXIT',
            visitor_log=visitor,
            parking=None
        )
    
    return Response({
        'status': 'success',
        'message': f'Visitor {visitor.name} signed out successfully',
        'visitor': VisitorSerializer(visitor).data,
        'access_log': AccessLogSerializer(access_log).data
    })