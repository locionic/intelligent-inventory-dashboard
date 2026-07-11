from django.test import TestCase
from django.utils import timezone
import datetime
from inventory.models import Dealership, Vehicle, AgingAction
from inventory.queries import get_annotated_vehicles


class AgingStockQueryTestCase(TestCase):
    def setUp(self):
        self.dealership = Dealership.objects.create(
            name="Test Dealership",
            location="Test Location"
        )
        self.today = timezone.localdate()

    def test_zero_days_not_aging(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN0DAYS",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today,
            price=20000.00,
            status=Vehicle.Status.IN_STOCK
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 0)
        self.assertFalse(annotated_v.is_aging)

    def test_89_days_not_aging(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN89DAYS",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today - datetime.timedelta(days=89),
            price=20000.00,
            status=Vehicle.Status.IN_STOCK
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 89)
        self.assertFalse(annotated_v.is_aging)

    def test_90_days_not_aging(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN90DAYS",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today - datetime.timedelta(days=90),
            price=20000.00,
            status=Vehicle.Status.IN_STOCK
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 90)
        self.assertFalse(annotated_v.is_aging)

    def test_91_days_is_aging(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN91DAYS",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today - datetime.timedelta(days=91),
            price=20000.00,
            status=Vehicle.Status.IN_STOCK
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 91)
        self.assertTrue(annotated_v.is_aging)

    def test_sold_vehicle_excluded(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN91SOLD",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today - datetime.timedelta(days=91),
            price=20000.00,
            status=Vehicle.Status.SOLD
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 91)
        self.assertFalse(annotated_v.is_aging)

    def test_reserved_vehicle_excluded(self):
        v = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VIN91RESERVED",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today - datetime.timedelta(days=91),
            price=20000.00,
            status=Vehicle.Status.RESERVED
        )
        queryset = get_annotated_vehicles()
        annotated_v = queryset.get(pk=v.pk)
        
        self.assertEqual(annotated_v.days_in_stock, 91)
        self.assertFalse(annotated_v.is_aging)


from rest_framework.test import APITestCase
from rest_framework import status

