# EcoAudit-AI
AI-Powered Residential Building Energy Audit System

An academic project demonstrating the application of data science and AI to residential building energy efficiency assessment in India.

---

## Features

- ✅ Residential building energy consumption estimation from appliance inventory
- ✅ Appliance-wise energy breakdown with interactive charts
- ✅ Calculated vs. billed consumption comparison
- ✅ Categorised energy audit findings (data-supported, assumption-based, inspection-required)
- ✅ Preliminary building envelope assessment
- ✅ Energy-saving recommendations with estimated savings and payback calculator
- ✅ Indian energy conservation codes and standards reference (ENS, ECBC, ECSBC, NBC, BEE S&L)
- ✅ **AI-powered conversational chatbot** — building-aware, supports Indian energy codes
- ✅ Downloadable PDF audit report
- ✅ Sample building data for quick demonstration

---

## Quick Start

### Prerequisites

- Python 3.11 or later
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd EcoAudit-AI-main

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The application opens in your browser at `http://localhost:8501`.

### Loading Sample Data

Click **📥 Load Sample Building** in the sidebar to load a demonstration dataset (a hypothetical 3BHK apartment in New Delhi). All sample values are illustrative assumptions.

---

## AI Chatbot Setup

The EcoAudit AI Assistant operates in two modes:

### Demo Mode (no API key configured)

- Uses a built-in knowledge base with building-aware responses
- Responds using your current building data, appliance inventory, bills, and audit findings
- Covers energy consumption, Indian codes, savings recommendations, and more
- **Limitation:** Responses are rule-based, not generatively conversational. Complex or novel questions may receive a generic fallback.

### Live Generative AI Mode (requires API key)

OpenAI is used when `OPENAI_API_KEY` is configured. The assistant uses the official OpenAI Python SDK Responses API and sends recent conversation turns plus current audit context. When both supported provider keys are configured, the existing Google-first provider priority is retained.

#### OpenAI (recommended)

1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Copy `.env.example` to `.env` in the project root and set:
   ```env
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4.1-mini
   ```
3. Restart Streamlit and open **AI Energy Assistant**. It reports the selected provider/model. Ask a question in the free-form chat input; suggested questions are optional shortcuts. API failures are shown with retry guidance and never disguised as demo responses.

#### Google Gemini (alternative)

1. Get an API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Set these values in `.env`:
   ```env
   GOOGLE_API_KEY=your-google-api-key-here
   GOOGLE_MODEL=gemini-3.8-flash
   ```

#### Streamlit Secrets

For deployment on Streamlit Cloud, add keys to `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-key-here"
OPENAI_MODEL = "gpt-4.1-mini"
```

When Gemini is selected, use `GOOGLE_API_KEY` and optionally `GOOGLE_MODEL` instead. Do not commit keys. Without a configured key the assistant explicitly reports Demo Mode; demo responses are curated, limited, and not generative AI.

> ⚠️ **Never commit `.env` or `secrets.toml` to version control.** The `.gitignore` already excludes these files.

---

## Project Structure

```
EcoAudit-AI-main/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── data/
│   └── sample_building.json        # Sample building data for demonstration
├── modules/
│   ├── __init__.py
│   ├── ai_assistant.py             # AI chatbot (API + demo mode)
│   ├── audit_engine.py             # Audit findings and envelope assessment
│   ├── building_codes.py           # Indian codes and standards reference
│   ├── data_validation.py          # Input validation
│   ├── energy_calculations.py      # Energy consumption calculations
│   └── report_generator.py         # PDF report generation
├── tests/
│   └── test_energy_calculations.py # Unit tests for calculations
└── docs/
    ├── code_references.md          # Code references documentation
    └── methodology.md              # Calculation methodology
```

---

## Chatbot Capabilities

The AI assistant can answer questions about:

| Category | Examples |
|----------|----------|
| **Energy Consumption** | "What are my top consuming appliances?", "Show my total energy usage" |
| **Bills & Costs** | "How does my calculated consumption compare to bills?", "Monthly cost?" |
| **Audit Findings** | "What are the main findings?", "Describe my building's energy profile" |
| **Indian Codes** | "Which codes apply to my building?", "What is Eco Niwas Samhita?" |
| **Savings** | "How can I reduce my bill?", "Which measures should I prioritise?" |
| **Building Envelope** | "What about my roof insulation?", "Window assessment?" |
| **Methodology** | "How are calculations done?", "What assumptions are used?" |
| **General** | "How does an energy audit work?", "What is kWh?" |
| **Hinglish** | "Mere ghar ka bijli bill kaise kam karein?" |

### Chatbot Limitations

- **Demo mode** uses keyword matching — it cannot understand arbitrary phrasing or complex multi-part questions
- **AI mode** depends on the language model's capabilities and may occasionally produce inaccurate information
- The chatbot does **not** invent building measurements, guarantee savings, or assess legal code compliance
- Code-related answers are educational — always verify from official sources
- Savings estimates are approximate ranges, not guaranteed outcomes
- The chatbot does not have access to real-time electricity tariff data or live regulatory updates

---

## Calculation Methodology

| Metric | Formula |
|--------|---------|
| Daily Consumption | Quantity × Rated Power (W) × Hours/Day ÷ 1000 = kWh |
| Monthly Consumption | Quantity × Rated Power (W) × Hours/Day × Days/Month ÷ 1000 = kWh |
| Annual Consumption | Monthly Consumption × 12 |
| Electricity Cost | Consumption (kWh) × Tariff (₹/kWh) |

**Key assumptions:** Rated power as proxy for actual draw, user-estimated usage hours, flat tariff rate, constant monthly usage for annual projection.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Web Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualisations | Plotly |
| PDF Reports | fpdf2 |
| AI Chatbot | Google Gemini / OpenAI API (optional) |
| Language | Python 3.11+ |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## References

- [Bureau of Energy Efficiency (BEE)](https://beeindia.gov.in/)
- [BEE Star Label Programme](https://beestarlabel.com/)
- [Bureau of Indian Standards (BIS)](https://www.bis.gov.in/)
- [Central Electricity Authority (CEA)](https://cea.nic.in/)

---

## Disclaimer

This tool provides **preliminary educational analysis**. It does not constitute a professional energy audit, legal code compliance assessment, or engineering recommendation. For formal assessments, consult a BEE-certified energy auditor.

---

## License

Academic project — see repository for licence details.
