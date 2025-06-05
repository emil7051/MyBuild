# Constants for TCO Calculations

# Electricity Costs

RETAIL_CHARGING_PRICE = 0.30 # $/kWh
OFFPEAK_CHARGING_PRICE = 0.15 # $/kWh
SOLAR_CHARGING_PRICE = 0.04 # $/kWh
PUBLIC_CHARGING_PRICE = 0.50 # $/kWh

# Electricity Mix

RETAIL_PROPORTION = 0.0 # % (Proportion of charging done at workplace AC chargers)
OFFPEAK_PROPORTION = .86 # % (Proportion of charging done at workplace AC chargers during offpeak hours)
PUBLIC_PROPORTION = 0.14 # % (Proportion of charging done at public DC fast chargers)
SOLAR_PROPORTION = 0.0 # % (Proportion of charging done at home via solar and storage)

# Rigid Truck Electricity Mix

RIGID_RETAIL_PROPORTION = 0.00 # (Assuming most charging takes place on overnight cycles)
RIGID_OFFPEAK_PROPORTION = 0.86 # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
RIGID_PUBLIC_PROPORTION = 0.14 # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
RIGID_SOLAR_PROPORTION = 0.00 # (Assuming no investment in solar infrastructure)

# Articulated Truck Electricity Mix

ART_RETAIL_PROPORTION = 0.00 # (Assuming most charging takes place on overnight cycles)
ART_OFFPEAK_PROPORTION = 0.67 # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
ART_PUBLIC_PROPORTION = 0.33 # (A weighted average calculated by using the trip proportions indicated by the Survey of Motor Vehicle Use, and typical charging strategies from Scania eMobility Hub)
ART_SOLAR_PROPORTION = 0.00 # (Assuming no investment in solar infrastructure)

# Charger Costs

SOLAR_PANEL_INSTALLATION = 1285 # $/kwh DC (single-axis-tracking solar behind the meter)
SOLAR_MAINTENANCE = 0.15 # $/kwh/year
STORAGE_INSTALLATION = 423 # $/kwh (4 hour lithium-ion battery energy-storage system)
STORAGE_MAINTENANCE = 0.025 # % (AEMO/NREL rule - percentage of CAPEX/year)
INFRASTRUCTURE_LIFE = 15 # Years
CHARGER_COST = 300000 # AUD (CCS high-power DC fast charger, includes cabinet, dispenser, cooling, and typical electrical work - Smart Freight Media Centre)GRID_UPGRADE = 1000000  # AUD 

# Fuel Costs

DIESEL_PRICE = 2.05 # $/litre (average diesel retail price from the Australian Institute of Petroleum, 2c per litre added for AdBlue)

# Labour Costs

HOURLY_WAGE = 47 # $/hour (Award wafge rate grade 8, with overtime based on a 49 hour work week, superannuation, leave loading, and workers comp)

# Emissions Factors

RETAIL_CHARGING_EMISSIONS = 0.7 # kgCO2e/kWh (current grid emissions)
OFFPEAK_CHARGING_EMISSIONS = 0.7 # kgCO2e/kWh (same as retail)
SOLAR_CHARGING_EMISSIONS = 0.04 # kgCO2e/kWh (lifecycle emissions of solar panels)
PUBLIC_CHARGING_EMISSIONS = 0.7 # kgCO2e/kWh (same as retail)
DIESEL_EMISSIONS = 2.68 # kgCO2e/litre

# Vehicle Operating Parameters

VEHICLE_LIFE = 15  # Years
RIGID_ANNUAL_KMS = 23000 # kms/year (SMVU Data)
ART_ANNUAL_KMS = 84000 # kms/year (SMVU Data)

# Payload Penalty - Based on BITRE freight rates
FREIGHT_RATE_RIGID = 0.17  # $/tonne-km (BITRE 2017 rate for rigid truck freight transport)
FREIGHT_RATE_ARTICULATED = 0.26  # $/tonne-km (BITRE 2017 rate for articulated truck freight transport)
PAYLOAD_UTILISATION_FACTOR = 0.85  # Trucks typically run at 85% payload capacity on average

# Insurance Costs

INSURANCE_RATE_BEV = 0.035 # % (annual insurance as a percentage of vehicle price for BEV)
INSURANCE_RATE_DSL = 0.0315 # % (annual insurance as a percentage of vehicle price for Diesel, based on Transport Industry Council guidelines)
OTHER_INSURANCE = 2000 # $/year (Permits, TAC fees, goods insurance, PLI, personal income insurance)

# Mainteannce Costs

RIGID_BEV_MAINTENANCE_COST = 0.10 # $/km (check this with T&E)
ART_BEV_MAINTENANCE_COST = 0.19 # $/km (check this with T&E)
RIGID_DSL_MAINTENANCE_COST = 0.18 # $/km (check this with T&E)
ART_DSL_MAINTENANCE_COST = 0.28 # $/km (check this with T&E)

# Financial Parameters

INFLATION_RATE = 0.025 # % (general annual inflation rate)
DISCOUNT_RATE = 0.05 # % (for NPV calculations)
INTEREST_RATE = 0.06 # % (for financing calculations, based on commercial rates for trucks available on financing website Savvy)
DEPRECIATION_RATE_FIRST_YEAR = 0.20 # % (first year depreciation)
DEPRECIATION_RATE_ONGOING = 0.10 # % (annual depreciation after first year)
FINANCING_TERM = 5 # Years
DOWN_PAYMENT_RATE = 0.20 # % (percentage of price paid upfront)

# Battery

BATTERY_REPLACEMENT_COST = 130 # $/kWh (cost to replace battery cells)
BATTERY_RECYCLE_VALUE = 13 # $/kWh (value obtained from recycling old battery)
BATTERY_DEGRADATION_RATE = 0.025 # %/year (annual capacity loss)

# Government Fees, Taxes, Incentives

FUEL_TAX_CREDIT = 0.203 # $/litre (included in DIESEL_PRICE but granted back as a rebate)
ROAD_USER_CHARGE = 0.305 # $/litre (included in DIESEL_PRICE, may need to apply to BEV's in some way)
STAMP_DUTY_RATE = 0.03 # % (percentage of vehicle price, assumed to be 3% based on freightmetrics.com.au)

# Other
HOURS_IN_YEAR = 8760 # Number of hours in a year
DAYS_IN_YEAR = 365 # Number of days in a year
WEEKS_IN_YEAR = 52 # Number of weeks in a year
MONTHS_IN_YEAR = 12 # Number of months in a year
