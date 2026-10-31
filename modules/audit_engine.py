"""
EcoAudit AI — Audit Engine

Generates energy audit findings based on building profile and appliance data.
Findings are categorized by confidence level and data source.
"""
from typing import Dict, List, Any, Optional
import pandas as pd


def generate_audit_findings(appliance_df: pd.DataFrame,
                            building_profile: Dict[str, Any],
                            bill_analysis: Optional[Dict[str, Any]] = None,
                            consumption_summary: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, str]]]:
    """Generate categorized energy audit findings.
    
    Returns:
        Dict with keys:
        - 'data_supported': Findings directly supported by user data
        - 'assumption_based': Findings based on assumptions
        - 'requires_inspection': Findings that need additional measurement
    """
    findings = {
        'data_supported': [],
        'assumption_based': [],
        'requires_inspection': []
    }
    
    if appliance_df.empty:
        findings['data_supported'].append({
            'category': 'Data Completeness',
            'finding': 'No appliance data has been entered. Please add appliances to receive energy audit findings.',
            'severity': 'info',
            'icon': '📋'
        })
        return findings
    
    # --- Data-supported findings ---
    
    # 1. Identify top consumers
    total_monthly = appliance_df['monthly_kwh'].sum()
    if total_monthly > 0:
        top_consumers = appliance_df.nlargest(3, 'monthly_kwh')
        for _, row in top_consumers.iterrows():
            pct = row['percentage_contribution']
            if pct >= 20:
                findings['data_supported'].append({
                    'category': 'High Energy Consumer',
                    'finding': f"{row['name']} accounts for approximately {pct:.1f}% of estimated monthly electricity consumption ({row['monthly_kwh']:.1f} kWh/month). This is one of the largest energy consumers in the inventory.",
                    'severity': 'warning' if pct >= 30 else 'info',
                    'icon': '⚡'
                })
    
    # 2. Check for high usage hours
    high_usage = appliance_df[appliance_df['hours_per_day'] >= 18]
    for _, row in high_usage.iterrows():
        if row['name'].lower() not in ['refrigerator', 'fridge', 'router', 'modem', 'wifi']:
            findings['data_supported'].append({
                'category': 'High Operating Hours',
                'finding': f"{row['name']} is recorded as operating {row['hours_per_day']} hours/day. If this is accurate, consider whether usage can be reduced during off-peak hours or idle periods.",
                'severity': 'warning',
                'icon': '🕐'
            })
    
    # 3. Lighting assessment
    lighting_apps = appliance_df[appliance_df['name'].str.lower().str.contains(
        'light|bulb|lamp|tube|cfl', na=False)]
    if not lighting_apps.empty:
        non_led = lighting_apps[~lighting_apps['name'].str.lower().str.contains('led', na=False)]
        if not non_led.empty:
            findings['data_supported'].append({
                'category': 'Lighting Efficiency',
                'finding': f"The inventory includes {len(non_led)} non-LED lighting entries. Replacing incandescent or CFL lights with LED alternatives can reduce lighting energy consumption by 50-80%.",
                'severity': 'warning',
                'icon': '💡'
            })
        
        total_lighting = lighting_apps['monthly_kwh'].sum()
        lighting_pct = (total_lighting / total_monthly * 100) if total_monthly > 0 else 0
        if lighting_pct > 25:
            findings['data_supported'].append({
                'category': 'Lighting Load',
                'finding': f"Lighting accounts for approximately {lighting_pct:.1f}% of estimated consumption. This is relatively high for a residential building. Review operating hours and fixture efficiency.",
                'severity': 'info',
                'icon': '💡'
            })
    
    # 4. AC assessment
    ac_apps = appliance_df[appliance_df['name'].str.lower().str.contains(
        'air.?condition|ac|split|window.?ac', na=False)]
    if not ac_apps.empty:
        ac_monthly = ac_apps['monthly_kwh'].sum()
        ac_pct = (ac_monthly / total_monthly * 100) if total_monthly > 0 else 0
        findings['data_supported'].append({
            'category': 'Cooling Load',
            'finding': f"Air conditioning accounts for approximately {ac_pct:.1f}% of estimated consumption ({ac_monthly:.1f} kWh/month). Cooling is typically a major consumer in Indian residences. Setting thermostat to 24-26°C and ensuring regular maintenance can improve efficiency.",
            'severity': 'warning' if ac_pct > 30 else 'info',
            'icon': '❄️'
        })
        for _, row in ac_apps.iterrows():
            if row['hours_per_day'] > 10:
                findings['data_supported'].append({
                    'category': 'Cooling Usage',
                    'finding': f"{row['name']} is recorded as running {row['hours_per_day']} hours/day. Consider using timers, fan-assisted ventilation during cooler hours, and ensuring windows and doors are properly sealed while AC is running.",
                    'severity': 'info',
                    'icon': '❄️'
                })
    
    # 5. Bill comparison findings
    if bill_analysis and consumption_summary:
        calc_monthly = consumption_summary.get('total_monthly_kwh', 0)
        if 'average_monthly_kwh' in bill_analysis:
            billed = bill_analysis['average_monthly_kwh']
            if billed > 0 and calc_monthly > 0:
                diff_pct = abs(calc_monthly - billed) / billed * 100
                if diff_pct > 20:
                    direction = "higher" if calc_monthly > billed else "lower"
                    findings['data_supported'].append({
                        'category': 'Bill Discrepancy',
                        'finding': f"Estimated appliance consumption ({calc_monthly:.1f} kWh/month) is approximately {diff_pct:.0f}% {direction} than the average billed consumption ({billed:.1f} kWh/month). See the bill comparison section for possible explanations.",
                        'severity': 'warning',
                        'icon': '📊'
                    })
    
    # --- Assumption-based findings ---
    
    # 6. Standby power
    electronics = appliance_df[appliance_df['name'].str.lower().str.contains(
        'tv|television|computer|laptop|monitor|printer|gaming|charger|set.?top|router|modem', na=False)]
    if len(electronics) >= 2:
        findings['assumption_based'].append({
            'category': 'Standby Consumption',
            'finding': f"The inventory includes {len(electronics)} electronic devices. These devices typically draw 1-15W in standby mode. Using power strips with switches to disconnect standby loads could reduce total consumption by an estimated 3-10%. This estimate is based on general industry data, not measurements.",
            'severity': 'info',
            'icon': '🔌'
        })
    
    # 7. Water heater
    water_heaters = appliance_df[appliance_df['name'].str.lower().str.contains(
        'water.?heater|geyser', na=False)]
    if not water_heaters.empty:
        findings['assumption_based'].append({
            'category': 'Water Heating',
            'finding': "Electric water heaters are high-power appliances. Using a timer, reducing heating duration, setting the thermostat to 50-55°C, and considering a solar water heater (where feasible) can significantly reduce consumption. A solar water heater may reduce electric water-heating energy by 60-80% (assumption based on general solar potential in India).",
            'severity': 'info',
            'icon': '🚿'
        })
    
    # --- Requires inspection ---
    
    # 8. Building envelope observations
    profile = building_profile or {}
    if profile:
        age = profile.get('building_age')
        if age and age > 15:
            findings['requires_inspection'].append({
                'category': 'Building Age',
                'finding': f"The building is reported as approximately {age} years old. Older buildings may benefit from insulation assessment, window sealing inspection, and evaluation of wiring efficiency. A professional energy audit can identify specific improvement opportunities.",
                'severity': 'info',
                'icon': '🏠'
            })
        
        if profile.get('roof_type') and 'insulation' not in str(profile.get('roof_insulation', '')).lower():
            findings['requires_inspection'].append({
                'category': 'Roof Insulation',
                'finding': "Roof insulation status has not been confirmed. In Indian climate conditions, proper roof insulation can reduce cooling loads by 10-30%. A site inspection would determine the current insulation level and improvement potential.",
                'severity': 'info',
                'icon': '🏗️'
            })
        
        if profile.get('window_area'):
            findings['requires_inspection'].append({
                'category': 'Window Assessment',
                'finding': f"Window area is reported as approximately {profile['window_area']} sq.m. Window orientation, glazing type, and shading significantly affect solar heat gain. A detailed assessment of window properties and shading options may identify cooling-load reduction opportunities.",
                'severity': 'info',
                'icon': '🪟'
            })
        
        if not profile.get('solar_installation'):
            findings['requires_inspection'].append({
                'category': 'Solar Potential',
                'finding': "No solar installation is reported. Depending on roof area, orientation, shading, and local regulations, rooftop solar may be worth evaluating. A site-specific solar feasibility study is recommended to determine actual potential and costs.",
                'severity': 'info',
                'icon': '☀️'
            })
        
        if profile.get('natural_ventilation') == 'Poor' or profile.get('natural_ventilation') == 'Limited':
            findings['requires_inspection'].append({
                'category': 'Ventilation',
                'finding': "Natural ventilation is reported as limited. Improving cross-ventilation or using ceiling fans effectively can reduce air-conditioning dependency during moderate weather. A professional assessment can recommend specific ventilation improvements.",
                'severity': 'info',
                'icon': '🌬️'
            })
    
    return findings


