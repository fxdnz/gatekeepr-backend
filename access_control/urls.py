from django.urls import path
from .views import (
    ResidentListCreateAPIView,
    ResidentRetrieveUpdateDestroyAPIView,
    VisitorListCreateAPIView,
    VisitorRetrieveUpdateDestroyAPIView,
    ParkingSlotListCreateAPIView,
    ParkingSlotRetrieveUpdateDestroyAPIView,
    AccessLogListAPIView,
    AccessLogRetrieveAPIView,
    RFIDCardListCreateAPIView, RFIDCardRetrieveUpdateDestroyAPIView,
    validate_rfid
)

urlpatterns = [
    # Resident endpoints
    path('rfid-cards/', RFIDCardListCreateAPIView.as_view(), name='rfidcard-list'),
    path('rfid-cards/<int:pk>/', RFIDCardRetrieveUpdateDestroyAPIView.as_view(), name='rfidcard-detail'),

    # Resident endpoints
    path('residents/', ResidentListCreateAPIView.as_view(), name='resident-list'),
    path('residents/<int:pk>/', ResidentRetrieveUpdateDestroyAPIView.as_view(), name='resident-detail'),
    
    # Visitor endpoints
    path('visitors/', VisitorListCreateAPIView.as_view(), name='visitor-list'),
    path('visitors/<int:pk>/', VisitorRetrieveUpdateDestroyAPIView.as_view(), name='visitor-detail'),
    
    # Parking endpoints
    path('parking/', ParkingSlotListCreateAPIView.as_view(), name='parking-list'),
    path('parking/<int:pk>/', ParkingSlotRetrieveUpdateDestroyAPIView.as_view(), name='parking-detail'),
    
    # Access log endpoints (read-only)
    path('access-logs/', AccessLogListAPIView.as_view(), name='access-log-list'),
    path('access-logs/<int:pk>/', AccessLogRetrieveAPIView.as_view(), name='access-log-detail'),
    
    # RFID validation endpoint
    path('validate-rfid/<str:rfid_uid>/', validate_rfid, name='validate-rfid'),
]