from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from inventory.models import Dealership, Vehicle, AgingAction
from inventory.queries import get_annotated_vehicles
from inventory.serializers import (
    DealershipSerializer,
    VehicleSerializer,
    VehicleDetailSerializer,
    AgingActionCreateSerializer
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class DealershipListView(generics.ListAPIView):
    """
    GET /api/dealerships/
    Returns list of dealerships for dropdown filter population.
    """
    queryset = Dealership.objects.all()
    serializer_class = DealershipSerializer

    pagination_class = None

    def get_queryset(self):
        return Dealership.objects.all().order_by('name')


class VehicleListView(generics.ListAPIView):
    """
    GET /api/vehicles/
    Query params: dealership_id, make, model, min_age_days, status
    Returns: paginated list of vehicles with computed days_in_stock and is_aging fields.
    """
    serializer_class = VehicleSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = get_annotated_vehicles().order_by('-intake_date', 'id')


        # Apply optional filters
        dealership_id = self.request.query_params.get('dealership_id')
        make = self.request.query_params.get('make')
        model = self.request.query_params.get('model')
        status_param = self.request.query_params.get('status')
        min_age_days = self.request.query_params.get('min_age_days')

        if dealership_id:
            queryset = queryset.filter(dealership_id=dealership_id)
        if make:
            queryset = queryset.filter(make__iexact=make)
        if model:
            queryset = queryset.filter(model__iexact=model)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if min_age_days:
            try:
                queryset = queryset.filter(days_in_stock__gte=int(min_age_days))
            except ValueError:
                pass

        # Optimize for N+1 queries by prefetching the actions in descending order
        queryset = queryset.prefetch_related(
            Prefetch(
                'actions',
                queryset=AgingAction.objects.order_by('-created_at'),
                to_attr='prefetched_actions'
            )
        )
        return queryset


class AgingVehicleListView(generics.ListAPIView):
    """
    GET /api/vehicles/aging/
    Same filters, pre-filtered to is_aging=True, sorted by days_in_stock desc.
    Returns: vehicles + their latest AgingAction if any.
    """
    serializer_class = VehicleSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = get_annotated_vehicles().filter(is_aging=True).order_by('-days_in_stock')

        # Apply optional filters
        dealership_id = self.request.query_params.get('dealership_id')
        make = self.request.query_params.get('make')
        model = self.request.query_params.get('model')
        status_param = self.request.query_params.get('status')
        min_age_days = self.request.query_params.get('min_age_days')

        if dealership_id:
            queryset = queryset.filter(dealership_id=dealership_id)
        if make:
            queryset = queryset.filter(make__iexact=make)
        if model:
            queryset = queryset.filter(model__iexact=model)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if min_age_days:
            try:
                queryset = queryset.filter(days_in_stock__gte=int(min_age_days))
            except ValueError:
                pass

        # Optimize for N+1 queries by prefetching the actions in descending order
        queryset = queryset.prefetch_related(
            Prefetch(
                'actions',
                queryset=AgingAction.objects.order_by('-created_at'),
                to_attr='prefetched_actions'
            )
        )
        return queryset


class VehicleDetailView(generics.RetrieveAPIView):
    """
    GET /api/vehicles/{id}/
    Returns: single vehicle detail + full AgingAction history.
    """
    queryset = get_annotated_vehicles()
    serializer_class = VehicleDetailSerializer


class AgingActionCreateView(generics.CreateAPIView):
    """
    POST /api/vehicles/{id}/actions/
    Logs an AgingAction. Validates vehicle exists (404) and is in_stock (400).
    """
    serializer_class = AgingActionCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['vehicle_id'] = self.kwargs.get('pk')
        return context

    def create(self, request, *args, **kwargs):
        # Retrieve vehicle first. Will raise HTTP 404 if vehicle does not exist.
        vehicle = get_object_or_404(Vehicle, pk=self.kwargs.get('pk'))
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(vehicle=vehicle)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
