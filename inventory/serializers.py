from rest_framework import serializers
from inventory.models import Dealership, Vehicle, AgingAction

class DealershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealership
        fields = ['id', 'name', 'location']


class AgingActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgingAction
        fields = ['action_type', 'notes', 'created_at']


class AgingActionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgingAction
        fields = ['id', 'action_type', 'notes', 'created_by', 'created_at']


class VehicleSerializer(serializers.ModelSerializer):
    days_in_stock = serializers.IntegerField(read_only=True)
    is_aging = serializers.BooleanField(read_only=True)
    latest_action = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            'id', 'vin', 'make', 'model', 'year', 'intake_date',
            'price', 'status', 'days_in_stock', 'is_aging', 'latest_action'
        ]

    def get_latest_action(self, obj):
        # Use prefetched actions to avoid N+1 query if present
        prefetched = getattr(obj, 'prefetched_actions', None)
        if prefetched is not None:
            return AgingActionSerializer(prefetched[0]).data if prefetched else None
        
        # Fallback to query
        latest = obj.actions.order_by('-created_at').first()
        return AgingActionSerializer(latest).data if latest else None


class VehicleDetailSerializer(VehicleSerializer):
    history = serializers.SerializerMethodField()

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ['history']

    def get_history(self, obj):
        actions = obj.actions.order_by('-created_at')
        return AgingActionHistorySerializer(actions, many=True).data


class AgingActionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgingAction
        fields = ['id', 'action_type', 'notes', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        vehicle_id = self.context.get('vehicle_id')
        try:
            vehicle = Vehicle.objects.get(pk=vehicle_id)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError("Vehicle does not exist.")

        # Validation: vehicle must be in_stock
        if vehicle.status != Vehicle.Status.IN_STOCK:
            raise serializers.ValidationError(
                "Actions can only be logged on in_stock vehicles."
            )
        return attrs
