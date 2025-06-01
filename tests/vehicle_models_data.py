import pandas as pd
from pathlib import Path

# Load the CSV that the user supplied
csv_path = Path("data/vehicle_models.csv")
df = pd.read_csv(csv_path)

# Filter out invalid rows - only keep rows with valid vehicle IDs
valid_df = df[
    df["vehicle_id"].notna()  # Not NaN
    & df["vehicle_id"]
    .astype(str)
    .str.match(r"^(BEV|DSL)\d{3}$")  # Matches BEV001, DSL001 pattern
].copy()

print(f"Original rows: {len(df)}")
print(f"Valid vehicle rows: {len(valid_df)}")

# Define the dataclass template
header = """
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
'''.format(
    csv_name=csv_path.name
)

rows = []
for _, row in valid_df.iterrows():
    # Handle potential NaN values by converting to 0.0 for numeric fields
    def safe_float(value):
        return 0.0 if pd.isna(value) else float(value)

    def safe_str(value):
        return "" if pd.isna(value) else str(value)

    rows.append(
        f"    VehicleModel({row['vehicle_id']!r}, {safe_str(row['comparison_pair'])!r}, "
        f"{safe_str(row['weight_class'])!r}, {safe_str(row['drivetrain_type'])!r}, {safe_str(row['model_name'])!r}, "
        f"{safe_float(row['payload'])}, {safe_float(row['msrp'])}, {safe_float(row['range'])}, {safe_float(row['battery_capacity'])}, "
        f"{safe_float(row['kwh_perkm'])}, {safe_float(row['litres_perkm'])}, {safe_float(row['battery_replacement_perkw'])}, "
        f"{safe_float(row['maintenance_cost_perkm'])}, {safe_float(row['annual_registration'])}, {safe_float(row['annual_kms'])}, "
        f"{safe_float(row['noise_pollution_perkm'])}"
        "),"
    )

content = (
    header
    + "\n".join(rows)
    + """
]

BY_ID: Dict[str, VehicleModel] = {m.vehicle_id: m for m in ALL_MODELS}
"""
)

# Write the file
out_path = Path("data/vehicles.py")
out_path.write_text(content)

print(f"Generated file: {out_path}")
print(f"Generated {len(rows)} vehicle records")