class VehicleAPITestCase(APITestCase):
    def setUp(self):
        self.dealership = Dealership.objects.create(
            name="Test Dealership",
            location="Test Location"
        )
        self.today = timezone.localdate()
        
        self.in_stock_vehicle = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VININSTOCK",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today,
            price=20000.00,
            status=Vehicle.Status.IN_STOCK
        )
        
        self.sold_vehicle = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VINSOLD",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today,
            price=20000.00,
            status=Vehicle.Status.SOLD
        )

        self.reserved_vehicle = Vehicle.objects.create(
            dealership=self.dealership,
            vin="VINRESERVED",
            make="Toyota",
            model="Camry",
            year=2023,
            intake_date=self.today,
            price=20000.00,
            status=Vehicle.Status.RESERVED
        )

    def test_create_action_success(self):
        url = f"/api/vehicles/{self.in_stock_vehicle.id}/actions/"
        data = {
            "action_type": "price_reduction_planned",
            "notes": "Reducing price",
            "created_by": "Manager"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AgingAction.objects.count(), 1)

    def test_create_action_invalid_action_type(self):
        url = f"/api/vehicles/{self.in_stock_vehicle.id}/actions/"
        data = {
            "action_type": "invalid_action_type",
            "notes": "Notes",
            "created_by": "Manager"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_action_missing_vehicle(self):
        url = "/api/vehicles/99999/actions/"
        data = {
            "action_type": "price_reduction_planned",
            "notes": "Notes",
            "created_by": "Manager"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_action_sold_vehicle_rejected(self):
        url = f"/api/vehicles/{self.sold_vehicle.id}/actions/"
        data = {
            "action_type": "price_reduction_planned",
            "notes": "Notes",
            "created_by": "Manager"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_action_reserved_vehicle_rejected(self):
        url = f"/api/vehicles/{self.reserved_vehicle.id}/actions/"
        data = {
            "action_type": "price_reduction_planned",
            "notes": "Notes",
            "created_by": "Manager"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vehicle_list_filtering(self):
        d2 = Dealership.objects.create(name="Dealership 2", location="Location 2")
        v2 = Vehicle.objects.create(
            dealership=d2,
            vin="VIN2",
            make="Honda",
            model="Civic",
            year=2022,
            intake_date=self.today - datetime.timedelta(days=95),
            price=18000.00,
            status=Vehicle.Status.IN_STOCK
        )
        
        url = "/api/vehicles/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 4)

        response = self.client.get(url, {"dealership_id": d2.id})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], v2.id)

        response = self.client.get(url, {"make": "Honda"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["make"], "Honda")

        response = self.client.get(url, {"make": "hOnDa"})
        self.assertEqual(len(response.data["results"]), 1)

        response = self.client.get(url, {"status": "sold"})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "sold")

        response = self.client.get(url, {"min_age_days": 90})
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], v2.id)

    def test_aging_vehicle_list(self):
        d2 = Dealership.objects.create(name="Dealership 2", location="Location 2")
        v_aging = Vehicle.objects.create(
            dealership=d2,
            vin="VINAGING",
            make="Honda",
            model="Civic",
            year=2022,
            intake_date=self.today - datetime.timedelta(days=95),
            price=18000.00,
            status=Vehicle.Status.IN_STOCK
        )
        
        url = "/api/vehicles/aging/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], v_aging.id)
        self.assertEqual(response.data["results"][0]["days_in_stock"], 95)
        self.assertTrue(response.data["results"][0]["is_aging"])

    def test_vehicle_detail(self):
        action1 = AgingAction.objects.create(
            vehicle=self.in_stock_vehicle,
            action_type="price_reduction_planned",
            notes="Note 1",
            created_by="John"
        )
        action2 = AgingAction.objects.create(
            vehicle=self.in_stock_vehicle,
            action_type="promotion_planned",
            notes="Note 2",
            created_by="Alice"
        )

        url = f"/api/vehicles/{self.in_stock_vehicle.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.in_stock_vehicle.id)
        self.assertIn("history", response.data)
        self.assertEqual(len(response.data["history"]), 2)
        self.assertEqual(response.data["history"][0]["id"], action2.id)
        self.assertEqual(response.data["history"][1]["id"], action1.id)

    def test_dealership_dropdown_list(self):
        url = "/api/dealerships/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.dealership.name)

    def test_vehicle_detail_write_methods_not_allowed(self):
        url = f"/api/vehicles/{self.in_stock_vehicle.id}/"
        
        # Test PUT returns 405
        response = self.client.put(url, {"make": "Modified"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PATCH returns 405
        response = self.client.patch(url, {"make": "Modified"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE returns 405
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_vehicle_list_n_plus_one_queries(self):
        # Clear existing vehicles to ensure a clean query measurement
        Vehicle.objects.all().delete()
        
        def create_vehicle(vin_suffix):
            v = Vehicle.objects.create(
                dealership=self.dealership,
                vin=f"VIN{vin_suffix}",
                make="Toyota",
                model="Camry",
                year=2023,
                intake_date=self.today,
                price=20000.00,
                status=Vehicle.Status.IN_STOCK
            )
            AgingAction.objects.create(
                vehicle=v,
                action_type="price_reduction_planned",
                notes="Notes",
                created_by="Manager"
            )
            return v
        
        # Create 1 vehicle
        create_vehicle("ONE")
        
        # Measure queries for 1 vehicle
        url = "/api/vehicles/"
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        
        with CaptureQueriesContext(connection) as ctx_one:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        query_count_for_one = len(ctx_one.captured_queries)
        
        # Create 4 more vehicles with actions (total 5)
        for i in range(4):
            create_vehicle(f"MORE{i}")
            
        with CaptureQueriesContext(connection) as ctx_five:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        query_count_for_five = len(ctx_five.captured_queries)
        
        # Assert query counts are exactly equal, proving no N+1 query issue
        self.assertEqual(query_count_for_one, query_count_for_five)
        # Expected query count should be 3: 
        # 1. SELECT COUNT(*) FROM vehicle (for pagination)
        # 2. SELECT vehicle (fetch items)
        # 3. SELECT agingaction WHERE vehicle_id IN (...) (prefetch)
        self.assertEqual(query_count_for_one, 3)




