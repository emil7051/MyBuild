#!/usr/bin/env python
"""Pre-deployment validation script to ensure all imports work correctly."""

import sys
from pathlib import Path

def validate_backend_imports():
    """Validate that all backend models can be imported."""
    print("🔍 Validating backend imports...")
    try:
        from backend.app.models import (
            CalculationRequest,
            CalculationResponse,
            ComparisonRequest,
            CostBreakdown,
            CostOverride,
            VehicleParamOverride,
            VehicleSummary,
            VehicleDetail,
        )
        print("✓ All backend models import successfully")
        print(f"  - VehicleParamOverride has {len(VehicleParamOverride.model_fields)} fields")
        return True
    except ImportError as e:
        print(f"✗ Backend import error: {e}")
        return False

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
