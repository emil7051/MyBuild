#!/usr/bin/env python
"""Pre-deployment validation script to ensure all imports work correctly."""

from importlib import import_module
from pathlib import Path
import sys


def validate_backend_imports():
    """Validate that all backend models can be imported."""
    print("🔍 Validating backend imports...")
    try:
        models_module = import_module("backend.app.models")
    except ImportError as exc:
        print(f"✗ Backend import error: {exc}")
        return False

    model_names = [
        "CalculationRequest",
        "CalculationResponse",
        "ComparisonRequest",
        "CostBreakdown",
        "CostOverride",
        "VehicleDetail",
        "VehicleParamOverride",
        "VehicleSummary",
    ]

    try:
        resolved_models = {name: getattr(models_module, name) for name in model_names}
    except AttributeError as exc:
        print(f"✗ Missing model attribute: {exc}")
        return False

    print("✓ All backend models import successfully")
    vehicle_param_override = resolved_models["VehicleParamOverride"]
    print(
        f"  - VehicleParamOverride has {len(vehicle_param_override.model_fields)} fields"
    )
    return True


def validate_backend_app():
    """Validate that the FastAPI app can be imported."""
    print("\n🔍 Validating FastAPI app...")
    try:
        from backend.app.main import app

        print(f"✓ FastAPI app imports successfully ({len(app.routes)} routes)")
        return True
    except Exception as e:
        print(f"✗ FastAPI app import error: {e}")
        return False


def validate_frontend_build():
    """Check if frontend build directory exists."""
    print("\n🔍 Checking frontend build...")
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        files = list(frontend_dist.glob("**/*"))
        print(f"✓ Frontend build exists ({len(files)} files)")
        return True
    else:
        print("⚠ Frontend build not found (run 'cd frontend && npm run build')")
        return False


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("PRE-DEPLOYMENT VALIDATION")
    print("=" * 60)

    checks = [
        validate_backend_imports(),
        validate_backend_app(),
        validate_frontend_build(),
    ]

    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All validation checks passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validation checks failed!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
