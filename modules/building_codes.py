"""
EcoAudit AI — Indian Energy Conservation Codes and Standards Reference

Provides verified references to Indian energy conservation codes, standards,
and official resources relevant to residential building energy audits.

DISCLAIMER: This module provides educational references only.
It does NOT constitute legal advice, formal code certification,
or a substitute for a qualified professional's inspection.
"""
from typing import Dict, List, Any


def get_all_codes_and_standards() -> List[Dict[str, Any]]:
    """Return a comprehensive list of Indian energy conservation codes and standards."""
    return [
        {
            'name': 'Eco Niwas Samhita (ENS) 2018 — Part I: Building Envelope',
            'edition': '2018',
            'issuing_authority': 'Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India',
            'subject': 'Energy Conservation Building Code for Residential Buildings — Part I covers the building envelope including walls, roofs, windows, and doors.',
            'relevance': 'Directly applicable to residential building envelope design. Establishes minimum performance standards for thermal performance of residential building envelope components to limit heat gains (in cooling-dominated climates) and heat losses (in heating-dominated climates).',
            'applicability_limitations': 'Applies to residential buildings or residential parts of mixed-use buildings. Adoption and enforcement depend on individual state governments incorporating it into their local building bylaws. Not all states have mandated it. Voluntary compliance is encouraged where not yet mandatory.',
            'official_source': 'https://beeindia.gov.in/en/programmes/eco-niwas-samhita',
            'key_provisions': [
                'Residential Envelope Transmittance Value (RETV) for building envelope in composite, hot-dry, warm-humid, and temperate climate zones.',
                'Overall thermal transmittance (U-value) requirements for roofs, walls, and fenestration.',
                'Climate-zone-specific compliance requirements.',
                'Five climate zones of India: Composite, Hot-Dry, Warm-Humid, Temperate, and Cold.'
            ],
            'verification_note': 'ENS 2018 Part I is a published document by BEE. Verify specific clause numbers and threshold values from the official BEE publication before citing in professional work.'
        },
        {
            'name': 'Eco Niwas Samhita 2021 — Part II: Electro-Mechanical and Renewable Energy Systems',
            'edition': '2021',
            'issuing_authority': 'Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India',
            'subject': 'Part II covers energy efficiency requirements for electro-mechanical systems and renewable energy use in residential buildings, including lighting, air conditioning, and solar energy systems.',
            'relevance': 'Complements Part I by addressing active building systems. Covers lighting power density, air-conditioning efficiency, solar water heating, and other energy-using systems in residences.',
            'applicability_limitations': 'Same as Part I — adoption depends on state governments. The specific mandatory or voluntary status varies by state. Updated provisions may have been released; check BEE website for the latest version.',
            'official_source': 'https://beeindia.gov.in/en/programmes/eco-niwas-samhita',
            'key_provisions': [
                'Minimum energy performance standards for residential lighting systems.',
                'Efficiency requirements for air conditioning and space cooling.',
                'Solar water heating system integration requirements.',
                'Provisions for energy-efficient electrical installations.'
            ],
            'verification_note': 'ENS 2021 Part II was published by BEE. Verify the latest edition, as updates may have been released. Check BEE official website for current documents.'
        },
        {
            'name': 'Energy Conservation and Sustainable Building Code (ECSBC) 2023',
            'edition': '2023',
            'issuing_authority': 'Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India',
            'subject': 'Integrated energy conservation and sustainability code. ECSBC 2023 supersedes the earlier ECBC (2017) for commercial buildings and includes provisions that may apply to larger residential buildings and mixed-use developments.',
            'relevance': 'While primarily aimed at commercial and large buildings, ECSBC 2023 may have residential provisions, especially for multi-story residential complexes and mixed-use buildings. It provides a framework for energy-efficient building design including renewable energy integration.',
            'applicability_limitations': 'Primarily applicable to commercial buildings with connected load ≥100 kW or contract demand ≥120 kVA (as per earlier ECBC criteria — verify updated criteria in ECSBC 2023). Small individual residences may not fall directly under its mandatory scope. State adoption required for enforcement.',
            'official_source': 'https://beeindia.gov.in/en/programmes/energy-conservation-building-codes',
            'key_provisions': [
                'Updated building envelope requirements.',
                'HVAC system efficiency standards.',
                'Lighting power density limits.',
                'Renewable energy integration requirements.',
                'Net-zero energy building framework.',
                'Sustainability provisions beyond energy including water and materials.'
            ],
            'verification_note': 'ECSBC 2023 is the successor to ECBC 2017. Verify the specific residential applicability from the official document, as the residential scope may differ from the earlier code. Check BEE for the latest published version and any subsequent amendments.'
        },
        {
            'name': 'Energy Conservation Building Code (ECBC) 2017',
            'edition': '2017',
            'issuing_authority': 'Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India',
            'subject': 'Energy conservation code primarily for commercial buildings. Covers building envelope, HVAC, lighting, electrical systems, and renewable energy.',
            'relevance': 'ECBC 2017 is primarily for commercial buildings (connected load ≥100 kW or contract demand ≥120 kVA). It is NOT directly applicable to typical individual residences. However, it provides useful benchmarks and methodology context. The residential equivalent is Eco Niwas Samhita.',
            'applicability_limitations': 'NOT directly applicable to individual residential buildings. Applicable to commercial buildings meeting the connected load/demand threshold. Now largely superseded by ECSBC 2023 for new construction. Included here for reference and comparison only.',
            'official_source': 'https://beeindia.gov.in/en/programmes/energy-conservation-building-codes',
            'key_provisions': [
                'Three tiers of compliance: ECBC (minimum), ECBC+ (enhanced), SuperECBC (superior).',
                'Building envelope thermal performance requirements.',
                'HVAC system efficiency requirements.',
                'Interior and exterior lighting power density limits.',
                'Electrical power system requirements.',
                'Renewable energy requirements scaling with tiers.'
            ],
            'verification_note': 'ECBC 2017 has been largely superseded by ECSBC 2023. Included for historical reference and commercial building comparison. Do not apply ECBC commercial thresholds to private residences.'
        },
        {
            'name': 'National Building Code of India (NBC) 2016',
            'edition': '2016 (SP 7:2016)',
            'issuing_authority': 'Bureau of Indian Standards (BIS)',
            'subject': 'Comprehensive building code covering planning, design, construction, and maintenance of buildings across India. Part 11 covers Approach to Sustainability.',
            'relevance': 'NBC includes general provisions applicable to all buildings including residences. Part 11 on sustainability includes energy efficiency guidelines for building design and services. Relevant provisions include natural ventilation, daylighting, and energy-efficient building services.',
            'applicability_limitations': 'NBC is a national reference standard. Mandatory enforcement depends on local building authority adoption. Not all provisions may be applicable to every residential building type. Specific energy-performance requirements for residences are more directly covered by Eco Niwas Samhita.',
            'official_source': 'https://www.bis.gov.in/',
            'key_provisions': [
                'Part 8: Building Services (electrical installations, plumbing, air conditioning).',
                'Part 11: Approach to Sustainability (energy, water, materials, waste, indoor environment).',
                'General structural and fire safety provisions.',
                'Planning and design standards for residential buildings.'
            ],
            'verification_note': 'NBC 2016 (SP 7:2016) is the current published edition by BIS. Verify specific part and clause references from the official BIS publication. A revised edition may be released; check BIS for updates.'
        },
        {
            'name': 'BEE Standards & Labelling Programme',
            'edition': 'Ongoing programme (started 2006)',
            'issuing_authority': 'Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India',
            'subject': 'Star rating and labelling programme for energy-consuming appliances and equipment to enable consumers to make informed purchasing decisions.',
            'relevance': 'Directly relevant to residential energy audits. BEE star labels on appliances (ACs, refrigerators, fans, TVs, washing machines, LED lamps, etc.) provide verified energy-efficiency information. Higher star ratings indicate lower energy consumption for the same output. Useful for appliance replacement recommendations.',
            'applicability_limitations': 'Star labels are mandatory for some appliance categories and voluntary for others. The list of covered appliances is updated periodically. Star ratings are revised over time, so a 5-star appliance from an earlier schedule may not meet the current 5-star criteria. Always check the rating year.',
            'official_source': 'https://beestarlabel.com/',
            'key_provisions': [
                'Mandatory labelling for appliances including room ACs, refrigerators (frost-free and direct cool), tubular fluorescent lamps, distribution transformers, and ceiling fans.',
                'Voluntary labelling for appliances including LED lamps, televisions, washing machines, computers, and more.',
                '1-star (least efficient) to 5-star (most efficient) rating scale.',
                'Annual energy consumption values printed on labels for direct comparison.',
                'Periodic revision of star-rating criteria to raise efficiency benchmarks.'
            ],
            'verification_note': 'The S&L programme is actively maintained by BEE. The list of mandatory and voluntary appliances and current star-rating schedules should be verified from the official BEE Star Label website (beestarlabel.com).'
        },
        {
            'name': 'Indian Electricity Rules and Safety Standards',
            'edition': 'Various — governed by Indian Electricity Act 2003 and Central Electricity Authority (CEA) regulations',
            'issuing_authority': 'Central Electricity Authority (CEA), Ministry of Power / Bureau of Indian Standards (BIS)',
            'subject': 'Electrical safety standards covering wiring, installation, earthing, and safety requirements for electrical installations in buildings.',
            'relevance': 'Relevant to residential energy audits only in the context of electrical safety of wiring, metering, and installed equipment. Improper or aged wiring can cause energy losses and safety hazards. Included for awareness only — detailed electrical safety assessment requires a licensed electrical professional.',
            'applicability_limitations': 'Electrical safety inspection is outside the scope of a preliminary energy audit. This reference is included only to note that energy-saving recommendations should not compromise electrical safety. All electrical modifications should comply with applicable safety standards and be carried out by qualified electricians.',
            'official_source': 'https://cea.nic.in/',
            'key_provisions': [
                'CEA (Measures relating to Safety and Electricity Supply) Regulations.',
                'IS 732: Code of Practice for Electrical Wiring Installations.',
                'IS 3043: Code of Practice for Earthing.',
                'Metering standards and energy accounting provisions.'
            ],
            'verification_note': 'Specific IS standards and CEA regulations should be verified from BIS (bis.gov.in) and CEA (cea.nic.in) respectively. Do not recommend electrical modifications without reference to applicable safety standards.'
        }
    ]


