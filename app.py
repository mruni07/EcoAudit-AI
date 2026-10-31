"""
EcoAudit AI — AI-Powered Residential Building Energy Audit System

Main Streamlit application entry point.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import application modules
from modules.energy_calculations import (
    process_appliance_inventory,
    get_consumption_summary,
    get_top_consumers,
    compare_bill_vs_calculated,
    analyze_monthly_bills,
    calculate_savings_for_intervention,
)
from modules.audit_engine import (
    generate_audit_findings,
    generate_building_envelope_assessment,
    get_default_interventions,
)
from modules.building_codes import (
    get_all_codes_and_standards,
    get_code_disclaimer,
    get_climate_zones,
    get_bee_star_label_info,
)
from modules.ai_assistant import (
    check_ai_availability,
    get_ai_response,
    get_suggested_questions,
    get_ai_provider,
)
from modules.report_generator import generate_report
from modules.data_validation import validate_appliance, validate_building_profile

# ─── Page Configuration ───
st.set_page_config(
    page_title="EcoAudit AI — Residential Energy Audit",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Theme and application styles ───
THEMES = {
    "Light": {"page": "#f7f9fc", "sidebar": "#edf3f7", "card": "#ffffff", "text": "#17212b", "muted": "#4b5966", "border": "#c8d2dc", "input": "#ffffff", "accent": "#176b45", "accent_text": "#ffffff", "soft": "#e8f4ed", "warning": "#fff4d6", "plot": "plotly_white"},
    "Dark": {"page": "#101820", "sidebar": "#17232d", "card": "#1d2b36", "text": "#f2f6f8", "muted": "#c0cbd3", "border": "#455663", "input": "#243541", "accent": "#58c58b", "accent_text": "#102018", "soft": "#20382d", "warning": "#42381f", "plot": "plotly_dark"},
}

# Theme is initialized before widgets render and remains stable across reruns.
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Light"
THEME = THEMES[st.session_state.app_theme]
px.defaults.template = THEME["plot"]

st.markdown(f"""
<style>
    :root {{ color-scheme: {'dark' if st.session_state.app_theme == 'Dark' else 'light'}; }}
    .stApp, [data-testid="stAppViewContainer"] {{ background: {THEME['page']}; color: {THEME['text']}; }}
    [data-testid="stSidebar"] {{ background: {THEME['sidebar']}; }}
    [data-testid="stSidebar"] * {{ color: {THEME['text']}; }}
    .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6, .stApp [data-testid="stCaptionContainer"] {{ color: {THEME['text']}; }}
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stHelp"] {{ color: {THEME['muted']}; }}
    [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] {{ color: {THEME['text']}; }}
    input, textarea, [data-baseweb="select"] > div, [data-testid="stNumberInput"] input {{
        background-color: {THEME['input']} !important; color: {THEME['text']} !important;
        border-color: {THEME['border']} !important;
    }}
    [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"] {{
        background-color: {THEME['card']} !important; color: {THEME['text']} !important;
    }}
    [data-testid="stExpander"], [data-testid="stDataFrame"], [data-testid="stTable"],
    [data-testid="stChatMessage"], [data-testid="stChatInput"] {{
        background-color: {THEME['card']}; color: {THEME['text']}; border-color: {THEME['border']};
    }}
    [data-testid="stChatInput"] textarea {{ color: {THEME['text']} !important; }}
    .stButton button, [data-testid="stDownloadButton"] button {{
        color: {THEME['text']}; border-color: {THEME['border']};
    }}
    .stButton button[kind="primary"] {{ background: {THEME['accent']}; color: {THEME['accent_text']}; }}
    .main-header {{ background: linear-gradient(135deg, #145337 0%, #1b8052 55%, #176b45 100%);
        padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem; color: #ffffff; text-align: center; }}
    .main-header h1, .main-header p {{ color: #ffffff !important; }}
    .main-header h1 {{ margin: 0; font-size: 2rem; font-weight: 700; }}
    .main-header p {{ margin: .3rem 0 0; font-size: .95rem; opacity: .94; }}
    .metric-card {{ background: {THEME['card']}; color: {THEME['text']}; border: 1px solid {THEME['border']};
        border-radius: 10px; padding: 1.2rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.12); margin-bottom: .5rem; }}
    .metric-card .metric-value {{ font-size: 1.8rem; font-weight: 700; color: {THEME['accent']}; margin: .3rem 0; }}
    .metric-card .metric-label {{ font-size: .85rem; color: {THEME['text']}; margin-bottom: .2rem; }}
    .metric-card .metric-unit {{ font-size: .75rem; color: {THEME['muted']}; }}
    .section-header {{ border-left: 4px solid {THEME['accent']}; padding-left: 12px; margin: 1.5rem 0 1rem; }}
    .finding-card, .chat-assistant, .info-box {{ background: {THEME['soft']}; color: {THEME['text']};
        border: 1px solid {THEME['border']}; border-left: 4px solid {THEME['accent']};
        border-radius: 8px; padding: 1rem; margin: .5rem 0 .8rem; }}
    .finding-card.warning, .sample-banner {{ background: {THEME['warning']}; color: {THEME['text']};
        border: 1px solid {THEME['border']}; border-left: 4px solid #bd7b00; border-radius: 8px; padding: 1rem; margin-bottom: .8rem; }}
    [data-testid="stAlert"] {{ color: {THEME['text']}; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# ─── Session State Initialization ───
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'building_profile': {},
        'appliances': [],
        'monthly_bills': {},
        'is_sample_data': False,
        'chat_history': [],
        'chat_sessions': {},
        'active_chat_id': None,
        'current_page': 'Home / Dashboard'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


def sync_theme_choice():
    """Persist the sidebar theme choice before the next app render."""
    st.session_state.app_theme = st.session_state.theme_choice

if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = st.session_state.app_theme


# ─── Sidebar Navigation ───
st.sidebar.markdown("### 🏠 EcoAudit AI")
st.sidebar.radio(
    "Display theme", ["Light", "Dark"], horizontal=True,
    key="theme_choice", on_change=sync_theme_choice,
    help="Choose a readable light or dark color theme."
)
st.sidebar.markdown("---")

pages = [
    "🏠 Home / Dashboard",
    "🏗️ Building Profile",
    "🔌 Appliance Inventory",
    "📊 Energy Consumption Analysis",
    "🔍 Energy Audit Findings",
    "🤖 AI Energy Assistant",
    "📜 Indian Codes & Standards",
    "💡 Recommendations & Savings",
    "📄 Download Audit Report",
    "ℹ️ About the Project"
]

selected_page = st.sidebar.radio("Navigation", pages, label_visibility="collapsed")
st.session_state.current_page = selected_page

st.sidebar.markdown("---")

# Sample data controls
st.sidebar.markdown("#### 📋 Quick Actions")
if st.sidebar.button("📥 Load Sample Building", use_container_width=True):
    with open(os.path.join(os.path.dirname(__file__), 'data', 'sample_building.json'), 'r') as f:
        sample = json.load(f)
    st.session_state.building_profile = sample['building_profile']
    st.session_state.appliances = sample['appliances']
    st.session_state.monthly_bills = sample['monthly_bills']
    st.session_state.is_sample_data = True
    st.rerun()

if st.sidebar.button("🗑️ Clear All Data / New Audit", use_container_width=True):
    st.session_state.building_profile = {}
    st.session_state.appliances = []
    st.session_state.monthly_bills = {}
    st.session_state.is_sample_data = False
    st.session_state.chat_history = []
    st.session_state.chat_sessions = {}
    st.session_state.active_chat_id = None
    st.session_state.pop('active_chat_selector', None)
    st.session_state.pop('loaded_chat_id', None)
    st.rerun()

# Show data status
st.sidebar.markdown("---")
st.sidebar.markdown("#### 📊 Data Status")
has_profile = bool(st.session_state.building_profile)
has_appliances = len(st.session_state.appliances) > 0
has_bills = any(v for v in st.session_state.monthly_bills.values() if v and v > 0) if st.session_state.monthly_bills else False

st.sidebar.markdown(f"{'✅' if has_profile else '⬜'} Building Profile")
st.sidebar.markdown(f"{'✅' if has_appliances else '⬜'} Appliance Inventory ({len(st.session_state.appliances)} items)")
st.sidebar.markdown(f"{'✅' if has_bills else '⬜'} Monthly Bills")

if st.session_state.is_sample_data:
    st.sidebar.warning("📋 Using sample data")


# ─── Helper Functions ───
def get_processed_data():
    """Process current session data and return computed results."""
    appliance_df = process_appliance_inventory(st.session_state.appliances)
    tariff = st.session_state.building_profile.get('tariff', 7.0) or 7.0
    summary = get_consumption_summary(appliance_df, tariff)
    return appliance_df, summary

def render_metric_card(label, value, unit=""):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-unit">{unit}</div>
    </div>
    """, unsafe_allow_html=True)

def show_sample_banner():
    """Show sample data warning banner."""
    if st.session_state.is_sample_data:
        st.markdown("""
        <div class="sample-banner">
            ⚠️ <strong>Illustrative Sample Data</strong> — This is not a measured real building. 
            All values are assumptions for demonstration. You can edit or clear this data.
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# PAGE: HOME / DASHBOARD
# ════════════════════════════════════════════════════
if selected_page == "🏠 Home / Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>🏠 EcoAudit AI</h1>
        <p>AI-Powered Residential Building Energy Audit and Efficiency Assessment</p>
    </div>
    """, unsafe_allow_html=True)
    
    show_sample_banner()

    appliance_df, summary = get_processed_data()
    
    if not st.session_state.appliances:
        st.info("👋 **Welcome to EcoAudit AI!** Start by loading the sample building data or entering your own building profile and appliances using the sidebar navigation.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 🏗️ Step 1: Building Profile")
            st.markdown("Enter your building details — type, area, location, and features.")
        with col2:
            st.markdown("#### 🔌 Step 2: Appliances")
            st.markdown("Add your appliances with power ratings and usage hours.")
        with col3:
            st.markdown("#### 📊 Step 3: Analyze")
            st.markdown("View energy analysis, audit findings, and recommendations.")
    else:
        # Dashboard metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Est. Daily Consumption", f"{summary['total_daily_kwh']:.1f}", "kWh/day")
        with col2:
            render_metric_card("Est. Monthly Consumption", f"{summary['total_monthly_kwh']:.1f}", "kWh/month")
        with col3:
            render_metric_card("Est. Monthly Cost", f"₹{summary['monthly_cost_inr']:,.0f}", f"at ₹{summary['tariff_used']}/kWh")
        with col4:
            render_metric_card("Est. Annual Cost", f"₹{summary['annual_cost_inr']:,.0f}", "per year")
        
        st.markdown("---")
        
        # Charts row
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("##### ⚡ Top Energy Consumers")
            top = get_top_consumers(appliance_df, 7)
            if not top.empty:
                fig = px.bar(top, x='monthly_kwh', y='name', orientation='h',
                            color='monthly_kwh',
                            color_continuous_scale=['#a8d5a2', '#228B22'],
                            labels={'monthly_kwh': 'Monthly kWh', 'name': ''},
                            text='monthly_kwh')
                fig.update_layout(height=350, showlegend=False, 
                                coloraxis_showscale=False,
                                margin=dict(l=0, r=20, t=10, b=30),
                                yaxis=dict(autorange='reversed'))
                fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.markdown("##### 📊 Consumption Distribution")
            if not appliance_df.empty:
                fig = px.pie(appliance_df, values='monthly_kwh', names='name',
                            color_discrete_sequence=px.colors.sequential.Greens_r,
                            hole=0.4)
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=30))
                fig.update_traces(textinfo='percent+label', textposition='inside',
                                 insidetextorientation='radial')
                st.plotly_chart(fig, use_container_width=True)
        
        # Monthly bills trend
        if st.session_state.monthly_bills:
            valid_bills = {k: v for k, v in st.session_state.monthly_bills.items() if v and v > 0}
            if valid_bills:
                st.markdown("##### 📈 Monthly Electricity Consumption Trend")
                month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                ordered_bills = {m: valid_bills[m] for m in month_order if m in valid_bills}
                bill_df = pd.DataFrame({'Month': list(ordered_bills.keys()), 
                                       'Consumption (kWh)': list(ordered_bills.values())})
                fig = px.line(bill_df, x='Month', y='Consumption (kWh)', markers=True,
                            line_shape='spline')
                fig.update_traces(line=dict(color='#228B22', width=3),
                                marker=dict(size=10, color='#1a5c1a'))
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=30))
                st.plotly_chart(fig, use_container_width=True)
        
        # Key findings preview
        findings = generate_audit_findings(appliance_df, st.session_state.building_profile,
                                           analyze_monthly_bills(st.session_state.monthly_bills,
                                                                summary['tariff_used']) if st.session_state.monthly_bills else None,
                                           summary)
        data_findings = findings.get('data_supported', [])
        if data_findings:
            st.markdown("##### 🔍 Key Findings Preview")
            for f in data_findings[:3]:
                severity_class = 'warning' if f.get('severity') == 'warning' else ''
                st.markdown(f"""
                <div class="finding-card {severity_class}">
                    <strong>{f.get('icon', '📋')} {f.get('category', '')}</strong><br>
                    {f.get('finding', '')}
                </div>
                """, unsafe_allow_html=True)
            if len(data_findings) > 3:
                st.info(f"📋 {len(data_findings) - 3} more findings available. Navigate to **Energy Audit Findings** for the complete list.")


# ════════════════════════════════════════════════════
# PAGE: BUILDING PROFILE
# ════════════════════════════════════════════════════
elif selected_page == "🏗️ Building Profile":
    st.markdown("## 🏗️ Building Profile")
    st.markdown("Enter your residential building information. Fields marked with * are recommended but not required.")
    show_sample_banner()
    
    profile = st.session_state.building_profile
    
    with st.form("building_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Building Name / Project Identifier", 
                               value=profile.get('name', ''))
            building_type = st.selectbox("Building Type", 
                                        ['Apartment', 'Independent House', 'Villa', 'Row House', 'Other'],
                                        index=['Apartment', 'Independent House', 'Villa', 'Row House', 'Other'].index(
                                            profile.get('building_type', 'Apartment')))
            city = st.text_input("City", value=profile.get('city', ''))
            state = st.text_input("State", value=profile.get('state', ''))
            climate_zone = st.selectbox("Climate Zone (if known)", 
                                       ['Not specified', 'Composite', 'Hot-Dry', 'Warm-Humid', 'Temperate', 'Cold'],
                                       index=['Not specified', 'Composite', 'Hot-Dry', 'Warm-Humid', 'Temperate', 'Cold'].index(
                                           profile.get('climate_zone', 'Not specified')))
            num_floors = st.number_input("Number of Floors", min_value=1, max_value=50,
                                        value=profile.get('num_floors', 1))
            num_units = st.number_input("Number of Residential Units", min_value=1, max_value=500,
                                       value=profile.get('num_units', 1))
            built_up_area = st.number_input("Approximate Built-up Area (sq.m)", min_value=0.0,
                                           value=float(profile.get('built_up_area', 0)))
            num_occupants = st.number_input("Number of Occupants", min_value=0, max_value=100,
                                           value=profile.get('num_occupants', 0))
        
        with col2:
            building_age = st.number_input("Building Age (years)", min_value=0, max_value=200,
                                          value=profile.get('building_age', 0))
            window_area = st.number_input("Approximate Window Area (sq.m, 0 if unknown)", 
                                         min_value=0.0, value=float(profile.get('window_area', 0)))
            window_orientation = st.text_input("Window Orientation (if known)", 
                                             value=profile.get('window_orientation', ''))
            roof_type = st.text_input("Roof Type (e.g., RCC slab, tiled, metal sheet)", 
                                    value=profile.get('roof_type', ''))
            roof_insulation = st.text_input("Roof Insulation Details (if known)", 
                                          value=profile.get('roof_insulation', ''))
            wall_construction = st.text_input("Wall Construction (e.g., brick, AAC block)", 
                                            value=profile.get('wall_construction', ''))
            natural_ventilation = st.selectbox("Natural Ventilation", 
                                             ['Not specified', 'Good', 'Moderate', 'Limited', 'Poor'],
                                             index=['Not specified', 'Good', 'Moderate', 'Limited', 'Poor'].index(
                                                 profile.get('natural_ventilation', 'Not specified')))
            lighting_type = st.selectbox("Primary Lighting Type", 
                                        ['Not specified', 'LED', 'CFL', 'Mix of LED and CFL', 
                                         'Incandescent', 'Tube lights', 'Mixed'],
                                        index=['Not specified', 'LED', 'CFL', 'Mix of LED and CFL',
                                               'Incandescent', 'Tube lights', 'Mixed'].index(
                                            profile.get('lighting_type', 'Not specified')))
            ac_availability = st.checkbox("Air Conditioning Available", 
                                         value=profile.get('ac_availability', False))
            solar_installation = st.checkbox("Solar Installation Present", 
                                           value=profile.get('solar_installation', False))
            tariff = st.number_input("Electricity Tariff (₹/kWh)", min_value=0.0, max_value=50.0,
                                    value=float(profile.get('tariff', 7.0)), step=0.5,
                                    help="Average flat-rate tariff. Actual tariffs may vary by slab.")
        
        submitted = st.form_submit_button("💾 Save Building Profile", use_container_width=True)
        
        if submitted:
            new_profile = {
                'name': name, 'building_type': building_type,
                'city': city, 'state': state,
                'climate_zone': climate_zone if climate_zone != 'Not specified' else '',
                'num_floors': num_floors, 'num_units': num_units,
                'built_up_area': built_up_area if built_up_area > 0 else None,
                'num_occupants': num_occupants if num_occupants > 0 else None,
                'building_age': building_age if building_age > 0 else None,
                'window_area': window_area if window_area > 0 else None,
                'window_orientation': window_orientation,
                'roof_type': roof_type, 'roof_insulation': roof_insulation,
                'wall_construction': wall_construction,
                'natural_ventilation': natural_ventilation if natural_ventilation != 'Not specified' else '',
                'lighting_type': lighting_type if lighting_type != 'Not specified' else '',
                'ac_availability': ac_availability,
                'solar_installation': solar_installation,
                'tariff': tariff
            }
            
            is_valid, errors = validate_building_profile(new_profile)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                st.session_state.building_profile = new_profile
                st.success("✅ Building profile saved successfully!")
    
    # Show current profile summary
    if profile:
        st.markdown("### 📋 Current Building Profile Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Building:** {profile.get('name', 'Not specified')}")
            st.markdown(f"**Type:** {profile.get('building_type', 'Not specified')}")
            st.markdown(f"**Location:** {profile.get('city', '')}, {profile.get('state', '')}")
            st.markdown(f"**Area:** {profile.get('built_up_area', 'N/A')} sq.m")
        with col2:
            st.markdown(f"**Occupants:** {profile.get('num_occupants', 'N/A')}")
            st.markdown(f"**Age:** {profile.get('building_age', 'N/A')} years")
            st.markdown(f"**Tariff:** ₹{profile.get('tariff', 'N/A')}/kWh")
            st.markdown(f"**AC:** {'Yes' if profile.get('ac_availability') else 'No'}")


# ════════════════════════════════════════════════════
# PAGE: APPLIANCE INVENTORY
# ════════════════════════════════════════════════════
elif selected_page == "🔌 Appliance Inventory":
    st.markdown("## 🔌 Appliance Inventory")
    st.markdown("Add, edit, and remove appliances. Power ratings are typically found on the appliance nameplate or in the product manual.")
    show_sample_banner()
    
    st.info("💡 **Note:** Rated power is the nameplate value. Actual average power draw may differ due to duty cycles "
            "(e.g., refrigerator compressors cycle on and off), thermostat behaviour, and operating conditions.")
    
    # Add new appliance
    st.markdown("### ➕ Add Appliance")
    
    with st.form("add_appliance_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            app_name = st.text_input("Appliance Name *")
            app_qty = st.number_input("Quantity *", min_value=1, max_value=100, value=1)
            app_power = st.number_input("Rated Power (Watts) *", min_value=0.0, max_value=50000.0, 
                                       value=0.0, step=10.0)
        with col2:
            app_hours = st.number_input("Average Hours of Use per Day *", min_value=0.0, 
                                       max_value=24.0, value=0.0, step=0.5)
            app_days = st.number_input("Days Used per Month *", min_value=0, max_value=31, value=30)
            app_category = st.selectbox("Usage Category", 
                                       ['General', 'Lighting', 'Cooling', 'Heating', 'Kitchen',
                                        'Laundry', 'Entertainment', 'Computing', 'Water Heating',
                                        'Utilities', 'Electronics', 'Networking', 'Other'])
        with col3:
            app_efficiency = st.text_input("Efficiency Information (optional)",
                                         placeholder="e.g., BEE 5-star, BLDC motor")
            app_source = st.selectbox("Power Rating Source", 
                                     ['Assumed', 'User-provided', 'Measured'],
                                     help="How was the power rating determined?")
        
        add_submitted = st.form_submit_button("➕ Add Appliance", use_container_width=True)
        
        if add_submitted:
            new_appliance = {
                'name': app_name, 'quantity': app_qty,
                'power_watts': app_power, 'hours_per_day': app_hours,
                'days_per_month': app_days, 'category': app_category,
                'efficiency_info': app_efficiency if app_efficiency else 'Not specified',
                'power_source': app_source
            }
            is_valid, errors = validate_appliance(new_appliance)
            if not is_valid:
                for err in errors:
                    st.error(err)
            else:
                st.session_state.appliances.append(new_appliance)
                st.success(f"✅ Added: {app_name}")
                st.rerun()
    
    # Common appliance presets
    with st.expander("📋 Quick-Add Common Appliances"):
        presets = [
            ("LED Light (9W)", 9, 6, 30, "Lighting"),
            ("CFL Light (18W)", 18, 5, 30, "Lighting"),
            ("Ceiling Fan (75W)", 75, 10, 30, "Cooling"),
            ("BLDC Fan (30W)", 30, 10, 30, "Cooling"),
            ("Split AC 1.5T (1500W)", 1500, 8, 25, "Cooling"),
            ("Refrigerator (150W)", 150, 24, 30, "Kitchen"),
            ("LED TV 43\" (80W)", 80, 5, 30, "Entertainment"),
            ("Washing Machine (500W)", 500, 1, 15, "Laundry"),
            ("Geyser 15L (2000W)", 2000, 0.5, 25, "Water Heating"),
            ("Water Pump 0.5HP (370W)", 370, 0.5, 30, "Utilities"),
            ("Desktop Computer (200W)", 200, 6, 25, "Computing"),
            ("Laptop (65W)", 65, 6, 25, "Computing"),
            ("Microwave (1200W)", 1200, 0.25, 25, "Kitchen"),
            ("Wi-Fi Router (12W)", 12, 24, 30, "Networking"),
        ]
        
        cols = st.columns(3)
        for i, (name, power, hours, days, cat) in enumerate(presets):
            col = cols[i % 3]
            if col.button(f"➕ {name}", key=f"preset_{i}", use_container_width=True):
                st.session_state.appliances.append({
                    'name': name.split('(')[0].strip(),
                    'quantity': 1, 'power_watts': power,
                    'hours_per_day': hours, 'days_per_month': days,
                    'category': cat, 'efficiency_info': 'Not specified',
                    'power_source': 'Assumed'
                })
                st.rerun()
    
    # Display current inventory
    st.markdown("### 📋 Current Appliance Inventory")
    
    if st.session_state.appliances:
        appliance_df = process_appliance_inventory(st.session_state.appliances)
        
        # Display as interactive table
        display_df = appliance_df[['name', 'quantity', 'power_watts', 'hours_per_day', 
                                    'days_per_month', 'daily_kwh', 'monthly_kwh', 
                                    'percentage_contribution', 'power_source']].copy()
        display_df.columns = ['Appliance', 'Qty', 'Power (W)', 'Hrs/Day', 'Days/Mo',
                              'Daily kWh', 'Monthly kWh', '% Share', 'Rating Source']
        display_df.index = range(1, len(display_df) + 1)
        
        st.dataframe(display_df, use_container_width=True, height=min(400, 40 + len(display_df) * 35))
        
        # Delete appliance
        if len(st.session_state.appliances) > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                del_idx = st.selectbox("Select appliance to remove", 
                                       range(len(st.session_state.appliances)),
                                       format_func=lambda i: st.session_state.appliances[i]['name'])
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Remove Selected", use_container_width=True):
                    removed = st.session_state.appliances.pop(del_idx)
                    st.success(f"Removed: {removed['name']}")
                    st.rerun()
        
        # Summary
        summary = get_consumption_summary(appliance_df, 
                                         st.session_state.building_profile.get('tariff', 7.0) or 7.0)
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Daily (kWh)", f"{summary['total_daily_kwh']:.2f}")
        with col2:
            st.metric("Total Monthly (kWh)", f"{summary['total_monthly_kwh']:.2f}")
        with col3:
            st.metric("Total Annual (kWh)", f"{summary['total_annual_kwh']:.2f}")
    else:
        st.info("No appliances added yet. Use the form above or quick-add presets to add appliances.")


# ════════════════════════════════════════════════════
# PAGE: ENERGY CONSUMPTION ANALYSIS
# ════════════════════════════════════════════════════
elif selected_page == "📊 Energy Consumption Analysis":
    st.markdown("## 📊 Energy Consumption Analysis")
    show_sample_banner()
    
    appliance_df, summary = get_processed_data()
    
    if not st.session_state.appliances:
        st.info("⚠️ No appliance data available. Please add appliances in the **Appliance Inventory** section.")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card("Daily Consumption", f"{summary['total_daily_kwh']:.2f}", "kWh")
        with col2:
            render_metric_card("Monthly Consumption", f"{summary['total_monthly_kwh']:.2f}", "kWh")
        with col3:
            render_metric_card("Monthly Cost", f"₹{summary['monthly_cost_inr']:,.0f}", 
                             f"at ₹{summary['tariff_used']}/kWh")
        with col4:
            render_metric_card("Annual Cost", f"₹{summary['annual_cost_inr']:,.0f}", "per year")
        
        st.markdown("---")
        
        # Appliance-wise breakdown
        st.markdown("### ⚡ Appliance-wise Energy Consumption")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            fig = px.bar(appliance_df.sort_values('monthly_kwh', ascending=True), 
                        x='monthly_kwh', y='name', orientation='h',
                        color='monthly_kwh',
                        color_continuous_scale=['#c8e6c9', '#1b5e20'],
                        labels={'monthly_kwh': 'Monthly kWh', 'name': 'Appliance'},
                        title='Monthly Consumption by Appliance')
            fig.update_layout(height=max(300, len(appliance_df) * 35),
                            coloraxis_showscale=False,
                            margin=dict(l=0, r=20, t=40, b=30))
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            fig = px.pie(appliance_df, values='monthly_kwh', names='name',
                        color_discrete_sequence=px.colors.sequential.Greens_r,
                        title='Consumption Distribution', hole=0.35)
            fig.update_layout(height=max(300, len(appliance_df) * 35),
                            margin=dict(l=0, r=0, t=40, b=30))
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.markdown("### 📋 Detailed Consumption Table")
        detail_df = appliance_df[['name', 'quantity', 'power_watts', 'hours_per_day',
                                   'days_per_month', 'daily_kwh', 'monthly_kwh', 
                                   'annual_kwh', 'percentage_contribution']].copy()
        detail_df.columns = ['Appliance', 'Qty', 'Power (W)', 'Hrs/Day', 'Days/Mo',
                            'Daily (kWh)', 'Monthly (kWh)', 'Annual (kWh)', '% of Total']
        st.dataframe(detail_df, use_container_width=True)
        
        st.info("📝 **Note:** These are estimates based on rated power and assumed usage patterns. "
               "Actual consumption may differ due to duty cycles, thermostat behaviour, and operating conditions. "
               "Annual estimates assume the monthly usage pattern remains constant.")
        
        # ── Monthly Bill Section ──
        st.markdown("---")
        st.markdown("### 📅 Monthly Electricity Bills")
        st.markdown("Enter billed consumption (kWh) for available months. Leave at 0 for unavailable months.")
        
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        with st.form("monthly_bills_form"):
            cols = st.columns(4)
            bill_inputs = {}
            for i, month in enumerate(month_names):
                col = cols[i % 4]
                current_val = st.session_state.monthly_bills.get(month, 0) or 0
                bill_inputs[month] = col.number_input(month[:3], min_value=0.0, max_value=10000.0,
                                                     value=float(current_val), step=10.0,
                                                     key=f"bill_{month}")
            
            if st.form_submit_button("💾 Save Monthly Bills", use_container_width=True):
                st.session_state.monthly_bills = bill_inputs
                st.success("✅ Monthly bill data saved!")
                st.rerun()
        
        # Bill analysis and comparison
        if st.session_state.monthly_bills:
            tariff = summary['tariff_used']
            bill_result = analyze_monthly_bills(st.session_state.monthly_bills, tariff)
            
            if 'error' not in bill_result:
                st.markdown("### 📈 Bill Analysis")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Monthly", f"{bill_result['average_monthly_kwh']:.0f} kWh")
                with col2:
                    st.metric("Highest Month", 
                             f"{bill_result['highest_month']} ({bill_result['highest_consumption_kwh']:.0f} kWh)")
                with col3:
                    st.metric("Lowest Month", 
                             f"{bill_result['lowest_month']} ({bill_result['lowest_consumption_kwh']:.0f} kWh)")
                
                # Trend chart
                valid_bills = {k: v for k, v in st.session_state.monthly_bills.items() if v and v > 0}
                if valid_bills:
                    ordered = {m: valid_bills[m] for m in month_names if m in valid_bills}
                    bill_chart_df = pd.DataFrame({
                        'Month': list(ordered.keys()),
                        'Billed (kWh)': list(ordered.values())
                    })
                    fig = px.line(bill_chart_df, x='Month', y='Billed (kWh)', markers=True,
                                title='Monthly Bill Consumption Trend')
                    fig.update_traces(line=dict(color='#228B22', width=3),
                                    marker=dict(size=10))
                    fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=30))
                    st.plotly_chart(fig, use_container_width=True)
                
                if not bill_result.get('is_complete_year'):
                    st.warning(bill_result.get('data_note', 'Partial year data available.'))
                
                # Bill vs calculated comparison
                avg_billed = bill_result['average_monthly_kwh']
                comparison = compare_bill_vs_calculated(summary['total_monthly_kwh'], avg_billed)
                
                st.markdown("### 🔄 Calculated vs. Billed Comparison")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Calculated (Appliances)", f"{comparison['calculated_monthly_kwh']:.1f} kWh/month")
                with col2:
                    st.metric("Billed (Average)", f"{comparison['billed_monthly_kwh']:.1f} kWh/month")
                with col3:
                    st.metric("Difference", f"{comparison['absolute_difference_kwh']:.1f} kWh ({comparison['percentage_difference']:.1f}%)")
                
                # Comparison chart
                comp_df = pd.DataFrame({
                    'Source': ['Calculated (Appliances)', 'Billed (Average)'],
                    'Monthly kWh': [comparison['calculated_monthly_kwh'], comparison['billed_monthly_kwh']]
                })
                fig = px.bar(comp_df, x='Source', y='Monthly kWh', color='Source',
                            color_discrete_map={'Calculated (Appliances)': '#4CAF50', 'Billed (Average)': '#2196F3'},
                            title='Calculated vs. Billed Consumption')
                fig.update_layout(height=300, showlegend=False, margin=dict(l=0, r=0, t=40, b=30))
                st.plotly_chart(fig, use_container_width=True)
                
                if comparison['possible_reasons']:
                    st.markdown("**Possible reasons for discrepancy:**")
                    for reason in comparison['possible_reasons']:
                        st.markdown(f"- {reason}")


# ════════════════════════════════════════════════════
# PAGE: ENERGY AUDIT FINDINGS
# ════════════════════════════════════════════════════
elif selected_page == "🔍 Energy Audit Findings":
    st.markdown("## 🔍 Energy Audit Findings")
    show_sample_banner()
    
    appliance_df, summary = get_processed_data()
    tariff = summary['tariff_used']
    
    bill_result = None
    if st.session_state.monthly_bills:
        bill_result = analyze_monthly_bills(st.session_state.monthly_bills, tariff)
        if 'error' in bill_result:
            bill_result = None
    
    findings = generate_audit_findings(appliance_df, st.session_state.building_profile,
                                       bill_result, summary)
    
    # Data-supported findings
    data_findings = findings.get('data_supported', [])
    if data_findings:
        st.markdown("### ✅ Findings Supported by User Data")
        st.markdown("_These findings are directly based on the data you entered._")
        for f in data_findings:
            severity_class = 'warning' if f.get('severity') == 'warning' else ''
            st.markdown(f"""
            <div class="finding-card {severity_class}">
                <strong>{f.get('icon', '📋')} {f.get('category', '')}</strong><br>
                {f.get('finding', '')}
            </div>
            """, unsafe_allow_html=True)
    
    # Assumption-based findings
    assumption_findings = findings.get('assumption_based', [])
    if assumption_findings:
        st.markdown("### ⚠️ Findings Based on Assumptions")
        st.markdown("_These findings are based on general assumptions and industry averages, not on measurements from your building._")
        for f in assumption_findings:
            st.markdown(f"""
            <div class="finding-card warning">
                <strong>{f.get('icon', '📋')} {f.get('category', '')}</strong><br>
                {f.get('finding', '')}
            </div>
            """, unsafe_allow_html=True)
    
    # Inspection-needed findings
    inspection_findings = findings.get('requires_inspection', [])
    if inspection_findings:
        st.markdown("### 🔎 Findings Requiring Additional Inspection")
        st.markdown("_These observations require professional measurement or site inspection for verification._")
        for f in inspection_findings:
            st.markdown(f"""
            <div class="finding-card">
                <strong>{f.get('icon', '📋')} {f.get('category', '')}</strong><br>
                {f.get('finding', '')}
            </div>
            """, unsafe_allow_html=True)
    
    if not data_findings and not assumption_findings and not inspection_findings:
        st.info("No findings available. Please enter building and appliance data to generate audit findings.")
    
    # Building Envelope Assessment
    st.markdown("---")
    st.markdown("## 🏗️ Building Envelope Assessment (Preliminary)")
    
    envelope = generate_building_envelope_assessment(st.session_state.building_profile)
    
    if envelope:
        for obs in envelope:
            with st.expander(f"📐 {obs.get('aspect', 'N/A')}", expanded=True):
                st.markdown(f"**Observation:** {obs.get('observation', '')}")
                st.markdown(f"**Confidence:** {obs.get('confidence', '')}")
                st.markdown(f"**Recommendation:** {obs.get('recommendation', '')}")
    else:
        st.info("Enter building profile data to receive envelope observations.")


# ════════════════════════════════════════════════════
# PAGE: AI ENERGY ASSISTANT
# ════════════════════════════════════════════════════
elif selected_page == "🤖 AI Energy Assistant":
    st.markdown("## 🤖 EcoAudit AI Assistant")
    st.markdown("Ask questions about your building's energy consumption, Indian energy codes, "
                "energy-saving recommendations, and more.")
    
    ai_available, ai_status = check_ai_availability()
    provider = get_ai_provider()
    
    if ai_available:
        st.success(f"🟢 {ai_status}")
    elif provider == 'demo':
        st.warning(f"🟡 {ai_status}")
        st.info("Configure `OPENAI_API_KEY` in `.env` (recommended) or Streamlit secrets to enable live generative answers. "
                "If `GOOGLE_API_KEY` is set, the existing Gemini provider is used. Demo responses are limited curated answers, not live AI. "
                "See `.env.example` and restart Streamlit after changing environment settings.")
    else:
        st.error(f"🔴 {ai_status}")
        st.caption("Live AI is not ready. Fix the model setting or install the provider SDK, then retry.")
    
    show_sample_banner()

    response_language = st.selectbox(
        'Reply language',
        ['Auto (match my message)', 'English (India)', 'Hindi', 'Hinglish'],
        key='assistant_response_language',
        help='EcoAudit AI uses Indian terms, electricity units, and ₹ by default. '
             'Choose Hindi or Hinglish for replies in that style.',
    )

    # Keep multiple conversations available during this Streamlit session.
    # Streamlit session state preserves them across normal reruns.
    if not st.session_state.chat_sessions:
        initial_id = uuid.uuid4().hex
        st.session_state.chat_sessions[initial_id] = {
            'title': 'Previous conversation' if st.session_state.chat_history else 'New chat',
            'messages': list(st.session_state.chat_history),
        }
        st.session_state.active_chat_id = initial_id
    elif st.session_state.active_chat_id not in st.session_state.chat_sessions:
        st.session_state.active_chat_id = next(iter(st.session_state.chat_sessions))

    chat_ids = list(st.session_state.chat_sessions)
    previous_active_chat = st.session_state.get('loaded_chat_id')
    selected_chat = st.selectbox(
        'Chat history', chat_ids,
        index=chat_ids.index(st.session_state.active_chat_id),
        format_func=lambda chat_id: st.session_state.chat_sessions[chat_id]['title'],
        key='active_chat_selector',
        help='Switch between conversations in this browser session.',
    )
    st.session_state.active_chat_id = selected_chat
    if previous_active_chat != selected_chat:
        st.session_state.pop('last_chat_submission', None)
    st.session_state.loaded_chat_id = selected_chat
    st.session_state.chat_history = list(
        st.session_state.chat_sessions[selected_chat]['messages']
    )
    chat_col, history_col = st.columns([1, 2])
    with chat_col:
        if st.button('＋ New chat', use_container_width=True):
            new_id = uuid.uuid4().hex
            st.session_state.chat_sessions[new_id] = {'title': 'New chat', 'messages': []}
            st.session_state.active_chat_id = new_id
            st.session_state.active_chat_selector = new_id
            st.session_state.loaded_chat_id = new_id
            st.session_state.chat_history = []
            st.rerun()
    with history_col:
        st.caption(f"{len(chat_ids)} conversation{'s' if len(chat_ids) != 1 else ''} in this session")
    
    # Build comprehensive context from all current data
    appliance_df, summary = get_processed_data()
    tariff = summary['tariff_used']
    context = {}
    context['response_language'] = response_language
    context['is_sample_data'] = bool(st.session_state.is_sample_data)
    # Keep the assistant grounded in references already maintained by this project.
    context['verified_code_references'] = get_all_codes_and_standards()
    
    if st.session_state.building_profile:
        context['building_profile'] = st.session_state.building_profile
    
    if summary and summary.get('total_monthly_kwh', 0) > 0:
        context['consumption_summary'] = summary
    
    if not appliance_df.empty:
        # Top consumers
        top = get_top_consumers(appliance_df, 5)
        if not top.empty:
            context['top_consumers'] = [
                {'name': row['name'], 'monthly_kwh': round(row['monthly_kwh'], 1),
                 'percentage': round(row['percentage_contribution'], 1)}
                for _, row in top.iterrows()
            ]
        # ALL appliances for detailed queries
        context['all_appliances'] = [
            {'name': row['name'], 'quantity': int(row['quantity']),
             'power_watts': row['power_watts'], 'hours_per_day': row['hours_per_day'],
             'days_per_month': int(row['days_per_month']),
             'daily_kwh': round(row['daily_kwh'], 2),
             'monthly_kwh': round(row['monthly_kwh'], 1),
             'percentage': round(row['percentage_contribution'], 1),
             'category': row.get('category', 'General'),
             'power_source': row.get('power_source', 'Assumed')}
            for _, row in appliance_df.iterrows()
        ]
    
    # Bill analysis
    bill_result = None
    bill_comparison_data = None
    if st.session_state.monthly_bills:
        bill_result = analyze_monthly_bills(st.session_state.monthly_bills, tariff)
        if 'error' not in bill_result:
            context['bill_analysis'] = bill_result
            if summary.get('total_monthly_kwh', 0) > 0:
                bill_comparison_data = compare_bill_vs_calculated(
                    summary['total_monthly_kwh'],
                    bill_result.get('average_monthly_kwh', 0)
                )
                context['bill_comparison'] = bill_comparison_data
        else:
            bill_result = None
    
    # Audit findings
    if st.session_state.appliances:
        findings = generate_audit_findings(
            appliance_df, st.session_state.building_profile, bill_result, summary)
        data_findings = findings.get('data_supported', [])
        if data_findings:
            context['findings_summary'] = '\n'.join([f"- {f['finding']}" for f in data_findings[:5]])
        context['findings_detail'] = findings
    
    # Building envelope
    if st.session_state.building_profile:
        envelope = generate_building_envelope_assessment(st.session_state.building_profile)
        if envelope:
            context['envelope_assessment'] = envelope
    
    # Interventions
    if st.session_state.appliances:
        interventions = get_default_interventions(appliance_df, st.session_state.building_profile)
        if interventions:
            context['interventions'] = interventions
    
    def submit_assistant_message(message):
        """Submit once, passing prior turns (excluding the current user turn)."""
        message = message.strip()
        if not message:
            return
        fingerprint = f"{len(st.session_state.chat_history)}:{message}"
        if st.session_state.get('last_chat_submission') == fingerprint:
            return
        st.session_state.last_chat_submission = fingerprint
        previous_turns = list(st.session_state.chat_history)
        st.session_state.chat_history.append({'role': 'user', 'content': message})
        active_chat = st.session_state.chat_sessions[st.session_state.active_chat_id]
        active_chat['messages'] = list(st.session_state.chat_history)
        if active_chat['title'] == 'New chat':
            active_chat['title'] = message[:42] + ('…' if len(message) > 42 else '')
        with st.spinner("EcoAudit AI is thinking…"):
            response = get_ai_response(message, context, previous_turns)
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response.get('response', 'No response was returned.'),
            'mode': response.get('mode', 'Unknown'),
            'error': bool(response.get('error')),
        })
        active_chat['messages'] = list(st.session_state.chat_history)

    # Suggested prompts are optional shortcuts. The free-form input below accepts any question.
    with st.expander("💬 Suggested questions (optional)", expanded=False):
        st.caption("Choose a shortcut or ask any question in the chat box below.")
        suggested = get_suggested_questions()
        for row_start in range(0, len(suggested), 3):
            cols = st.columns(3)
            for offset, col in enumerate(cols):
                idx = row_start + offset
                if idx < len(suggested) and col.button(
                    suggested[idx], key=f"suggested_{idx}", use_container_width=True
                ):
                    submit_assistant_message(suggested[idx])
                    st.rerun()

    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg['role']):
            st.markdown(msg.get('content', ''))
            if msg.get('mode'):
                st.caption(f"Response mode: {msg['mode']}")
            if msg.get('error'):
                st.error("Request failed. Review the message above, then try again after checking your key, model, network, or provider quota.")

    if st.session_state.chat_history and st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.session_state.chat_sessions[st.session_state.active_chat_id]['messages'] = []
        st.session_state.chat_sessions[st.session_state.active_chat_id]['title'] = 'New chat'
        st.session_state.pop('last_chat_submission', None)
        st.rerun()

    user_input = st.chat_input("Ask EcoAudit AI anything… energy, Python, general questions, or Hinglish")
    if user_input:
        submit_assistant_message(user_input)
        st.rerun()


# ════════════════════════════════════════════════════
# PAGE: INDIAN CODES & STANDARDS
# ════════════════════════════════════════════════════
elif selected_page == "📜 Indian Codes & Standards":
    st.markdown("## 📜 Indian Energy Conservation Codes and Standards")
    st.markdown("Relevant codes, standards, and official resources for residential building energy efficiency in India.")
    
    # Disclaimer
    st.markdown(get_code_disclaimer())
    st.markdown("---")
    
    # Codes and standards
    codes = get_all_codes_and_standards()
    
    for code in codes:
        with st.expander(f"📑 {code['name']}", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Official Name:** {code['name']}")
                st.markdown(f"**Edition / Year:** {code['edition']}")
                st.markdown(f"**Issuing Authority:** {code['issuing_authority']}")
                st.markdown(f"**Subject:** {code['subject']}")
            with col2:
                st.markdown(f"**Official Source:** [{code['official_source']}]({code['official_source']})")
            
            st.markdown("---")
            st.markdown(f"**Relevance to Residential Energy Auditing:**")
            st.markdown(code['relevance'])
            
            st.markdown(f"**Applicability Limitations:**")
            st.warning(code['applicability_limitations'])
            
            if code.get('key_provisions'):
                st.markdown("**Key Provisions:**")
                for provision in code['key_provisions']:
                    st.markdown(f"- {provision}")
            
            st.info(f"📌 {code.get('verification_note', 'Verify from official sources.')}")
    
    # Climate zones section
    st.markdown("---")
    st.markdown("### 🌡️ Indian Climate Zones (as per BEE/ENS)")
    
    zones = get_climate_zones()
    cols = st.columns(len(zones))
    for i, zone in enumerate(zones):
        with cols[i]:
            st.markdown(f"**{zone['zone']}**")
            st.markdown(f"_{zone['description']}_")
            st.markdown(f"**Cities:** {zone['example_cities']}")
            st.caption(zone['key_considerations'])
    
    # BEE Star Label info
    st.markdown("---")
    st.markdown("### ⭐ BEE Standards & Labelling Programme")
    
    star_info = get_bee_star_label_info()
    st.markdown(f"**{star_info['programme_name']}**")
    st.markdown(star_info['description'])
    st.markdown(f"**Rating Scale:** {star_info['rating_scale']}")
    st.markdown(f"**Official Website:** [{star_info['official_website']}]({star_info['official_website']})")
    
    st.markdown("#### Common Residential Appliances:")
    
    for app in star_info['common_residential_appliances']:
        with st.expander(f"{'🏷️' if app['labelling_status']=='Mandatory' else '🔖'} {app['appliance']} — {app['labelling_status']}"):
            st.markdown(f"**Labelling Status:** {app['labelling_status']}")
            st.markdown(f"**Tip:** {app['tip']}")
            st.markdown(f"**Typical Savings:** {app['typical_savings']}")
    
    st.info(f"📝 {star_info['note']}")


# ════════════════════════════════════════════════════
# PAGE: RECOMMENDATIONS & SAVINGS
# ════════════════════════════════════════════════════
elif selected_page == "💡 Recommendations & Savings":
    st.markdown("## 💡 Energy-Saving Recommendations & Savings Calculator")
    show_sample_banner()
    
    appliance_df, summary = get_processed_data()
    tariff = summary['tariff_used']
    
    if not st.session_state.appliances:
        st.info("⚠️ No appliance data available. Please add appliances first to receive recommendations.")
    else:
        interventions = get_default_interventions(appliance_df, st.session_state.building_profile)
        
        if not interventions:
            st.info("No specific interventions identified based on the current data. Try adding more appliances or building details.")
        else:
            st.info("💡 **Note:** The reduction percentages below are assumed estimates unless supported by "
                   "project-specific evidence. You can adjust them to see how savings change. "
                   "Do not treat these as guaranteed outcomes.")
            
            total_monthly_saved = 0
            total_annual_saved = 0
            
            for i, intervention in enumerate(interventions):
                with st.expander(f"{'💡' if intervention['category']=='Lighting' else '⚡'} "
                               f"{intervention['name']}", expanded=True):
                    st.markdown(f"**{intervention['description']}**")
                    st.markdown(f"**Category:** {intervention['category']}")
                    st.markdown(f"**Baseline Monthly Consumption:** {intervention['baseline_monthly_kwh']:.1f} kWh")
                    st.caption(f"_Confidence: {intervention['confidence']}_")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        reduction_pct = st.slider(
                            f"Assumed Reduction (%)",
                            min_value=0, max_value=100,
                            value=int(intervention['default_reduction'] * 100),
                            key=f"reduction_{i}",
                            help="Adjust this percentage to see estimated savings."
                        )
                    with col2:
                        impl_cost = st.number_input(
                            "Implementation Cost (₹, optional)",
                            min_value=0.0, value=0.0, step=500.0,
                            key=f"cost_{i}"
                        )
                    
                    # Calculate savings
                    savings = calculate_savings_for_intervention(
                        intervention['baseline_monthly_kwh'],
                        reduction_pct / 100.0,
                        tariff=tariff,
                        implementation_cost=impl_cost if impl_cost > 0 else None
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Est. Monthly Savings", f"{savings['monthly_kwh_saved']:.1f} kWh",
                                 f"₹{savings['monthly_cost_saved_inr']:.0f}")
                    with col2:
                        st.metric("Est. Annual Savings", f"{savings['annual_kwh_saved']:.1f} kWh",
                                 f"₹{savings['annual_cost_saved_inr']:,.0f}")
                    with col3:
                        if savings.get('payback_months') is not None:
                            st.metric("Est. Payback", f"{savings['payback_months']:.1f} months",
                                     f"{savings.get('payback_years', 0):.1f} years")
                        elif impl_cost > 0:
                            st.metric("Est. Payback", "Insufficient data")
                    
                    total_monthly_saved += savings['monthly_kwh_saved']
                    total_annual_saved += savings['annual_kwh_saved']
                    
                    st.caption(savings.get('assumption_note', ''))
            
            # Total potential savings
            st.markdown("---")
            st.markdown("### 📊 Total Potential Savings Summary")
            st.warning("⚠️ **Important:** These totals assume all interventions are implemented independently. "
                      "Some savings may overlap. Actual combined savings may be lower than the sum.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                render_metric_card("Total Monthly Savings", f"{total_monthly_saved:.1f}", "kWh/month")
            with col2:
                render_metric_card("Total Monthly Cost Savings", 
                                 f"₹{total_monthly_saved * tariff:,.0f}", "per month")
            with col3:
                render_metric_card("Total Annual Cost Savings", 
                                 f"₹{total_annual_saved * tariff:,.0f}", "per year")
            
            # Before vs After chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Current Estimated',
                x=['Monthly Consumption'],
                y=[summary['total_monthly_kwh']],
                marker_color='#ef5350'
            ))
            fig.add_trace(go.Bar(
                name='After Interventions (Est.)',
                x=['Monthly Consumption'],
                y=[max(0, summary['total_monthly_kwh'] - total_monthly_saved)],
                marker_color='#4CAF50'
            ))
            fig.update_layout(title='Baseline vs. Estimated Post-Intervention Consumption',
                            yaxis_title='kWh/month', height=350, barmode='group',
                            margin=dict(l=0, r=0, t=40, b=30))
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════
# PAGE: DOWNLOAD AUDIT REPORT
# ════════════════════════════════════════════════════
elif selected_page == "📄 Download Audit Report":
    st.markdown("## 📄 Download Energy Audit Report")
    show_sample_banner()
    
    if not st.session_state.appliances and not st.session_state.building_profile:
        st.info("⚠️ No data available. Please enter building and appliance data, or load sample data, before generating a report.")
    else:
        st.markdown("Generate a comprehensive PDF report containing your building profile, "
                   "appliance inventory, energy analysis, audit findings, and recommendations.")
        
        st.markdown("### Report Contents:")
        st.markdown("""
        1. **Scope and Methodology** — Audit approach and calculation methods
        2. **Building Profile** — Your building details
        3. **Appliance Inventory** — All appliances with consumption estimates
        4. **Consumption Summary** — Daily, monthly, and annual estimates
        5. **Bill Comparison** — Calculated vs. billed consumption (if available)
        6. **Monthly Bill Analysis** — Trends and patterns (if available)
        7. **Audit Findings** — Categorized observations
        8. **Envelope Assessment** — Preliminary building envelope observations
        9. **Recommendations** — Energy-saving interventions with estimated savings
        10. **Code References** — Relevant Indian energy conservation standards
        11. **Limitations** — What the audit covers and doesn't cover
        """)
        
        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
            try:
                with st.spinner("Generating report..."):
                    appliance_df, summary = get_processed_data()
                    tariff = summary['tariff_used']
                    
                    bill_result = None
                    bill_comparison = None
                    if st.session_state.monthly_bills:
                        bill_result = analyze_monthly_bills(st.session_state.monthly_bills, tariff)
                        if 'error' in bill_result:
                            bill_result = None
                        elif bill_result:
                            bill_comparison = compare_bill_vs_calculated(
                                summary['total_monthly_kwh'],
                                bill_result.get('average_monthly_kwh', 0)
                            )
                    
                    findings = generate_audit_findings(
                        appliance_df, st.session_state.building_profile,
                        bill_result, summary
                    )
                    
                    envelope = generate_building_envelope_assessment(st.session_state.building_profile)
                    
                    interventions = get_default_interventions(appliance_df, st.session_state.building_profile)
                    for intervention in interventions:
                        savings = calculate_savings_for_intervention(
                            intervention['baseline_monthly_kwh'],
                            intervention['default_reduction'],
                            tariff=tariff
                        )
                        intervention['savings'] = savings
                    
                    pdf_bytes = generate_report(
                        building_profile=st.session_state.building_profile,
                        appliance_df=appliance_df,
                        consumption_summary=summary,
                        bill_analysis=bill_result,
                        bill_comparison=bill_comparison,
                        audit_findings=findings,
                        envelope_assessment=envelope,
                        interventions=interventions,
                        is_sample_data=st.session_state.is_sample_data
                    )
                
                building_name = st.session_state.building_profile.get('name', 'Building')
                safe_name = "".join(c for c in building_name if c.isalnum() or c in ' -_')[:50]
                filename = f"EcoAudit_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                st.success("✅ Report generated successfully!")
                st.download_button(
                    label="⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except ImportError as e:
                st.error(f"❌ Report generation requires the fpdf2 package. Install with: `pip install fpdf2`")
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
                st.info("Please check that all data is valid and try again.")


# ════════════════════════════════════════════════════
# PAGE: ABOUT THE PROJECT
# ════════════════════════════════════════════════════
elif selected_page == "ℹ️ About the Project":
    st.markdown("## ℹ️ About EcoAudit AI")
    
    st.markdown("""
    ### Project Overview
    
    **EcoAudit AI** is an AI-powered residential building energy audit application designed as an 
    academic project. It provides preliminary energy analysis, identifies potential energy-saving 
    opportunities, and generates comprehensive audit reports.
    
    ### What This Application Does
    
    - ✅ Estimates residential electricity consumption based on appliance inventory
    - ✅ Identifies major energy-consuming appliances
    - ✅ Calculates monthly and annual energy costs
    - ✅ Compares calculated consumption with actual bills
    - ✅ Generates categorized energy audit findings
    - ✅ Provides preliminary building envelope observations
    - ✅ Suggests potential energy-saving interventions with estimated savings
    - ✅ References relevant Indian energy conservation codes and standards
    - ✅ Offers an AI-powered chatbot for energy efficiency Q&A
    - ✅ Generates downloadable PDF audit reports
    
    ### What This Application Does NOT Do
    
    - ❌ Provide a certified professional energy audit
    - ❌ Prove or certify legal code compliance
    - ❌ Replace professional energy auditors or engineers
    - ❌ Guarantee energy savings or financial returns
    - ❌ Perform detailed thermal simulations
    - ❌ Measure actual energy consumption (uses estimates)
    
    ### Technology Stack
    
    | Component | Technology |
    |-----------|-----------|
    | Web Framework | Streamlit |
    | Data Processing | Pandas, NumPy |
    | Visualizations | Plotly |
    | PDF Reports | fpdf2 |
    | AI Chatbot | Google Gemini / OpenAI API (optional) |
    | Language | Python 3.11+ |
    
    ### Calculation Methodology
    
    **Daily Consumption:** Quantity × Rated Power (W) × Hours/Day ÷ 1000 = kWh
    
    **Monthly Consumption:** Quantity × Rated Power (W) × Hours/Day × Days/Month ÷ 1000 = kWh
    
    **Annual Consumption:** Monthly Consumption × 12 (assuming constant monthly usage)
    
    **Cost:** Consumption (kWh) × Tariff (₹/kWh)
    
    ### Key Assumptions and Limitations
    
    1. Rated power is used as a proxy for actual power draw
    2. Usage hours are estimated averages, not continuous measurements
    3. Electricity tariff is a flat rate (actual tariffs may use slabs)
    4. Annual projections assume constant monthly usage
    5. Savings estimates use assumed reduction percentages
    6. Building envelope assessment is qualitative
    
    ### AI Integration
    
    The chatbot supports two modes:
    - **Full AI Mode:** Uses OpenAI API for nuanced, context-aware responses (requires API key)
    - **Demo Mode:** Uses a curated knowledge base with pre-written responses (no API key needed)
    
    ### References
    
    - [Bureau of Energy Efficiency (BEE)](https://beeindia.gov.in/)
    - [BEE Star Label Programme](https://beestarlabel.com/)
    - [Bureau of Indian Standards (BIS)](https://www.bis.gov.in/)
    - [Central Electricity Authority (CEA)](https://cea.nic.in/)
    
    ---
    
    ### Academic Context
    
    This project was developed as an academic project under a Civil Engineering-related minor, 
    demonstrating the application of data science concepts to residential building energy efficiency.
    
    **Disclaimer:** This tool provides preliminary educational analysis. It does not constitute a 
    professional energy audit, legal code compliance assessment, or engineering recommendation.
    """)
    
    st.markdown("---")
    st.markdown("#### 📊 Application Version")
    st.markdown(f"- **Version:** 1.0.0")
    st.markdown(f"- **Last Updated:** {datetime.now().strftime('%B %Y')}")
    st.markdown(f"- **Python:** {os.sys.version.split()[0]}")
    
    ai_available, ai_status = check_ai_availability()
    st.markdown(f"- **AI Mode:** {'🟢 Full AI' if ai_available else '🟡 Demo Mode'}")
