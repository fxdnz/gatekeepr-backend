from django.urls import path
from .views import (
    ResidentListCreateAPIView,
    ResidentRetrieveUpdateDestroyAPIView,
    RFIDListCreateAPIView,
    RFIDRetrieveUpdateDestroyAPIView,
    ParkingSlotListCreateAPIView,
    ParkingSlotRetrieveUpdateDestroyAPIView,
    VisitorListCreateAPIView,
    VisitorRetrieveUpdateDestroyAPIView,
    AccessLogListCreateAPIView,
    AccessLogRetrieveAPIView,
    validate_rfid,
    sign_out_visitor  # Add this import
)

urlpatterns = [
    # Resident endpoints
    path('residents/', ResidentListCreateAPIView.as_view(), name='resident-list'),
    path('residents/<int:pk>/', ResidentRetrieveUpdateDestroyAPIView.as_view(), name='resident-detail'),
    
    # RFID endpoints
    path('rfid/', RFIDListCreateAPIView.as_view(), name='rfid-list'),
    path('rfid/<int:pk>/', RFIDRetrieveUpdateDestroyAPIView.as_view(), name='rfid-detail'),
    
    # ParkingSlot endpoints
    path('parking/', ParkingSlotListCreateAPIView.as_view(), name='parking-list'),
    path('parking/<int:pk>/', ParkingSlotRetrieveUpdateDestroyAPIView.as_view(), name='parking-detail'),
    
    # Visitor endpoints
    path('visitors/', VisitorListCreateAPIView.as_view(), name='visitor-list'),
    path('visitors/<int:pk>/', VisitorRetrieveUpdateDestroyAPIView.as_view(), name='visitor-detail'),
    
    # AccessLog endpoints
    path('access-logs/', AccessLogListCreateAPIView.as_view(), name='access-log-list'),
    path('access-logs/<int:pk>/', AccessLogRetrieveAPIView.as_view(), name='access-log-detail'),
    
    # RFID validation endpoint
    path('validate-rfid/', validate_rfid, name='validate-rfid'),
    
    # Visitor sign-out endpoint
    path('sign-out-visitor/', sign_out_visitor, name='sign-out-visitor'),  # Add this
]