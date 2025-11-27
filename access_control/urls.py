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
    RFIDListCreateAPIView,
    RFIDRetrieveUpdateDestroyAPIView,
    validate_rfid
)

urlpatterns = [

    # Residents
    path('residents/', ResidentListCreateAPIView.as_view()),
    path('residents/<int:pk>/', ResidentRetrieveUpdateDestroyAPIView.as_view()),

    # RFID CRUD
    path('rfid/', RFIDListCreateAPIView.as_view()),
    path('rfid/<int:pk>/', RFIDRetrieveUpdateDestroyAPIView.as_view()),

    # Visitors
    path('visitors/', VisitorListCreateAPIView.as_view()),
    path('visitors/<int:pk>/', VisitorRetrieveUpdateDestroyAPIView.as_view()),

    # Parking
    path('parking/', ParkingSlotListCreateAPIView.as_view()),
    path('parking/<int:pk>/', ParkingSlotRetrieveUpdateDestroyAPIView.as_view()),

    # Access Logs
    path('access-logs/', AccessLogListAPIView.as_view()),
    path('access-logs/<int:pk>/', AccessLogRetrieveAPIView.as_view()),

    # RFID Validation
    path('validate-rfid/', validate_rfid),
]
