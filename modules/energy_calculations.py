"""
EcoAudit AI — Energy Calculation Engine

Provides transparent energy consumption calculations for residential buildings.
All calculations use explicit formulas with clearly stated assumptions.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any


def calculate_daily_consumption_kwh(quantity: int, power_watts: float, hours_per_day: float) -> float:
    """Calculate estimated daily energy consumption for an appliance.
    
    Formula: Quantity × Rated Power (W) × Hours Used per Day ÷ 1000
    
    Args:
        quantity: Number of appliance units
        power_watts: Rated power per unit in watts
        hours_per_day: Average hours of use per day
    
    Returns:
        Estimated daily consumption in kWh
    
    Raises:
        ValueError: If any input is negative or quantity is zero
    """
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    if power_watts < 0:
        raise ValueError(f"Power rating cannot be negative, got {power_watts}")
    if hours_per_day < 0 or hours_per_day > 24:
        raise ValueError(f"Hours per day must be between 0 and 24, got {hours_per_day}")
    
    return quantity * power_watts * hours_per_day / 1000.0


def calculate_monthly_consumption_kwh(quantity: int, power_watts: float, 
                                       hours_per_day: float, days_per_month: int) -> float:
    """Calculate estimated monthly energy consumption for an appliance.
    
    Formula: Quantity × Rated Power (W) × Hours Used per Day × Days Used per Month ÷ 1000
    
    Args:
        quantity: Number of appliance units
        power_watts: Rated power per unit in watts  
        hours_per_day: Average hours of use per day
        days_per_month: Number of days the appliance is used per month
    
    Returns:
        Estimated monthly consumption in kWh
    
    Raises:
        ValueError: If any input is invalid
    """
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    if power_watts < 0:
        raise ValueError(f"Power rating cannot be negative, got {power_watts}")
    if hours_per_day < 0 or hours_per_day > 24:
        raise ValueError(f"Hours per day must be between 0 and 24, got {hours_per_day}")
    if days_per_month < 0 or days_per_month > 31:
        raise ValueError(f"Days per month must be between 0 and 31, got {days_per_month}")
    
    return quantity * power_watts * hours_per_day * days_per_month / 1000.0


def calculate_annual_consumption_kwh(monthly_consumption_kwh: float) -> float:
    """Calculate estimated annual energy consumption.
    
    Formula: Monthly consumption × 12
    Assumption: Monthly usage pattern remains constant throughout the year.
    
    Args:
        monthly_consumption_kwh: Estimated monthly consumption in kWh
    
    Returns:
        Estimated annual consumption in kWh
    """
    if monthly_consumption_kwh < 0:
        raise ValueError(f"Monthly consumption cannot be negative, got {monthly_consumption_kwh}")
    return monthly_consumption_kwh * 12.0


def calculate_electricity_cost(consumption_kwh: float, tariff_per_kwh: float) -> float:
    """Calculate estimated electricity cost.
    
    Args:
        consumption_kwh: Energy consumption in kWh
        tariff_per_kwh: Electricity tariff in ₹/kWh
    
    Returns:
        Estimated cost in ₹
    """
    if consumption_kwh < 0:
        raise ValueError(f"Consumption cannot be negative, got {consumption_kwh}")
    if tariff_per_kwh < 0:
        raise ValueError(f"Tariff cannot be negative, got {tariff_per_kwh}")
    return consumption_kwh * tariff_per_kwh


def process_appliance_inventory(appliances: List[Dict[str, Any]]) -> pd.DataFrame:
    """Process a list of appliances and compute consumption metrics.
    
    Args:
        appliances: List of dicts with keys:
            - name (str): Appliance name
            - quantity (int): Number of units
            - power_watts (float): Rated power per unit in watts
            - hours_per_day (float): Average daily usage hours
            - days_per_month (int): Days used per month
            - category (str, optional): Usage category
            - efficiency_info (str, optional): Efficiency details
            - power_source (str, optional): 'Measured', 'User-provided', or 'Assumed'
    
    Returns:
        DataFrame with columns: name, quantity, power_watts, hours_per_day, days_per_month,
        daily_kwh, monthly_kwh, annual_kwh, percentage_contribution, category, 
        efficiency_info, power_source
    """
    if not appliances:
        return pd.DataFrame(columns=['name', 'quantity', 'power_watts', 'hours_per_day',
                                      'days_per_month', 'daily_kwh', 'monthly_kwh', 
                                      'annual_kwh', 'percentage_contribution',
                                      'category', 'efficiency_info', 'power_source'])
    
    results = []
    for app in appliances:
        name = app.get('name', 'Unknown')
        qty = app.get('quantity', 1)
        power = app.get('power_watts', 0)
        hours = app.get('hours_per_day', 0)
        days = app.get('days_per_month', 30)
        category = app.get('category', 'General')
        eff_info = app.get('efficiency_info', 'Not specified')
        power_src = app.get('power_source', 'Assumed')
        
        try:
            daily = calculate_daily_consumption_kwh(qty, power, hours)
            monthly = calculate_monthly_consumption_kwh(qty, power, hours, days)
            annual = calculate_annual_consumption_kwh(monthly)
        except ValueError:
            daily = 0.0
            monthly = 0.0
            annual = 0.0
        
        results.append({
            'name': name,
            'quantity': qty,
            'power_watts': power,
            'hours_per_day': hours,
            'days_per_month': days,
            'daily_kwh': round(daily, 3),
            'monthly_kwh': round(monthly, 3),
            'annual_kwh': round(annual, 3),
            'category': category,
            'efficiency_info': eff_info,
            'power_source': power_src
        })
    
    df = pd.DataFrame(results)
    
    total_monthly = df['monthly_kwh'].sum()
    if total_monthly > 0:
        df['percentage_contribution'] = round(df['monthly_kwh'] / total_monthly * 100, 2)
    else:
        df['percentage_contribution'] = 0.0
    
    return df


def get_consumption_summary(df: pd.DataFrame, tariff: float = 7.0) -> Dict[str, float]:
    """Calculate aggregate consumption summary from processed appliance data.
    
    Args:
        df: DataFrame from process_appliance_inventory
        tariff: Electricity tariff in ₹/kWh
    
    Returns:
        Dict with total_daily_kwh, total_monthly_kwh, total_annual_kwh,
        monthly_cost_inr, annual_cost_inr, tariff_used
    """
    if df.empty:
        return {
            'total_daily_kwh': 0.0,
            'total_monthly_kwh': 0.0, 
            'total_annual_kwh': 0.0,
            'monthly_cost_inr': 0.0,
            'annual_cost_inr': 0.0,
            'tariff_used': tariff
        }
    
    total_daily = round(df['daily_kwh'].sum(), 3)
    total_monthly = round(df['monthly_kwh'].sum(), 3)
    total_annual = round(df['annual_kwh'].sum(), 3)
    monthly_cost = round(calculate_electricity_cost(total_monthly, tariff), 2)
    annual_cost = round(calculate_electricity_cost(total_annual, tariff), 2)
    
    return {
        'total_daily_kwh': total_daily,
        'total_monthly_kwh': total_monthly,
        'total_annual_kwh': total_annual,
        'monthly_cost_inr': monthly_cost,
        'annual_cost_inr': annual_cost,
        'tariff_used': tariff
    }


def get_top_consumers(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Get the top N energy-consuming appliances."""
    if df.empty:
        return df
    return df.nlargest(top_n, 'monthly_kwh')[['name', 'monthly_kwh', 'annual_kwh', 'percentage_contribution']]