def generate_building_envelope_assessment(building_profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate preliminary building envelope observations.
    
    This is a qualitative screening, NOT a detailed thermal simulation.
    """
    observations = []
    
    if not building_profile:
        observations.append({
            'aspect': 'Data Availability',
            'observation': 'No building profile data available. Enter building details to receive envelope observations.',
            'confidence': 'N/A',
            'recommendation': 'Complete the Building Profile section.'
        })
        return observations
    
    profile = building_profile
    
    # Roof
    roof_type = profile.get('roof_type', '')
    roof_insulation = profile.get('roof_insulation', '')
    if roof_type:
        obs = f"Roof type: {roof_type}."
        if roof_insulation:
            obs += f" Insulation: {roof_insulation}."
            rec = "Verify insulation condition during next maintenance cycle."
        else:
            obs += " Insulation status not specified."
            rec = "Consider a roof insulation assessment. Proper insulation can reduce cooling loads significantly in hot climates."
        observations.append({
            'aspect': 'Roof',
            'observation': obs,
            'confidence': 'Based on user input — not verified by inspection',
            'recommendation': rec
        })
    
    # Walls
    wall_construction = profile.get('wall_construction', '')
    if wall_construction:
        observations.append({
            'aspect': 'External Walls',
            'observation': f"Wall construction reported as: {wall_construction}.",
            'confidence': 'Based on user input — not verified by inspection',
            'recommendation': 'Wall insulation and construction quality affect thermal performance. For detailed U-value assessment, a professional inspection is recommended.'
        })
    else:
        observations.append({
            'aspect': 'External Walls',
            'observation': 'Wall construction details not provided.',
            'confidence': 'N/A',
            'recommendation': 'Provide wall construction details for a more comprehensive assessment.'
        })
    
    # Windows
    window_area = profile.get('window_area')
    built_up_area = profile.get('built_up_area')
    window_orientation = profile.get('window_orientation', '')
    if window_area and built_up_area and built_up_area > 0:
        wwr = window_area / built_up_area * 100
        obs = f"Approximate Window-to-Wall Ratio (WWR): {wwr:.1f}%."
        if window_orientation:
            obs += f" Primary orientation: {window_orientation}."
        if wwr > 40:
            rec = "WWR appears relatively high. Consider external shading devices, curtains, or reflective glazing to reduce solar heat gain."
        elif wwr < 15:
            rec = "WWR is relatively low. This may limit natural daylight and increase artificial lighting needs."
        else:
            rec = "WWR is within a typical range. Ensure windows have appropriate shading for orientation."
        observations.append({
            'aspect': 'Windows',
            'observation': obs,
            'confidence': 'Preliminary estimate based on user-provided areas — actual WWR calculation requires wall area measurement',
            'recommendation': rec
        })
    
    # Ventilation
    ventilation = profile.get('natural_ventilation', '')
    if ventilation:
        observations.append({
            'aspect': 'Ventilation',
            'observation': f"Natural ventilation reported as: {ventilation}.",
            'confidence': 'Based on user assessment — not verified',
            'recommendation': 'Good cross-ventilation can significantly reduce AC dependency. Consider ceiling fans to enhance air movement.' if ventilation in ['Good', 'Adequate'] else 'Improving ventilation through design changes or exhaust fans may reduce cooling loads.'
        })
    
    # Climate zone
    climate_zone = profile.get('climate_zone', '')
    if climate_zone:
        observations.append({
            'aspect': 'Climate Zone',
            'observation': f"Climate zone: {climate_zone}.",
            'confidence': 'User-specified',
            'recommendation': _get_climate_recommendation(climate_zone)
        })
    
    # Overall note
    observations.append({
        'aspect': '⚠️ Assessment Limitation',
        'observation': 'This is a preliminary qualitative screening based on user-provided descriptions. It does NOT constitute a detailed thermal simulation or a professional building energy audit.',
        'confidence': 'N/A',
        'recommendation': 'For accurate U-values, heat transfer coefficients, SHGC values, and code compliance verification, a professional energy auditor with appropriate instrumentation should be consulted.'
    })
    
    return observations


def _get_climate_recommendation(climate_zone: str) -> str:
    """Provide general climate-zone-specific guidance."""
    zone = climate_zone.lower()
    if 'hot' in zone and 'dry' in zone:
        return "Hot-dry climate: Prioritize roof insulation, external shading, light-colored exterior surfaces, and reducing west-facing glazing."
    elif 'warm' in zone and 'humid' in zone:
        return "Warm-humid climate: Prioritize ventilation, dehumidification, shading from rain and sun, and reflective roofing."
    elif 'composite' in zone:
        return "Composite climate: Building needs to address both hot-dry summers and cooler winters. Consider adaptable shading and moderate insulation."
    elif 'temperate' in zone:
        return "Temperate climate: Moderate insulation needs. Maximize natural ventilation and daylight utilization."
    elif 'cold' in zone:
        return "Cold climate: Prioritize insulation, airtightness, passive solar heating, and double-glazed windows."
    else:
        return "Consider climate-appropriate insulation, shading, and ventilation strategies."


def get_default_interventions(appliance_df: pd.DataFrame, 
                               building_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a list of potential energy-saving interventions based on audit data."""
    interventions = []
    
    if appliance_df.empty:
        return interventions
    
    total_monthly = appliance_df['monthly_kwh'].sum()
    
    # 1. LED replacement
    lighting = appliance_df[appliance_df['name'].str.lower().str.contains(
        'light|bulb|lamp|tube|cfl', na=False)]
    non_led = lighting[~lighting['name'].str.lower().str.contains('led', na=False)]
    if not non_led.empty:
        interventions.append({
            'name': 'Replace non-LED lighting with LED alternatives',
            'description': 'LED lights use 50-80% less energy than incandescent or CFL bulbs for equivalent light output.',
            'baseline_monthly_kwh': round(non_led['monthly_kwh'].sum(), 2),
            'default_reduction': 0.60,
            'category': 'Lighting',
            'confidence': 'Estimate based on typical LED vs. incandescent/CFL savings'
        })
    
    # 2. Reduce operating hours
    high_use = appliance_df[(appliance_df['hours_per_day'] >= 8) & 
                           (~appliance_df['name'].str.lower().str.contains('fridge|refrigerator|router|modem', na=False))]
    if not high_use.empty:
        interventions.append({
            'name': 'Reduce unnecessary operating hours',
            'description': 'Review appliances with long operating hours and reduce usage during idle periods.',
            'baseline_monthly_kwh': round(high_use['monthly_kwh'].sum(), 2),
            'default_reduction': 0.15,
            'category': 'Usage Optimization',
            'confidence': 'User-adjustable assumption — actual reduction depends on specific usage patterns'
        })
    
    # 3. AC optimization
    ac_apps = appliance_df[appliance_df['name'].str.lower().str.contains(
        'air.?condition|ac|split|window.?ac', na=False)]
    if not ac_apps.empty:
        interventions.append({
            'name': 'Optimize air conditioning usage',
            'description': 'Set thermostat to 24-26°C, ensure regular servicing, clean filters, and seal gaps around doors/windows. Use fans to supplement.',
            'baseline_monthly_kwh': round(ac_apps['monthly_kwh'].sum(), 2),
            'default_reduction': 0.20,
            'category': 'Cooling',
            'confidence': 'General estimate — actual savings depend on current settings, maintenance state, and building envelope'
        })
    
    # 4. Standby power reduction
    electronics = appliance_df[appliance_df['name'].str.lower().str.contains(
        'tv|television|computer|laptop|monitor|printer|gaming|charger|set.?top', na=False)]
    if len(electronics) >= 2:
        interventions.append({
            'name': 'Reduce standby power consumption',
            'description': 'Use power strips with switches to disconnect electronics when not in use. Standby consumption is typically 1-15W per device.',
            'baseline_monthly_kwh': round(electronics['monthly_kwh'].sum() * 0.1, 2),
            'default_reduction': 0.50,
            'category': 'Standby Power',
            'confidence': 'Rough estimate — standby power varies significantly across devices'
        })
    
    # 5. Efficient appliance upgrade
    high_power = appliance_df[appliance_df['power_watts'] >= 1000]
    if not high_power.empty:
        interventions.append({
            'name': 'Evaluate high-power appliances for efficient alternatives',
            'description': 'Appliances rated 1000W or more may have BEE star-rated efficient alternatives. Higher star ratings indicate lower energy consumption for the same output.',
            'baseline_monthly_kwh': round(high_power['monthly_kwh'].sum(), 2),
            'default_reduction': 0.15,
            'category': 'Appliance Upgrade',
            'confidence': 'General estimate — actual savings depend on specific appliance models and BEE ratings'
        })
    
    # 6. Solar assessment
    if building_profile and not building_profile.get('solar_installation'):
        roof_area = building_profile.get('built_up_area', 0)
        if roof_area > 0 and total_monthly > 100:
            interventions.append({
                'name': 'Evaluate rooftop solar photovoltaic installation',
                'description': 'Rooftop solar panels can offset a significant portion of electricity consumption. Feasibility depends on roof area, orientation, shading, and local policies. This is an area for further professional assessment.',
                'baseline_monthly_kwh': round(total_monthly, 2),
                'default_reduction': 0.30,
                'category': 'Renewable Energy',
                'confidence': 'Very rough estimate — actual solar generation depends on site-specific factors. Professional feasibility study recommended.'
            })
    
    return interventions
