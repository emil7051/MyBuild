"""Test imports to debug the issue"""

try:
    print("Testing numpy_financial import...")
    import numpy_financial as npf
    print("✓ numpy_financial imported successfully")
except ImportError as e:
    print(f"✗ Failed to import numpy_financial: {e}")

try:
    print("\nTesting calculations import...")
    from calculations.calculations import vehicle_data
    print("✓ calculations imported successfully")
except ImportError as e:
    print(f"✗ Failed to import calculations: {e}")

try:
    print("\nTesting reports import...")
    from reports import calculate_payback_analysis
    print("✓ reports imported successfully")
except ImportError as e:
    print(f"✗ Failed to import reports: {e}")

print("\nAll imports tested.")