def compare_bill_vs_calculated(calculated_monthly_kwh: float, 
                                 billed_monthly_kwh: float) -> Dict[str, Any]:
    """Compare calculated appliance-based consumption with actual billed consumption.
    
    Args:
        calculated_monthly_kwh: Total estimated monthly consumption from appliance inventory
        billed_monthly_kwh: Actual billed monthly consumption in kWh
    
    Returns:
        Dict with calculated, billed, absolute_difference, percentage_difference,
        possible_reasons
    """
    abs_diff = round(abs(calculated_monthly_kwh - billed_monthly_kwh), 2)
    
    if billed_monthly_kwh > 0:
        pct_diff = round((abs_diff / billed_monthly_kwh) * 100, 2)
    elif calculated_monthly_kwh > 0:
        pct_diff = round((abs_diff / calculated_monthly_kwh) * 100, 2)
    else:
        pct_diff = 0.0
    
    reasons = []
    if calculated_monthly_kwh > billed_monthly_kwh:
        reasons = [
            "Actual usage hours may be lower than assumed hours.",
            "Some appliances may have duty cycles (e.g., refrigerators, ACs) that reduce average power draw below rated power.",
            "Some appliances may not be used every day of the month.",
            "Power ratings used may be higher than actual operating power."
        ]
    elif billed_monthly_kwh > calculated_monthly_kwh:
        reasons = [
            "Some appliances may not be included in the inventory.",
            "Common-area or shared electricity loads may be included in the bill.",
            "Actual usage hours may be higher than estimated.",
            "Standby power consumption of appliances is not accounted for.",
            "Meter measurement includes all connected loads, some of which may be overlooked."
        ]
    else:
        reasons = ["Calculated and billed consumption match closely."]
    
    return {
        'calculated_monthly_kwh': round(calculated_monthly_kwh, 2),
        'billed_monthly_kwh': round(billed_monthly_kwh, 2),
        'absolute_difference_kwh': abs_diff,
        'percentage_difference': pct_diff,
        'calculated_higher': calculated_monthly_kwh > billed_monthly_kwh,
        'possible_reasons': reasons
    }


