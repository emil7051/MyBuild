API schema casing is mixed by model:
- Vehicles endpoints return snake_case fields (VehicleSummary/VehicleDetail: vehicle_id, model_name, drivetrain_type, etc.).
- Session payload/response uses camelCase aliases for wizardData, sessionId, operatorProfile, and dutyCycle.longHaul; results entries remain snake_case from CalculationResponse.
- Analytics summary uses camelCase aliases (totalSessions, completedSessions, etc.).
API.md was updated to reflect these shapes.