"""
Vehicle data for TCO analysis.

- VehicleModel dataclass
- ALL_MODELS - list[VehicleModel]
- BY_ID - dict[str, VehicleModel]  (for O(1) lookup)
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass(slots=True, frozen=True)
class VehicleModel:
    vehicle_id: str
    comparison_pair: str
    weight_class: str
    drivetrain_type: str
    model_name: str
    payload: float
    msrp: float
    range_km: float
    battery_capacity_kwh: float
    kwh_per_km: float
    litres_per_km: float
    battery_replacement_per_kw: float
    maintenance_cost_per_km: float
    annual_registration: float
    annual_kms: float
    noise_pollution_per_km: float


ALL_MODELS: List[VehicleModel] = [
    VehicleModel('BEV001', 'DSL001', 'Light Rigid', 'BEV', 'Jac N75', 4.0, 176500.0, 220.0, 100.0, 0.48, 0.0, 130.0, 0.05, 653.0, 23000.0, 0.004),
    VehicleModel('BEV002', 'DSL002', 'Light Rigid', 'BEV', 'Hyundai Mighty Electric', 4.0, 150000.0, 200.0, 97.0, 0.48, 0.0, 130.0, 0.05, 653.0, 23000.0, 0.004),
    VehicleModel('BEV003', 'DSL003', 'Light Rigid', 'BEV', 'Jac N90', 5.0, 150000.0, 180.0, 107.0, 0.61, 0.0, 130.0, 0.05, 653.0, 23000.0, 0.004),
    VehicleModel('BEV004', 'DSL004', 'Medium Rigid', 'BEV', 'Volvo FL', 10.5, 200000.0, 300.0, 264.0, 1.09, 0.0, 130.0, 0.08, 653.0, 23000.0, 0.006),
    VehicleModel('BEV005', 'DSL005', 'Medium Rigid', 'BEV', 'MB eActros 300', 22.0, 400000.0, 300.0, 336.0, 1.09, 0.0, 130.0, 0.08, 653.0, 23000.0, 0.006),
    VehicleModel('BEV006', 'DSL006', 'Articulated', 'BEV', 'MB eActros 600', 42.0, 600000.0, 500.0, 621.0, 1.2, 0.0, 130.0, 0.12, 6872.0, 84000.0, 0.009),
    VehicleModel('BEV007', 'DSL007', 'Articulated', 'BEV', 'Volvo FH', 42.0, 450000.0, 300.0, 540.0, 1.2, 0.0, 130.0, 0.12, 6872.0, 84000.0, 0.009),
    VehicleModel('BEV008', 'DSL008', 'Articulated', 'BEV', 'Scania 45R', 42.0, 320000.0, 390.0, 624.0, 1.2, 0.0, 130.0, 0.12, 6872.0, 84000.0, 0.009),
    VehicleModel('DSL001', 'BEV001', 'Light Rigid', 'Diesel', 'Hino 300', 4.5, 80000.0, 600.0, 0.0, 0.0, 0.28, 0.0, 0.2, 653.0, 23000.0, 0.01),
    VehicleModel('DSL002', 'BEV002', 'Light Rigid', 'Diesel', 'Hyundai Mighty', 4.0, 75000.0, 600.0, 0.0, 0.0, 0.28, 0.0, 0.02, 653.0, 23000.0, 0.01),
    VehicleModel('DSL003', 'BEV003', 'Light Rigid', 'Diesel', 'Hino 500', 6.0, 130000.0, 600.0, 0.0, 0.0, 0.28, 0.0, 0.02, 653.0, 23000.0, 0.01),
    VehicleModel('DSL004', 'BEV004', 'Medium Rigid', 'Diesel', 'Volvo FE', 12.0, 220000.0, 600.0, 0.0, 0.0, 0.32, 0.0, 0.025, 653.0, 23000.0, 0.017),
    VehicleModel('DSL005', 'BEV005', 'Medium Rigid', 'Diesel', 'MB Actros', 25.0, 270000.0, 1400.0, 0.0, 0.0, 0.32, 0.0, 0.025, 653.0, 23000.0, 0.017),
    VehicleModel('DSL006', 'BEV006', 'Articulated', 'Diesel', 'MB Actros', 50.0, 270000.0, 1400.0, 0.0, 0.0, 0.35, 0.0, 0.03, 6872.0, 84000.0, 0.025),
    VehicleModel('DSL007', 'BEV007', 'Articulated', 'Diesel', 'Volvo FH', 50.0, 280000.0, 2000.0, 0.0, 0.0, 0.35, 0.0, 0.03, 6872.0, 84000.0, 0.025),
    VehicleModel('DSL008', 'BEV008', 'Articulated', 'Diesel', 'Scania R560', 50.0, 300000.0, 1500.0, 0.0, 0.0, 0.35, 0.0, 0.03, 6872.0, 84000.0, 0.025),
]

BY_ID: Dict[str, VehicleModel] = {m.vehicle_id: m for m in ALL_MODELS}
