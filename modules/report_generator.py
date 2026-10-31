"""
EcoAudit AI — PDF Report Generator

Generates a downloadable PDF energy audit report from user-entered data
and calculated results. Uses FPDF2 for PDF generation.

The report can be generated even when the AI API is unavailable.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def _pdf_safe_text(value: Any) -> str:
    """Convert common symbols to readable text supported by FPDF core fonts."""
    text = str(value)
    replacements = {
        '₹': 'INR ', '—': '-', '–': '-', '×': 'x', '→': '->', '•': '-',
        '’': "'", '‘': "'", '“': '"', '”': '"', '…': '...',
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text.encode('latin-1', errors='replace').decode('latin-1')


class EcoAuditReport(FPDF if FPDF else object):
    """Custom PDF report for EcoAudit AI energy audit results."""
    
    def __init__(self):
        if FPDF is None:
            raise ImportError("fpdf2 package is required for report generation. Install with: pip install fpdf2")
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def cell(self, w, h=0, text="", *args, **kwargs):
        """Keep report generation resilient when data contains Unicode symbols."""
        return super().cell(w, h, _pdf_safe_text(text), *args, **kwargs)

    def multi_cell(self, w, h, text, *args, **kwargs):
        return super().multi_cell(w, h, _pdf_safe_text(text), *args, **kwargs)
    
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(34, 139, 34)
        self.cell(0, 8, 'EcoAudit AI', new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'AI-Powered Residential Building Energy Audit Report', new_x="LMARGIN", new_y="NEXT", align='L')
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'EcoAudit AI Report | Page {self.page_no()}/{{nb}} | Generated {datetime.now().strftime("%d-%b-%Y %H:%M")}', 
                  new_x="RIGHT", new_y="TOP", align='C')
    
    def section_title(self, title: str, num: str = ""):
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(34, 100, 34)
        prefix = f"{num}. " if num else ""
        self.cell(0, 10, f'{prefix}{title}', new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(34, 139, 34)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)
    
    def sub_title(self, title: str):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
    
    def body_text(self, text: str):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, text)
        self.ln(2)
    
    def key_value(self, key: str, value: str):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(60, 60, 60)
        self.cell(65, 6, key + ":", new_x="RIGHT", new_y="TOP")
        self.set_font('Helvetica', '', 9)
        self.set_text_color(40, 40, 40)
        self.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")
    
    def info_box(self, text: str):
        self.set_fill_color(240, 248, 240)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(3)
    
    def warning_box(self, text: str):
        self.set_fill_color(255, 248, 230)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(120, 80, 0)
        self.multi_cell(0, 5, text, fill=True)
        self.ln(3)
    
    def add_table(self, headers: List[str], rows: List[List[str]], 
                  col_widths: Optional[List[int]] = None):
        """Add a formatted table to the report."""
        if not col_widths:
            available_width = 190
            col_widths = [available_width // len(headers)] * len(headers)
            # Adjust last column to fill remaining space
            col_widths[-1] = available_width - sum(col_widths[:-1])
        
        # Header row
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(34, 139, 34)
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, border=1, fill=True,
                      new_x="RIGHT", new_y="TOP", align='C')
        self.ln()
        
        # Data rows
        self.set_font('Helvetica', '', 8)
        self.set_text_color(40, 40, 40)
        fill = False
        for row in rows:
            if self.get_y() > 260:
                self.add_page()
            if fill:
                self.set_fill_color(245, 250, 245)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell_text in enumerate(row):
                self.cell(col_widths[i], 6, str(cell_text)[:50], border=1, fill=True,
                          new_x="RIGHT", new_y="TOP", align='C')
            self.ln()
            fill = not fill
        self.ln(4)


def generate_report(building_profile: Dict[str, Any],
                    appliance_df: Any,
                    consumption_summary: Dict[str, float],
                    bill_analysis: Optional[Dict[str, Any]] = None,
                    bill_comparison: Optional[Dict[str, Any]] = None,
                    audit_findings: Optional[Dict[str, List]] = None,
                    envelope_assessment: Optional[List[Dict]] = None,
                    interventions: Optional[List[Dict]] = None,
                    is_sample_data: bool = False) -> bytes:
    """Generate a complete PDF energy audit report.
    
    Args:
        building_profile: Building profile data
        appliance_df: DataFrame with processed appliance data
        consumption_summary: Aggregate consumption summary
        bill_analysis: Monthly bill analysis results
        bill_comparison: Bill vs calculated comparison
        audit_findings: Categorized audit findings
        envelope_assessment: Building envelope observations
        interventions: Energy-saving interventions with savings
        is_sample_data: Whether this uses sample data
    
    Returns:
        PDF file content as bytes
    """
    if FPDF is None:
        raise ImportError("fpdf2 package is required. Install with: pip install fpdf2")
    
    pdf = EcoAuditReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # ── Title Page ──
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(34, 139, 34)
    pdf.ln(20)
    pdf.cell(0, 15, 'EcoAudit AI', new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, 'Residential Building Energy Audit Report', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    if is_sample_data:
        pdf.warning_box("ILLUSTRATIVE SAMPLE DATA -- This report uses sample data for demonstration. "
                       "It does not represent a measured real building.")
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    building_name = building_profile.get('name', 'Not specified')
    pdf.cell(0, 8, f'Building: {building_name}', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, f'Report Date: {datetime.now().strftime("%d %B %Y")}', new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 8, f'Location: {building_profile.get("city", "")}, {building_profile.get("state", "")}',
             new_x="LMARGIN", new_y="NEXT", align='C')
    
    # ── 1. Scope and Methodology ──
    pdf.add_page()
    pdf.section_title("Scope and Methodology", "1")
    pdf.body_text(
        "This report presents a preliminary energy audit analysis of a residential building. "
        "The analysis is based on user-provided building information, appliance inventory data, "
        "and electricity consumption records where available.\n\n"
        "Methodology:\n"
        "- Appliance energy consumption is estimated using: "
        "Quantity x Rated Power (W) x Hours/Day x Days/Month / 1000 = kWh/month\n"
        "- Annual consumption assumes the monthly usage pattern remains constant (x12).\n"
        "- Electricity costs are estimated using the user-provided tariff rate.\n"
        "- Audit findings are categorized by data confidence level.\n"
        "- Building envelope assessment is qualitative and based on user descriptions.\n\n"
        "This is NOT a certified professional energy audit. It provides preliminary educational analysis "
        "to identify potential energy-saving opportunities."
    )
    
    pdf.sub_title("Data Sources and Assumptions")
    pdf.body_text(
        "- Building profile: User-provided descriptive information.\n"
        "- Appliance ratings: Rated (nameplate) power values, which may differ from actual average power draw "
        "due to duty cycles, thermostat behaviour, and operating conditions.\n"
        "- Usage hours: User-estimated averages, not continuous measurements.\n"
        "- Electricity tariff: Flat rate as specified by the user. Actual bills may use slab-based tariffs.\n"
        "- All sample values are illustrative and are not official reference values." if is_sample_data else
        "- Building profile: User-provided information.\n"
        "- Appliance ratings: As entered by the user.\n"
        "- Usage hours: User-estimated averages.\n"
        "- Electricity tariff: As specified by the user."
    )
    
    # ── 2. Building Profile ──
    pdf.add_page()
    pdf.section_title("Building Profile", "2")
    
    profile_fields = [
        ("Building Name", building_profile.get('name', 'Not specified')),
        ("Building Type", building_profile.get('building_type', 'Not specified')),
        ("City", building_profile.get('city', 'Not specified')),
        ("State", building_profile.get('state', 'Not specified')),
        ("Climate Zone", building_profile.get('climate_zone', 'Not specified')),
        ("Number of Floors", str(building_profile.get('num_floors', 'Not specified'))),
        ("Number of Units", str(building_profile.get('num_units', 'Not specified'))),
        ("Built-up Area", f"{building_profile.get('built_up_area', 'N/A')} sq.m"),
        ("Number of Occupants", str(building_profile.get('num_occupants', 'Not specified'))),
        ("Building Age", f"{building_profile.get('building_age', 'N/A')} years"),
        ("Window Area", f"{building_profile.get('window_area', 'N/A')} sq.m"),
        ("Window Orientation", building_profile.get('window_orientation', 'Not specified')),
        ("Roof Type", building_profile.get('roof_type', 'Not specified')),
        ("Roof Insulation", building_profile.get('roof_insulation', 'Not specified')),
        ("Wall Construction", building_profile.get('wall_construction', 'Not specified')),
        ("Natural Ventilation", building_profile.get('natural_ventilation', 'Not specified')),
        ("Lighting Type", building_profile.get('lighting_type', 'Not specified')),
        ("AC Available", "Yes" if building_profile.get('ac_availability') else "No"),
        ("Solar Installation", "Yes" if building_profile.get('solar_installation') else "No"),
        ("Electricity Tariff", f"Rs. {building_profile.get('tariff', 'N/A')}/kWh"),
    ]
    
    for key, value in profile_fields:
        pdf.key_value(key, str(value))
    
    # ── 3. Appliance Inventory ──
    pdf.add_page()
    pdf.section_title("Appliance Inventory", "3")
    
    if appliance_df is not None and not appliance_df.empty:
        headers = ["Appliance", "Qty", "Power(W)", "Hrs/Day", "Days/Mo", "Monthly kWh", "%"]
        col_widths = [50, 15, 22, 20, 20, 28, 18]
        
        rows = []
        for _, row in appliance_df.iterrows():
            rows.append([
                str(row['name'])[:30],
                str(row['quantity']),
                str(row['power_watts']),
                str(row['hours_per_day']),
                str(row['days_per_month']),
                f"{row['monthly_kwh']:.1f}",
                f"{row['percentage_contribution']:.1f}%"
            ])
        
        pdf.add_table(headers, rows, col_widths)
        
        pdf.info_box("Note: Rated power is used as a proxy for actual power draw. Appliances with duty cycles "
                    "(e.g., refrigerators, ACs, water heaters) may have actual average draw significantly below "
                    "the rated power. Estimated consumption may differ from measured consumption.")
    else:
        pdf.body_text("No appliance data entered.")
    
    # ── 4. Energy Consumption Summary ──
    pdf.add_page()
    pdf.section_title("Energy Consumption Summary", "4")
    
    if consumption_summary:
        summary_fields = [
            ("Total Est. Daily Consumption", f"{consumption_summary.get('total_daily_kwh', 0):.2f} kWh"),
            ("Total Est. Monthly Consumption", f"{consumption_summary.get('total_monthly_kwh', 0):.2f} kWh"),
            ("Total Est. Annual Consumption", f"{consumption_summary.get('total_annual_kwh', 0):.2f} kWh"),
            ("Electricity Tariff", f"Rs. {consumption_summary.get('tariff_used', 0)}/kWh"),
            ("Est. Monthly Electricity Cost", f"Rs. {consumption_summary.get('monthly_cost_inr', 0):,.2f}"),
            ("Est. Annual Electricity Cost", f"Rs. {consumption_summary.get('annual_cost_inr', 0):,.2f}"),
        ]
        for key, value in summary_fields:
            pdf.key_value(key, value)
        
        pdf.ln(4)
        pdf.info_box("These estimates are based on appliance rated power and user-estimated usage patterns. "
                    "Actual consumption may vary. Annual estimates assume constant monthly usage.")
    
    # ── 5. Bill Comparison ──
    if bill_comparison and bill_comparison.get('billed_monthly_kwh', 0) > 0:
        pdf.section_title("Bill vs. Calculated Comparison", "5")
        pdf.key_value("Calculated Monthly Consumption", 
                      f"{bill_comparison['calculated_monthly_kwh']:.1f} kWh")
        pdf.key_value("Billed Monthly Consumption", 
                      f"{bill_comparison['billed_monthly_kwh']:.1f} kWh")
        pdf.key_value("Absolute Difference", 
                      f"{bill_comparison['absolute_difference_kwh']:.1f} kWh")
        pdf.key_value("Percentage Difference", 
                      f"{bill_comparison['percentage_difference']:.1f}%")
        
        if bill_comparison.get('possible_reasons'):
            pdf.ln(3)
            pdf.sub_title("Possible Reasons for Discrepancy")
            for reason in bill_comparison['possible_reasons']:
                pdf.body_text(f"  - {reason}")
    
    # ── 6. Monthly Bill Trends ──
    if bill_analysis and bill_analysis.get('data'):
        pdf.add_page()
        sec_num = "6" if bill_comparison else "5"
        pdf.section_title("Monthly Bill Analysis", sec_num)
        
        pdf.key_value("Months Available", str(bill_analysis.get('months_available', 0)))
        pdf.key_value("Average Monthly Consumption", f"{bill_analysis.get('average_monthly_kwh', 0):.1f} kWh")
        pdf.key_value("Highest Consumption Month", 
                      f"{bill_analysis.get('highest_month', 'N/A')} ({bill_analysis.get('highest_consumption_kwh', 0):.0f} kWh)")
        pdf.key_value("Lowest Consumption Month", 
                      f"{bill_analysis.get('lowest_month', 'N/A')} ({bill_analysis.get('lowest_consumption_kwh', 0):.0f} kWh)")
        pdf.key_value("Total for Period", f"{bill_analysis.get('total_for_period_kwh', 0):,.0f} kWh")
        pdf.key_value("Est. Period Cost", f"Rs. {bill_analysis.get('estimated_period_cost_inr', 0):,.0f}")
        
        if not bill_analysis.get('is_complete_year', True):
            pdf.ln(3)
            pdf.warning_box(bill_analysis.get('data_note', 'Partial year data.'))
    
    # ── 7. Audit Findings ──
    pdf.add_page()
    pdf.section_title("Energy Audit Findings", "7")
    
    if audit_findings:
        for category, label in [('data_supported', 'Findings Supported by User Data'),
                                 ('assumption_based', 'Findings Based on Assumptions'),
                                 ('requires_inspection', 'Findings Requiring Additional Inspection')]:
            items = audit_findings.get(category, [])
            if items:
                pdf.sub_title(label)
                for item in items:
                    finding_text = f"[{item.get('category', '')}] {item.get('finding', '')}"
                    pdf.body_text(finding_text)
    else:
        pdf.body_text("No audit findings generated. Enter building and appliance data to receive findings.")
    
    # ── 8. Building Envelope Assessment ──
    if envelope_assessment:
        pdf.add_page()
        pdf.section_title("Building Envelope Assessment (Preliminary)", "8")
        pdf.warning_box("This is a preliminary qualitative screening based on user-provided descriptions. "
                       "It does NOT constitute a detailed thermal simulation or professional building energy audit.")
        
        for obs in envelope_assessment:
            pdf.sub_title(obs.get('aspect', ''))
            pdf.body_text(f"Observation: {obs.get('observation', '')}")
            pdf.body_text(f"Confidence: {obs.get('confidence', '')}")
            pdf.body_text(f"Recommendation: {obs.get('recommendation', '')}")
    
    # ── 9. Energy-Saving Recommendations ──
    if interventions:
        pdf.add_page()
        pdf.section_title("Energy-Saving Recommendations", "9")
        pdf.info_box("The following are potential energy-saving interventions. Reduction percentages "
                    "are assumed estimates unless supported by project-specific evidence. "
                    "Actual savings may vary significantly.")
        
        for i, intervention in enumerate(interventions, 1):
            pdf.sub_title(f"{i}. {intervention.get('name', '')}")
            pdf.body_text(intervention.get('description', ''))
            pdf.key_value("Category", intervention.get('category', ''))
            pdf.key_value("Baseline Consumption", f"{intervention.get('baseline_monthly_kwh', 0):.1f} kWh/month")
            pdf.key_value("Assumed Reduction", f"{intervention.get('default_reduction', 0) * 100:.0f}%")
            
            if 'savings' in intervention:
                s = intervention['savings']
                pdf.key_value("Est. Monthly Savings", f"{s.get('monthly_kwh_saved', 0):.1f} kWh")
                pdf.key_value("Est. Monthly Cost Saving", f"Rs. {s.get('monthly_cost_saved_inr', 0):.0f}")
                pdf.key_value("Est. Annual Cost Saving", f"Rs. {s.get('annual_cost_saved_inr', 0):,.0f}")
            
            pdf.body_text(f"Confidence: {intervention.get('confidence', 'Estimate')}")
            pdf.ln(2)
    
    # ── 10. Codes and Standards References ──
    pdf.add_page()
    pdf.section_title("Relevant Indian Codes and Standards", "10")
    pdf.body_text(
        "The following codes and standards are relevant to residential building energy efficiency in India. "
        "These references are for educational awareness. Consult official sources for specific provisions."
    )
    
    code_references = [
        ("Eco Niwas Samhita (ENS) 2018 - Part I", "BEE", "Residential building envelope energy conservation"),
        ("Eco Niwas Samhita 2021 - Part II", "BEE", "Electro-mechanical and renewable energy systems"),
        ("ECSBC 2023", "BEE", "Energy conservation and sustainable building code"),
        ("National Building Code (NBC 2016)", "BIS", "Comprehensive building standards"),
        ("BEE Standards & Labelling Programme", "BEE", "Appliance energy efficiency ratings"),
    ]
    
    headers = ["Code/Standard", "Authority", "Subject"]
    rows = [[c[0], c[1], c[2]] for c in code_references]
    pdf.add_table(headers, rows, [65, 30, 95])
    
    pdf.body_text("Official sources: beeindia.gov.in | beestarlabel.com | bis.gov.in")
    
    # ── 11. Limitations ──
    pdf.add_page()
    pdf.section_title("Limitations and Uncertainty", "11")
    pdf.body_text(
        "This preliminary energy audit has the following limitations:\n\n"
        "1. Consumption estimates are based on rated (nameplate) power, not measured power draw. "
        "Actual consumption may differ significantly for thermostat-controlled appliances.\n\n"
        "2. Usage hours are user-estimated averages, not based on continuous monitoring.\n\n"
        "3. Annual projections assume constant monthly usage, which may not reflect seasonal variations.\n\n"
        "4. The electricity tariff used is a flat rate. Actual tariffs may include slab structures, "
        "time-of-day rates, taxes, and fixed charges.\n\n"
        "5. Building envelope assessment is qualitative and based on user descriptions, "
        "not on measured U-values or thermal imaging.\n\n"
        "6. Energy-saving estimates use assumed reduction percentages and are not guaranteed outcomes.\n\n"
        "7. This tool does not verify code compliance. Code applicability depends on state-level adoption.\n\n"
        "8. AI-generated responses (where available) are for informational purposes and should be verified.\n\n"
        "For a comprehensive professional energy audit, consult a BEE-certified energy auditor."
    )
    
    # ── 12. Conclusion ──
    pdf.section_title("Conclusion and Recommended Next Steps", "12")
    
    if consumption_summary:
        total_monthly = consumption_summary.get('total_monthly_kwh', 0)
        monthly_cost = consumption_summary.get('monthly_cost_inr', 0)
        pdf.body_text(
            f"Based on the data provided, the estimated monthly electricity consumption of this "
            f"residential building is approximately {total_monthly:.0f} kWh, with an estimated "
            f"monthly cost of Rs. {monthly_cost:,.0f} at the specified tariff."
        )
    
    pdf.body_text(
        "Recommended next steps:\n\n"
        "1. Review and prioritize the identified energy-saving opportunities.\n"
        "2. Start with no-cost behavioural changes and low-cost upgrades.\n"
        "3. Consider professional energy metering for accurate consumption data.\n"
        "4. Evaluate BEE star-rated replacements for high-consumption appliances.\n"
        "5. Assess solar and insulation opportunities with qualified professionals.\n"
        "6. For formal compliance assessment, consult a BEE-certified energy auditor."
    )
    
    pdf.ln(5)
    pdf.info_box("This report was generated by EcoAudit AI, an educational energy audit tool. "
                "It provides preliminary analysis and does not constitute a certified professional "
                "energy audit or formal code compliance assessment.")
    
    return pdf.output()