def get_code_disclaimer() -> str:
    """Return the standard disclaimer for code references."""
    return """⚠️ **Disclaimer**

This application provides preliminary educational references to Indian energy conservation codes 
and standards for informational purposes only.

It does **NOT** constitute:
- A formal code compliance assessment or certification.
- Legal advice regarding building regulations.
- A substitute for a qualified professional energy auditor's inspection.
- An authoritative interpretation of any code or standard.

All code references should be verified from official sources before use in professional work. 
Code applicability, mandatory status, and specific threshold values depend on state-level adoption, 
building category, and the applicable edition of the code.

For formal compliance assessment, consult a BEE-certified energy auditor or relevant local authority."""


def get_climate_zones() -> List[Dict[str, str]]:
    """Return Indian climate zones as defined by BEE/ENS."""
    return [
        {
            'zone': 'Composite',
            'description': 'Neither predominantly hot-dry, warm-humid, temperate, nor cold. Experiences significant seasonal variation.',
            'example_cities': 'New Delhi, Lucknow, Allahabad, Patna',
            'key_considerations': 'Needs balanced approach for summer cooling and winter comfort.'
        },
        {
            'zone': 'Hot-Dry',
            'description': 'High temperatures with low humidity for most of the year.',
            'example_cities': 'Jaipur, Jodhpur, Ahmedabad',
            'key_considerations': 'Prioritize insulation, shading, reflective surfaces, and thermal mass.'
        },
        {
            'zone': 'Warm-Humid',
            'description': 'Warm temperatures with consistently high humidity.',
            'example_cities': 'Chennai, Mumbai, Kolkata, Thiruvananthapuram',
            'key_considerations': 'Prioritize ventilation, dehumidification, and shading.'
        },
        {
            'zone': 'Temperate',
            'description': 'Moderate temperatures throughout the year.',
            'example_cities': 'Bengaluru, Pune, parts of Western Ghats',
            'key_considerations': 'Maximize natural ventilation and daylight. Minimal cooling/heating needs.'
        },
        {
            'zone': 'Cold',
            'description': 'Low temperatures for a significant part of the year.',
            'example_cities': 'Shimla, Srinagar, Leh, Darjeeling',
            'key_considerations': 'Prioritize insulation, airtightness, passive solar heating, double glazing.'
        }
    ]


