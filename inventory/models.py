from django.db import models

class Dealership(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    class Status(models.TextChoices):
        IN_STOCK = 'in_stock', 'In Stock'
        SOLD = 'sold', 'Sold'
        RESERVED = 'reserved', 'Reserved'

    dealership = models.ForeignKey(
        Dealership,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )
    vin = models.CharField(max_length=17, unique=True)
    make = models.CharField(max_length=255, db_index=True)
    model = models.CharField(max_length=255, db_index=True)
    year = models.PositiveIntegerField()
    intake_date = models.DateField(db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_STOCK,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['dealership', 'status', 'intake_date']),
        ]

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.vin})"



class AgingAction(models.Model):
    class ActionType(models.TextChoices):
        PRICE_REDUCTION_PLANNED = 'price_reduction_planned', 'Price Reduction Planned'
        PROMOTION_PLANNED = 'promotion_planned', 'Promotion Planned'
        TRANSFER_PLANNED = 'transfer_planned', 'Transfer Planned'
        NO_ACTION = 'no_action', 'No Action'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    action_type = models.CharField(
        max_length=30,
        choices=ActionType.choices
    )
    notes = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} on {self.vehicle.vin} at {self.created_at}"