def analyze_monthly_bills(monthly_bills: Dict[str, float], tariff: float = 7.0) -> Dict[str, Any]:
    """Analyze monthly electricity bill data.
    
    Args:
        monthly_bills: Dict mapping month names to consumption in kWh.
                       Example: {'January': 350, 'February': 320, ...}
        tariff: Electricity tariff in ₹/kWh
    
    Returns:
        Dict with analysis results including trends, averages, costs.
    """
    if not monthly_bills:
        return {'error': 'No monthly bill data provided'}
    
    # Filter out zero/None entries
    valid_bills = {k: v for k, v in monthly_bills.items() if v is not None and v > 0}
    
    if not valid_bills:
        return {'error': 'No valid monthly bill data found'}
    
    months = list(valid_bills.keys())
    values = list(valid_bills.values())
    
    avg_consumption = round(sum(values) / len(values), 2)
    max_month = months[values.index(max(values))]
    min_month = months[values.index(min(values))]
    total_for_period = round(sum(values), 2)
    
    # Month-to-month changes
    changes = []
    for i in range(1, len(values)):
        change = round(values[i] - values[i-1], 2)
        pct_change = round((change / values[i-1]) * 100, 2) if values[i-1] > 0 else 0.0
        changes.append({
            'from': months[i-1],
            'to': months[i],
            'change_kwh': change,
            'change_percent': pct_change
        })
    
    return {
        'months_available': len(valid_bills),
        'data': valid_bills,
        'average_monthly_kwh': avg_consumption,
        'highest_month': max_month,
        'highest_consumption_kwh': round(max(values), 2),
        'lowest_month': min_month,
        'lowest_consumption_kwh': round(min(values), 2),
        'total_for_period_kwh': total_for_period,
        'estimated_period_cost_inr': round(total_for_period * tariff, 2),
        'estimated_avg_monthly_cost_inr': round(avg_consumption * tariff, 2),
        'month_to_month_changes': changes,
        'is_complete_year': len(valid_bills) == 12,
        'data_note': f"Analysis based on {len(valid_bills)} month(s) of available data." + 
                     ("" if len(valid_bills) == 12 else " This is not a complete annual record.")
    }


def calculate_savings_for_intervention(baseline_consumption_kwh: float,
                                        reduction_fraction: float,
                                        tariff: float = 7.0,
                                        implementation_cost: Optional[float] = None) -> Dict[str, Any]:
    """Calculate estimated savings from an energy-saving intervention.
    
    Args:
        baseline_consumption_kwh: Monthly baseline consumption in kWh for the relevant appliance(s)
        reduction_fraction: Assumed fractional reduction (0.0 to 1.0)
        tariff: Electricity tariff in ₹/kWh
        implementation_cost: Optional cost of implementing the intervention in ₹
    
    Returns:
        Dict with estimated monthly and annual savings in kWh and ₹
    """
    if reduction_fraction < 0 or reduction_fraction > 1:
        raise ValueError(f"Reduction fraction must be between 0 and 1, got {reduction_fraction}")
    if baseline_consumption_kwh < 0:
        raise ValueError(f"Baseline consumption cannot be negative")
    
    monthly_kwh_saved = round(baseline_consumption_kwh * reduction_fraction, 3)
    monthly_cost_saved = round(monthly_kwh_saved * tariff, 2)
    annual_kwh_saved = round(monthly_kwh_saved * 12, 3)
    annual_cost_saved = round(monthly_cost_saved * 12, 2)
    
    result = {
        'baseline_monthly_kwh': round(baseline_consumption_kwh, 3),
        'reduction_fraction': reduction_fraction,
        'reduction_percentage': round(reduction_fraction * 100, 1),
        'monthly_kwh_saved': monthly_kwh_saved,
        'annual_kwh_saved': annual_kwh_saved,
        'monthly_cost_saved_inr': monthly_cost_saved,
        'annual_cost_saved_inr': annual_cost_saved,
        'tariff_used': tariff,
        'assumption_note': f"Estimated savings assume a {round(reduction_fraction*100,1)}% reduction in the relevant baseline consumption. Actual savings may vary."
    }
    
    if implementation_cost is not None and implementation_cost > 0:
        if annual_cost_saved > 0:
            payback_months = round(implementation_cost / monthly_cost_saved, 1) if monthly_cost_saved > 0 else float('inf')
            result['implementation_cost_inr'] = implementation_cost
            result['payback_months'] = payback_months
            result['payback_years'] = round(payback_months / 12, 1)
        else:
            result['implementation_cost_inr'] = implementation_cost
            result['payback_months'] = None
            result['payback_years'] = None
            result['payback_note'] = 'Insufficient data to calculate payback period.'
    
    return result
