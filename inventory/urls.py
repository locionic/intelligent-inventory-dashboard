from django.urls import path
from inventory.views import (
    DealershipListView,
    VehicleListView,
    AgingVehicleListView,
    VehicleDetailView,
    AgingActionCreateView
)

urlpatterns = [
    path('dealerships/', DealershipListView.as_view(), name='dealership-list'),
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/aging/', AgingVehicleListView.as_view(), name='aging-vehicle-list'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/<int:pk>/actions/', AgingActionCreateView.as_view(), name='vehicle-action-create'),
]