def get_bee_star_label_info() -> Dict[str, Any]:
    """Return information about BEE Star Labelling for common residential appliances."""
    return {
        'programme_name': 'BEE Standards & Labelling Programme',
        'description': 'BEE star labels help consumers compare energy efficiency of appliances. Higher stars = lower energy consumption for equivalent output.',
        'rating_scale': '1 star (least efficient) to 5 stars (most efficient)',
        'official_website': 'https://beestarlabel.com/',
        'common_residential_appliances': [
            {
                'appliance': 'Room Air Conditioners (Split & Window)',
                'labelling_status': 'Mandatory',
                'tip': 'Choose 5-star or highest available rating. Inverter ACs generally offer better part-load efficiency.',
                'typical_savings': 'A 5-star AC may consume 20-30% less energy than a 2-3 star AC of similar capacity.'
            },
            {
                'appliance': 'Refrigerators (Frost-Free & Direct Cool)',
                'labelling_status': 'Mandatory',
                'tip': 'Choose the right size for household needs. Over-sized refrigerators consume more energy.',
                'typical_savings': 'A 5-star refrigerator may save 30-45% energy compared to a 1-2 star model.'
            },
            {
                'appliance': 'Ceiling Fans',
                'labelling_status': 'Mandatory',
                'tip': 'BEE 5-star rated fans and BLDC motor fans offer significantly lower consumption (28-35W) vs conventional fans (70-80W).',
                'typical_savings': 'A BLDC/5-star fan can save 50-60% energy vs conventional fans.'
            },
            {
                'appliance': 'LED Lamps',
                'labelling_status': 'Voluntary (check BEE for updates)',
                'tip': 'Look for BEE star-rated LED lamps for verified efficiency and longevity.',
                'typical_savings': 'LEDs use 75-80% less energy than incandescent bulbs.'
            },
            {
                'appliance': 'Televisions',
                'labelling_status': 'Voluntary',
                'tip': 'Larger screens consume more energy. Choose an appropriate screen size.',
                'typical_savings': 'Varies by size and technology (LCD, LED, OLED).'
            },
            {
                'appliance': 'Washing Machines',
                'labelling_status': 'Voluntary',
                'tip': 'Front-load machines are generally more water and energy efficient than top-load.',
                'typical_savings': 'Front-load may save 30-50% energy vs top-load.'
            },
            {
                'appliance': 'Electric Water Heaters (Geysers)',
                'labelling_status': 'Mandatory',
                'tip': 'Choose the right capacity. Larger tanks lose more heat. Consider solar water heaters.',
                'typical_savings': 'A 5-star geyser has better insulation reducing standby heat loss.'
            }
        ],
        'note': 'BEE star ratings are periodically revised. A 5-star rating from an older schedule may not meet current 5-star criteria. Always check the star label validity period and the schedule year.'
    }
