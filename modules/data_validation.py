"""
EcoAudit AI — Data Validation Module

Validation functions for user inputs to prevent invalid data from
crashing calculations or producing misleading results.
"""
from typing import Any, Dict, List, Tuple, Optional


def validate_positive_number(value: Any, field_name: str) -> Tuple[bool, str]:
    """Validate that a value is a positive number."""
    try:
        num = float(value)
        if num < 0:
            return False, f"{field_name} cannot be negative (got {num})."
        return True, ""
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number."


def validate_positive_integer(value: Any, field_name: str) -> Tuple[bool, str]:
    """Validate that a value is a positive integer."""
    try:
        num = int(value)
        if num <= 0:
            return False, f"{field_name} must be a positive integer (got {num})."
        return True, ""
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid integer."


def validate_hours(value: Any, field_name: str = "Hours") -> Tuple[bool, str]:
    """Validate hours value (0-24)."""
    try:
        num = float(value)
        if num < 0 or num > 24:
            return False, f"{field_name} must be between 0 and 24 (got {num})."
        return True, ""
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number."


def validate_days(value: Any, field_name: str = "Days") -> Tuple[bool, str]:
    """Validate days value (0-31)."""
    try:
        num = int(value)
        if num < 0 or num > 31:
            return False, f"{field_name} must be between 0 and 31 (got {num})."
        return True, ""
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid integer."


def validate_appliance(appliance: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a complete appliance entry.
    
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    if not appliance.get('name', '').strip():
        errors.append("Appliance name is required.")
    
    valid, msg = validate_positive_integer(appliance.get('quantity', 0), "Quantity")
    if not valid:
        errors.append(msg)
    
    valid, msg = validate_positive_number(appliance.get('power_watts', -1), "Power rating (W)")
    if not valid:
        errors.append(msg)
    
    valid, msg = validate_hours(appliance.get('hours_per_day', -1), "Hours per day")
    if not valid:
        errors.append(msg)
    
    valid, msg = validate_days(appliance.get('days_per_month', -1), "Days per month")
    if not valid:
        errors.append(msg)
    
    return len(errors) == 0, errors


def validate_building_profile(profile: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate building profile data."""
    errors = []
    
    if profile.get('num_floors') is not None:
        valid, msg = validate_positive_integer(profile['num_floors'], "Number of floors")
        if not valid:
            errors.append(msg)
    
    if profile.get('num_units') is not None:
        valid, msg = validate_positive_integer(profile['num_units'], "Number of units")
        if not valid:
            errors.append(msg)
    
    if profile.get('built_up_area') is not None:
        valid, msg = validate_positive_number(profile['built_up_area'], "Built-up area")
        if not valid:
            errors.append(msg)
    
    if profile.get('num_occupants') is not None:
        valid, msg = validate_positive_integer(profile['num_occupants'], "Number of occupants")
        if not valid:
            errors.append(msg)
    
    if profile.get('tariff') is not None:
        valid, msg = validate_positive_number(profile['tariff'], "Electricity tariff")
        if not valid:
            errors.append(msg)
    
    return len(errors) == 0, errors


def validate_monthly_bills(bills: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate monthly bill entries."""
    errors = []
    for month, value in bills.items():
        if value is not None and value != 0:
            valid, msg = validate_positive_number(value, f"Bill for {month}")
            if not valid:
                errors.append(msg)
    return len(errors) == 0, errors


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator
