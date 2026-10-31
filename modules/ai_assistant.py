"""
EcoAudit AI — AI Energy Audit Assistant

Provides an AI-powered chatbot for answering questions about residential
energy consumption, audit results, Indian energy codes, and energy-saving
measures.

Supports:
- Full AI mode: Uses Google Gemini API or OpenAI API when credentials are
  available. The provider is selected automatically based on which API key
  is configured (GOOGLE_API_KEY checked first, then OPENAI_API_KEY).
- Demo mode: Uses a comprehensive, building-aware curated knowledge base
  with deterministic responses. Clearly labelled as demo mode.
"""
import os
import re
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from dotenv import load_dotenv
    # Streamlit does not load .env files automatically. Load this project's
    # local file so the UI's setup instructions work as written. Existing
    # process environment variables take precedence and are never overwritten.
    load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
except ImportError:
    # Environment variables and Streamlit secrets remain supported without
    # python-dotenv; requirements.txt includes it for normal installations.
    pass


# ─── Provider Detection ────────────────────────────────────────────

def _get_google_key() -> str:
    """Return the Google API key from env / Streamlit secrets, or ''."""
    key = os.environ.get('GOOGLE_API_KEY', '').strip()
    if key and not _is_placeholder_key(key):
        return key
    try:
        import streamlit as st
        key = st.secrets.get('GOOGLE_API_KEY', '').strip()
        if key and not _is_placeholder_key(key):
            return key
    except Exception:
        pass
    return ''


def _get_openai_key() -> str:
    """Return the OpenAI API key from env / Streamlit secrets, or ''."""
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if key and not _is_placeholder_key(key):
        return key
    try:
        import streamlit as st
        key = st.secrets.get('OPENAI_API_KEY', '').strip()
        if key and not _is_placeholder_key(key):
            return key
    except Exception:
        pass
    return ''


def _is_placeholder_key(key: str) -> bool:
    return bool(re.fullmatch(r'your[-_].*[-_]key[-_]here', key.strip(), re.IGNORECASE))


def _setting(name: str, default: str) -> str:
    value = os.environ.get(name, '').strip()
    if value:
        return value
    try:
        import streamlit as st
        value = str(st.secrets.get(name, '')).strip()
        return value or default
    except Exception:
        return default


def _configured_model(provider: str) -> str:
    if provider == 'openai':
        return _setting('OPENAI_MODEL', 'gpt-4.1-mini')
    if provider == 'google':
        return _setting('GOOGLE_MODEL', 'gemini-3.8-flash')
    return ''


def _model_is_supported(provider: str, model: str) -> bool:
    """Reject empty or clearly unsupported model identifiers before requests."""
    if provider == 'openai':
        pattern = r'(?:gpt-(?:4(?:\.[0-9]+)?|4o|[5-9](?:\.[0-9]+)?)(?:-[a-z0-9.-]+)?|o[134](?:-[a-z0-9.-]+)?|chatgpt-4o-latest)'
        return bool(re.fullmatch(pattern, model))
    if provider == 'google':
        return bool(re.fullmatch(r'gemini-[A-Za-z0-9.-]+', model))
    return False


def get_ai_provider() -> str:
    """Return the active AI provider: 'google', 'openai', or 'demo'."""
    if _get_google_key():
        return 'google'
    if _get_openai_key():
        return 'openai'
    return 'demo'


def check_ai_availability() -> Tuple[bool, str]:
    """Check if AI API credentials are available.

    Returns:
        Tuple of (is_available, status_message)
    """
    provider = get_ai_provider()
    if provider == 'demo':
        return False, "Demo Mode — no API key configured. Responses use a limited curated knowledge base and are not generative AI."
    model = _configured_model(provider)
    provider_label = 'Google Gemini' if provider == 'google' else 'OpenAI'
    if not _model_is_supported(provider, model):
        return False, f"{provider_label} model configuration is invalid. Check the {provider.upper()}_MODEL setting."
    package = 'google.genai' if provider == 'google' else 'openai'
    try:
        sdk_found = importlib.util.find_spec(package) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        sdk_found = False
    if not sdk_found:
        install = 'google-genai' if provider == 'google' else 'openai'
        return False, f"{provider_label} key detected, but its SDK is missing. Install {install}."
    return True, f"Live AI Mode — {provider_label} · {model}."


# ─── Public API ─────────────────────────────────────────────────────

def get_ai_response(user_message: str,
                    context: Dict[str, Any] = None,
                    chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get a response from the AI assistant.

    Automatically selects full AI mode or demo mode based on credential
    availability.

    Args:
        user_message: User's question
        context: Dict containing current audit context (building profile,
                 appliance data, consumption summary, findings, bills, etc.)
        chat_history: List of previous messages in the conversation

    Returns:
        Dict with 'response', 'mode', and 'error' (if any)
    """
    provider = get_ai_provider()

    if provider == 'google':
        return _get_google_response(user_message, context, chat_history)
    elif provider == 'openai':
        return _get_openai_response(user_message, context, chat_history)
    else:
        return _get_demo_response(user_message, context, chat_history)


def _error_result(provider: str, model: str, exc: Exception) -> Dict[str, Any]:
    """Return safe, actionable API errors without exposing request/credential data."""
    name = 'Google Gemini' if provider == 'google' else 'OpenAI'
    message = str(exc).lower()
    kind = type(exc).__name__.lower()
    if 'auth' in kind or 'unauthorized' in message or '401' in message or 'api key' in message:
        detail = f"{name} authentication failed. Check the configured API key."
    elif 'rate' in kind or '429' in message or 'quota' in message:
        detail = f"{name} rate limit or quota reached. Wait, check billing/limits, then retry."
    elif 'connection' in kind or 'timeout' in kind or 'connect' in message or 'timeout' in message:
        detail = f"Could not connect to {name}. Check the network and retry."
    elif 'badrequest' in kind or 'invalidargument' in kind or '404' in message or '400' in message:
        detail = f"{name} rejected model '{model}' or the request. Verify model access and configuration."
    else:
        detail = f"{name} could not complete the request. Check provider status and retry."
    return {'response': f"I couldn't get a live response. {detail}",
            'mode': f'Live AI unavailable ({name} · {model})', 'error': detail}


def get_suggested_questions() -> List[str]:
    """Return a rich list of suggested questions for the chatbot."""
    return [
        # Energy consumption
        "What are the top energy-consuming appliances in my building?",
        "Show my total energy consumption breakdown",
        # Bills
        "How does my calculated consumption compare to my electricity bills?",
        "What is my estimated monthly electricity cost?",
        # Audit
        "What are the main findings of my energy audit?",
        "Describe the current building's energy profile",
        # Codes
        "Which Indian energy codes apply to my building?",
        "What is Eco Niwas Samhita and does it apply here?",
        # Savings
        "How can I reduce my monthly electricity bill?",
        "Which energy-saving measures should I prioritise?",
        # General
        "How does a residential energy audit work?",
        "Explain the assumptions used in my calculations",
    ]


# ─── Google Gemini API ──────────────────────────────────────────────

def _get_google_response(user_message: str,
                         context: Dict[str, Any] = None,
                         chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get a generative response from the configured Google Gemini API."""
    model_name = _configured_model('google')
    if not _model_is_supported('google', model_name):
        return {'response': 'The configured Google Gemini model name is invalid. Check GOOGLE_MODEL.',
                'mode': 'Configuration error', 'error': 'Unsupported Google Gemini model name.'}
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_get_google_key())
        transcript = []
        for msg in (chat_history or [])[-6:]:
            role = msg.get('role')
            content = str(msg.get('content', ''))[:1200]
            if role in ('user', 'assistant') and content:
                transcript.append(f"{role.title()}: {content}")
        transcript.append(f"User: {user_message}")
        generation_config = {
            'system_instruction': _build_system_prompt(context),
            'max_output_tokens': 700,
        }
        # Gemini 2.5+ and Gemini 3 support low thinking effort. For 3.8 Flash,
        # low is the fastest supported level (minimal is not supported).
        if re.match(r'gemini-(?:2\.5|3\.)', model_name):
            generation_config['thinking_config'] = types.ThinkingConfig(
                thinking_level='low'
            )
        response = client.models.generate_content(
            model=model_name,
            contents="\n\n".join(transcript),
            config=types.GenerateContentConfig(**generation_config),
        )
        answer = getattr(response, 'text', None)
        if not answer:
            raise ValueError('Empty Gemini response')

        return {
            'response': answer,
            'mode': f'AI-Powered (Google Gemini — {model_name})',
            'error': None,
        }

    except Exception as e:
        return _error_result('google', model_name, e)


# ─── OpenAI API ─────────────────────────────────────────────────────

def _get_openai_response(user_message: str,
                         context: Dict[str, Any] = None,
                         chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get a generative response using OpenAI's official Responses API."""
    model_name = _configured_model('openai')
    if not _model_is_supported('openai', model_name):
        return {'response': 'The configured OpenAI model is not supported by this integration. Check OPENAI_MODEL.',
                'mode': 'Configuration error', 'error': 'Unsupported OpenAI Responses API model.'}
    try:
        from openai import OpenAI

        client = OpenAI(api_key=_get_openai_key(), timeout=45.0, max_retries=1)
        conversation = []
        if chat_history:
            for msg in chat_history[-12:]:
                role = msg.get('role')
                content = msg.get('content', '')
                if role in ('user', 'assistant') and content:
                    conversation.append({'role': role, 'content': content})
        conversation.append({'role': 'user', 'content': user_message})

        response = client.responses.create(
            model=model_name,
            instructions=_build_system_prompt(context),
            input=conversation,
            max_output_tokens=1200,
        )
        answer = getattr(response, 'output_text', None)
        if not answer:
            raise ValueError('Empty OpenAI response')

        return {
            'response': answer,
            'mode': f'AI-Powered (OpenAI — {model_name})',
            'error': None,
        }
    except Exception as e:
        return _error_result('openai', model_name, e)


# ─── System Prompt for API Mode ────────────────────────────────────

def _build_system_prompt(context: Dict[str, Any] = None) -> str:
    """Build a comprehensive system prompt with full audit context."""

    base = """You are EcoAudit AI Assistant — an expert on residential building energy efficiency in India, built into the EcoAudit AI academic project for performing "Energy Audit of a Typical Residential Building."

Your role is to answer the user's full range of normal questions, including general knowledge, explanations, programming, Python, data science, academic topics, energy audits, and Indian standards. Generate a fresh, relevant answer to the actual question; do not limit replies to suggested questions or curated FAQ topics. Answer the question directly first. When EcoAudit, the current audit, or residential energy efficiency adds useful context, connect the answer to this system or the supplied building data. Do not force an EcoAudit connection into unrelated questions. Use building context when relevant without restricting questions to the project domain.

## Guidelines
1. Always distinguish between measured data, user-entered values, calculated estimates, and assumptions. Never invent building measurements.
2. Use the Current Building Context below as the source of truth for this building's data. When the user asks about "this building" or "my building," refer to these values.
3. When citing Indian energy codes (Eco Niwas Samhita, ECBC, ECSBC, NBC), note that adoption depends on state government implementation. Do not invent clause numbers, threshold values, or official URLs you cannot verify.
4. Present savings estimates as approximate ranges, not guaranteed outcomes. Do not double-count overlapping recommendations.
5. Use ₹ (Indian Rupees) for costs and kWh for energy. Explain units when the user seems unfamiliar.
6. Recommend a BEE-certified professional energy auditor for detailed assessments, code compliance, and safety inspections.
7. Do not recommend unsafe electrical modifications.
8. If you don't know something, say so honestly. If information is missing from the building data, say what is missing and give a useful general answer.
9. Localize for India: use Indian English conventions, ₹, kWh ("units" on electricity bills), and Indian residential context where relevant. Match the user's language by default; if they write in Hinglish, respond naturally in Hinglish. Honor any response-language preference supplied below.
10. Keep answers clear and well-structured with headings and bullet points when useful. Include relevant figures from the building data when available, and briefly explain how they relate to the answer. For unrelated general questions, answer naturally without adding irrelevant audit commentary.
11. For code-related questions, always include: the code's full name, issuing authority, purpose, whether it applies to this building type, and the official source link when verified.
12. Treat profile and appliance fields as user-entered; treat bill readings as user-provided bill data (not independently verified); treat consumption and costs calculated by the app as estimates; label assumptions and suggestions. Only call values measured if the context explicitly identifies them as measured.
13. If the building uses sample/demo data, mention that the values are illustrative.
14. For exact Indian code clauses, current standards, legal compliance, or technical limits, only cite the verified references supplied below; otherwise say verification is needed from the official issuer. Never guarantee compliance or savings."""

    if context and context.get('response_language'):
        language = context['response_language']
        if language == 'Auto (match my message)':
            language = "match the language and style of the user's message"
        base += f"\n\n## Response Language Preference\nRespond in: {language}. Keep technical terms clear and familiar to Indian users."

    if not context:
        base += "\n\n**No building data has been entered yet.** Answer general questions about energy audits, Indian codes, and residential energy efficiency. When the user asks about their specific building, let them know they need to enter building data first."
        return base

    if context.get('is_sample_data'):
        base += "\n\nThe currently loaded building and appliance data is illustrative sample data, not measured site data. State this when discussing its results."

    parts = [base, "\n\n## Current Building Context"]

    # Building profile
    bp = context.get('building_profile', {})
    if bp:
        parts.append("\n### Building Profile")
        parts.append(f"- Name: {bp.get('name', 'Not specified')}")
        parts.append(f"- Type: {bp.get('building_type', 'Not specified')}")
        city = bp.get('city', '')
        state = bp.get('state', '')
        if city or state:
            parts.append(f"- Location: {city}, {state}" if city and state else f"- Location: {city or state}")
        cz = bp.get('climate_zone', '')
        if cz:
            parts.append(f"- Climate Zone: {cz}")
        area = bp.get('built_up_area')
        if area:
            parts.append(f"- Built-up Area: {area} sq.m")
        occ = bp.get('num_occupants')
        if occ:
            parts.append(f"- Occupants: {occ}")
        age = bp.get('building_age')
        if age:
            parts.append(f"- Building Age: {age} years")
        parts.append(f"- AC Available: {'Yes' if bp.get('ac_availability') else 'No'}")
        parts.append(f"- Solar Installation: {'Yes' if bp.get('solar_installation') else 'No'}")
        wall = bp.get('wall_construction', '')
        if wall:
            parts.append(f"- Wall Construction: {wall}")
        roof = bp.get('roof_type', '')
        if roof:
            parts.append(f"- Roof Type: {roof}")
        ri = bp.get('roof_insulation', '')
        if ri:
            parts.append(f"- Roof Insulation: {ri}")
        vent = bp.get('natural_ventilation', '')
        if vent:
            parts.append(f"- Natural Ventilation: {vent}")
        lt = bp.get('lighting_type', '')
        if lt:
            parts.append(f"- Lighting Type: {lt}")
        wa = bp.get('window_area')
        if wa:
            parts.append(f"- Window Area: {wa} sq.m")
        wo = bp.get('window_orientation', '')
        if wo:
            parts.append(f"- Window Orientation: {wo}")
        tariff = bp.get('tariff')
        if tariff:
            parts.append(f"- Electricity Tariff: ₹{tariff}/kWh")

    # Consumption summary
    cs = context.get('consumption_summary', {})
    if cs and cs.get('total_monthly_kwh', 0) > 0:
        parts.append("\n### Estimated Consumption Summary (from appliance inventory)")
        parts.append(f"- Daily: {cs.get('total_daily_kwh', 0):.1f} kWh")
        parts.append(f"- Monthly: {cs.get('total_monthly_kwh', 0):.1f} kWh")
        parts.append(f"- Annual: {cs.get('total_annual_kwh', 0):.1f} kWh")
        parts.append(f"- Monthly Cost: ₹{cs.get('monthly_cost_inr', 0):,.0f}")
        parts.append(f"- Annual Cost: ₹{cs.get('annual_cost_inr', 0):,.0f}")
        parts.append(f"- Tariff Used: ₹{cs.get('tariff_used', 0)}/kWh")

    # Top consumers
    tc = context.get('top_consumers', [])
    if tc:
        parts.append("\n### Top Energy-Consuming Appliances")
        for i, c in enumerate(tc[:5], 1):
            parts.append(f"{i}. {c['name']}: {c['monthly_kwh']} kWh/month ({c['percentage']}%)")

    # All appliances (condensed)
    apps = context.get('all_appliances', [])
    if apps:
        parts.append(f"\n### Full Appliance Inventory ({len(apps)} items)")
        for a in apps[:12]:
            src = f" [{a.get('power_source', 'Assumed')}]" if a.get('power_source') != 'Assumed' else ''
            parts.append(
                f"- {a['name']}: {a['quantity']}×{a['power_watts']}W, "
                f"{a['hours_per_day']}h/day, {a['days_per_month']}d/mo → "
                f"{a['monthly_kwh']} kWh/mo ({a['percentage']}%){src}"
            )

    # Bill analysis
    ba = context.get('bill_analysis', {})
    if ba and ba.get('average_monthly_kwh'):
        parts.append("\n### Electricity Bill Data")
        parts.append(f"- Average Monthly Billed: {ba['average_monthly_kwh']:.0f} kWh")
        parts.append(f"- Highest: {ba.get('highest_month', '?')} ({ba.get('highest_consumption_kwh', 0):.0f} kWh)")
        parts.append(f"- Lowest: {ba.get('lowest_month', '?')} ({ba.get('lowest_consumption_kwh', 0):.0f} kWh)")
        parts.append(f"- Months Available: {ba.get('months_available', 0)}")

    # Bill comparison
    bc = context.get('bill_comparison', {})
    if bc and bc.get('billed_monthly_kwh', 0) > 0:
        parts.append("\n### Calculated vs Billed Comparison")
        parts.append(f"- Calculated (appliances): {bc['calculated_monthly_kwh']:.1f} kWh/month")
        parts.append(f"- Billed (average): {bc['billed_monthly_kwh']:.1f} kWh/month")
        parts.append(f"- Difference: {bc['absolute_difference_kwh']:.1f} kWh ({bc['percentage_difference']:.1f}%)")
        if bc.get('possible_reasons'):
            parts.append("- Possible reasons: " + "; ".join(bc['possible_reasons'][:3]))

    # Findings
    fs = context.get('findings_summary', '')
    if fs:
        parts.append("\n### Key Audit Findings")
        parts.append(fs)

    # Envelope assessment (condensed)
    ea = context.get('envelope_assessment', [])
    if ea:
        parts.append("\n### Building Envelope Observations")
        for obs in ea:
            aspect = obs.get('aspect', '')
            if '⚠️' not in aspect:
                parts.append(f"- {aspect}: {obs.get('observation', '')}")

    # Interventions (condensed)
    iv = context.get('interventions', [])
    if iv:
        parts.append("\n### Potential Energy-Saving Interventions")
        for intv in iv:
            parts.append(
                f"- {intv['name']}: baseline {intv['baseline_monthly_kwh']:.1f} kWh/mo, "
                f"est. {intv['default_reduction']*100:.0f}% reduction"
            )

    references = context.get('verified_code_references', [])
    if references:
        parts.append("\n### Existing Code References (verify current applicability with issuing authority)")
        for ref in references[:4]:
            parts.append(
                f"- {ref.get('name', 'Reference')}; edition/year: {ref.get('edition', 'not specified')}; "
                f"issuing authority: {ref.get('issuing_authority', 'not specified')}; "
                f"official source: {ref.get('official_source', 'not supplied')}; "
                f"verification note: {ref.get('verification_note', 'Verify current edition and applicability.') }"
            )

    return "\n".join(parts)


# ─── Demo Mode ──────────────────────────────────────────────────────

def _get_demo_response(user_message: str,
                       context: Dict[str, Any] = None,
                       chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Provide building-aware deterministic responses from curated knowledge.

    This is NOT a generative AI model. It matches user questions to
    categories and builds responses using actual building data when
    available.
    """
    msg = user_message.lower().strip()

    # Product questions do not require any profile or appliance information.
    if any(phrase in msg for phrase in (
        'what is ecoaudit', 'what does ecoaudit', 'what is eco audit',
        'what does eco audit', 'purpose of ecoaudit', 'purpose of eco audit',
        'what is this app', 'what does this app do', 'what is this system',
    )):
        return {
            'response': _match_knowledge_base(msg, context),
            'mode': 'Demo Mode (Product Information)',
            'error': None,
        }

    # Try context-aware responses first
    if context:
        ctx_response = _context_aware_response(msg, context)
        if ctx_response:
            return {
                'response': ctx_response,
                'mode': 'Demo Mode (Building-Aware Knowledge Base)',
                'error': None,
            }

    # Try conversation-history-aware follow-ups
    if chat_history:
        followup = _followup_response(msg, chat_history, context)
        if followup:
            return {
                'response': followup,
                'mode': 'Demo Mode (Building-Aware Knowledge Base)',
                'error': None,
            }

    # Match against knowledge base
    best = _match_knowledge_base(msg, context)

    return {
        'response': best,
        'mode': 'Demo Mode (Building-Aware Knowledge Base)',
        'error': None,
    }


# ─── Hinglish Detection ────────────────────────────────────────────

_HINGLISH_WORDS = {
    'bijli', 'batti', 'pankha', 'bachat', 'ghar', 'paisa', 'paise',
    'kitna', 'kaise', 'kya', 'kab', 'kahan', 'kyun', 'kaun',
    'mera', 'mere', 'meri', 'hamara', 'hamare',
    'zyada', 'jyada', 'kam', 'bahut', 'thoda',
    'nahi', 'nahin', 'haan', 'acha', 'achha',
    'kharcha', 'kharche', 'mahina', 'saal',
    'urja', 'vidyut', 'sudhaar', 'suraksha',
    'chappar', 'diwar', 'khidki',
    'batao', 'bataye', 'bataiye', 'samjhao',
    'chalana', 'band', 'chalu',
    'ac', 'fridge',
}


def _is_hinglish(msg: str) -> bool:
    """Detect if a message contains Hinglish words."""
    words = set(re.findall(r'[a-z]+', msg.lower()))
    return len(words & _HINGLISH_WORDS) >= 2


# ─── Context-Aware Response Builder ────────────────────────────────

def _context_aware_response(msg: str, context: Dict[str, Any]) -> Optional[str]:
    """Build context-aware responses using actual building data."""

    hinglish = _is_hinglish(msg)

    # ── Top consumers / highest consuming ──
    if _matches(msg, ['top', 'highest', 'most', 'sabse', 'zyada', 'jyada'],
                ['consum', 'use', 'energy', 'electric', 'bijli', 'appliance', 'wala']):
        tc = context.get('top_consumers', [])
        if tc:
            lines = ["Based on your current appliance inventory, the **highest-consuming appliances** are:\n"]
            if hinglish:
                lines = ["Aapke appliance inventory ke hisaab se, **sabse zyada bijli khaane waale appliances** hain:\n"]
            for i, c in enumerate(tc, 1):
                lines.append(f"{i}. **{c['name']}** — {c['monthly_kwh']} kWh/month ({c['percentage']}% of total)")
            cs = context.get('consumption_summary', {})
            if cs:
                lines.append(f"\n**Total estimated monthly consumption: {cs.get('total_monthly_kwh', 0):.1f} kWh**")
            lines.append("\n*Note: These estimates are based on rated power and assumed usage hours. "
                        "Actual consumption may differ due to duty cycles, thermostat behaviour, and operating conditions.*")
            return "\n".join(lines)
        return _no_data_response("appliance inventory", "top energy consumers", hinglish)

    # ── Total consumption / breakdown / show consumption ──
    if _matches(msg, ['total', 'overall', 'kul', 'pura'],
                ['consum', 'use', 'energy', 'bijli', 'breakdown', 'summary']):
        cs = context.get('consumption_summary', {})
        if cs and cs.get('total_monthly_kwh', 0) > 0:
            lines = ["### 📊 Energy Consumption Summary\n"]
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Estimated Daily Consumption | {cs['total_daily_kwh']:.1f} kWh |")
            lines.append(f"| Estimated Monthly Consumption | {cs['total_monthly_kwh']:.1f} kWh |")
            lines.append(f"| Estimated Annual Consumption | {cs['total_annual_kwh']:.1f} kWh |")
            lines.append(f"| Estimated Monthly Cost | ₹{cs['monthly_cost_inr']:,.0f} |")
            lines.append(f"| Estimated Annual Cost | ₹{cs['annual_cost_inr']:,.0f} |")
            lines.append(f"| Tariff Used | ₹{cs['tariff_used']}/kWh |")
            apps = context.get('all_appliances', [])
            if apps:
                lines.append(f"\nThis is based on **{len(apps)} appliances** in your inventory.")
            lines.append("\n*Estimates use rated power × usage hours. Actual consumption may vary.*")
            return "\n".join(lines)
        return _no_data_response("appliance inventory", "consumption summary", hinglish)

    # ── Monthly cost / bill amount / expense / spending ──
    if _matches(msg, ['cost', 'expense', 'spend', 'kharcha', 'kharche', 'paisa', 'paise', 'kitna'],
                ['month', 'bill', 'electric', 'bijli', 'mahina', 'rupee', 'rupay']):
        cs = context.get('consumption_summary', {})
        if cs and cs.get('monthly_cost_inr', 0) > 0:
            lines = [f"Based on your appliance inventory and the tariff of ₹{cs['tariff_used']}/kWh:\n"]
            if hinglish:
                lines = [f"Aapke appliance inventory aur ₹{cs['tariff_used']}/kWh tariff ke hisaab se:\n"]
            lines.append(f"- **Estimated Monthly Consumption:** {cs['total_monthly_kwh']:.1f} kWh")
            lines.append(f"- **Estimated Monthly Cost:** ₹{cs['monthly_cost_inr']:,.0f}")
            lines.append(f"- **Estimated Annual Consumption:** {cs['total_annual_kwh']:.1f} kWh")
            lines.append(f"- **Estimated Annual Cost:** ₹{cs['annual_cost_inr']:,.0f}")
            lines.append("\n*These are estimates based on rated power and assumed usage patterns. "
                        "Actual billed amounts may differ due to tariff slabs, taxes, fixed charges, and actual usage variations.*")
            return "\n".join(lines)
        return _no_data_response("appliance inventory", "cost estimate", hinglish)

    # ── Bill comparison / calculated vs billed / discrepancy ──
    if _matches(msg, ['compar', 'difference', 'discrep', 'match', 'tally', 'fark'],
                ['bill', 'calculat', 'estimat', 'actual', 'billed', 'bijli']):
        bc = context.get('bill_comparison', {})
        if bc and bc.get('billed_monthly_kwh', 0) > 0:
            calc = bc['calculated_monthly_kwh']
            billed = bc['billed_monthly_kwh']
            diff = bc['absolute_difference_kwh']
            pct = bc['percentage_difference']
            direction = "higher" if bc.get('calculated_higher') else "lower"
            lines = ["### 🔄 Calculated vs. Billed Consumption\n"]
            lines.append(f"| Source | Monthly kWh |")
            lines.append(f"|--------|------------|")
            lines.append(f"| Calculated (appliance estimates) | {calc:.1f} kWh |")
            lines.append(f"| Billed (average from entered bills) | {billed:.1f} kWh |")
            lines.append(f"| Difference | {diff:.1f} kWh ({pct:.1f}%) |")
            lines.append(f"\nThe calculated estimate is **{direction}** than the billed average.")
            reasons = bc.get('possible_reasons', [])
            if reasons:
                lines.append("\n**Possible reasons for the discrepancy:**")
                for r in reasons:
                    lines.append(f"- {r}")
            lines.append("\n*Neither value is necessarily more accurate. Bills include all loads; "
                        "estimates depend on assumed usage.*")
            return "\n".join(lines)
        # Check if we have bills at all
        ba = context.get('bill_analysis', {})
        if not ba:
            return ("No monthly electricity bills have been entered yet. Please add your monthly "
                    "bill data in the **Energy Consumption Analysis** section to see a comparison "
                    "between calculated and billed consumption.\n\n"
                    "In general, differences arise from: missing appliances in the inventory, "
                    "duty cycles reducing actual draw below rated power, shared meters, "
                    "standby consumption, and seasonal variations.")
        cs = context.get('consumption_summary', {})
        if not cs or cs.get('total_monthly_kwh', 0) <= 0:
            return _no_data_response("appliance inventory", "bill comparison", hinglish)

    # ── Audit findings / results / observations ──
    if _matches(msg, ['finding', 'audit', 'result', 'observ', 'assessment', 'jaanch'],
                ['main', 'key', 'summary', 'show', 'what', 'kya', 'batao']):
        fs = context.get('findings_summary', '')
        fd = context.get('findings_detail', {})
        if fs or fd:
            lines = ["### 🔍 Energy Audit Findings\n"]
            ds = fd.get('data_supported', []) if fd else []
            ab = fd.get('assumption_based', []) if fd else []
            ri = fd.get('requires_inspection', []) if fd else []
            if ds:
                lines.append("**Findings supported by your data:**")
                for f in ds:
                    lines.append(f"- {f.get('icon', '📋')} **{f.get('category', '')}:** {f.get('finding', '')}")
            if ab:
                lines.append("\n**Findings based on general assumptions:**")
                for f in ab:
                    lines.append(f"- {f.get('icon', '📋')} **{f.get('category', '')}:** {f.get('finding', '')}")
            if ri:
                lines.append("\n**Findings requiring professional inspection:**")
                for f in ri:
                    lines.append(f"- {f.get('icon', '📋')} **{f.get('category', '')}:** {f.get('finding', '')}")
            if not ds and not ab and not ri and fs:
                lines.append(fs)
            lines.append("\n*For a comprehensive professional energy audit, consult a BEE-certified energy auditor.*")
            return "\n".join(lines)
        return _no_data_response("building and appliance data", "audit findings", hinglish)

    # ── Building profile / describe building ──
    if _matches(msg, ['building', 'profile', 'describe', 'ghar', 'makan', 'flat'],
                ['current', 'my', 'this', 'detail', 'info', 'mera', 'about', 'describe']):
        bp = context.get('building_profile', {})
        if bp:
            lines = ["### 🏠 Current Building Profile\n"]
            lines.append(f"| Property | Value |")
            lines.append(f"|----------|-------|")
            for label, key in [
                ("Name", "name"), ("Type", "building_type"),
                ("City", "city"), ("State", "state"),
                ("Climate Zone", "climate_zone"),
                ("Built-up Area", "built_up_area"),
                ("Occupants", "num_occupants"),
                ("Building Age", "building_age"),
                ("Roof Type", "roof_type"),
                ("Wall Construction", "wall_construction"),
                ("Lighting Type", "lighting_type"),
                ("Natural Ventilation", "natural_ventilation"),
            ]:
                val = bp.get(key)
                if val:
                    unit = " sq.m" if key == 'built_up_area' else (" years" if key == 'building_age' else '')
                    lines.append(f"| {label} | {val}{unit} |")
            lines.append(f"| AC Available | {'Yes' if bp.get('ac_availability') else 'No'} |")
            lines.append(f"| Solar Installation | {'Yes' if bp.get('solar_installation') else 'No'} |")
            tariff = bp.get('tariff')
            if tariff:
                lines.append(f"| Electricity Tariff | ₹{tariff}/kWh |")
            cs = context.get('consumption_summary', {})
            if cs and cs.get('total_monthly_kwh', 0) > 0:
                lines.append(f"\n**Estimated monthly consumption:** {cs['total_monthly_kwh']:.1f} kWh "
                            f"(₹{cs['monthly_cost_inr']:,.0f}/month)")
            return "\n".join(lines)
        return _no_data_response("building profile", "building description", hinglish)

    # ── Appliance list ──
    if _matches(msg, ['appliance', 'list', 'inventory', 'saman', 'upkaran'],
                ['all', 'show', 'list', 'what', 'which', 'kon', 'kaun', 'sabhi']):
        apps = context.get('all_appliances', [])
        if apps:
            lines = [f"### 🔌 Appliance Inventory ({len(apps)} items)\n"]
            lines.append("| # | Appliance | Qty | Power (W) | Hrs/Day | Monthly kWh | % Share |")
            lines.append("|---|-----------|-----|-----------|---------|-------------|---------|")
            for i, a in enumerate(apps, 1):
                lines.append(f"| {i} | {a['name']} | {a['quantity']} | {a['power_watts']} | "
                            f"{a['hours_per_day']} | {a['monthly_kwh']} | {a['percentage']}% |")
            cs = context.get('consumption_summary', {})
            if cs:
                lines.append(f"\n**Total: {cs.get('total_monthly_kwh', 0):.1f} kWh/month**")
            return "\n".join(lines)
        return _no_data_response("appliance inventory", "appliance list", hinglish)

    # ── Envelope / insulation / roof / walls ──
    if _matches(msg, ['envelope', 'insulat', 'roof', 'wall', 'window', 'glazing',
                      'shading', 'wwr', 'chappar', 'diwar', 'khidki'],
                ['build', 'assess', 'current', 'my', 'thermal', 'heat', 'improve']):
        ea = context.get('envelope_assessment', [])
        if ea:
            lines = ["### 🏗️ Building Envelope Assessment\n"]
            for obs in ea:
                aspect = obs.get('aspect', '')
                if '⚠️' in aspect:
                    continue
                lines.append(f"**{aspect}**")
                lines.append(f"- Observation: {obs.get('observation', '')}")
                lines.append(f"- Confidence: {obs.get('confidence', 'N/A')}")
                lines.append(f"- Recommendation: {obs.get('recommendation', '')}\n")
            lines.append("*This is a preliminary qualitative screening, not a professional thermal audit.*")
            return "\n".join(lines)
        return _no_data_response("building profile", "envelope assessment", hinglish)

    # ── Savings / interventions / reduce bill ──
    if _matches(msg, ['save', 'saving', 'reduce', 'lower', 'cut', 'decrease', 'bachat', 'kam'],
                ['bill', 'energy', 'electric', 'consum', 'cost', 'bijli', 'kharcha', 'tip']):
        iv = context.get('interventions', [])
        if iv:
            tariff = context.get('consumption_summary', {}).get('tariff_used', 7.0)
            lines = ["### 💡 Potential Energy-Saving Measures\n"]
            for i, intv in enumerate(iv, 1):
                est_save = intv['baseline_monthly_kwh'] * intv['default_reduction']
                lines.append(f"**{i}. {intv['name']}**")
                lines.append(f"   - Category: {intv['category']}")
                lines.append(f"   - Baseline: {intv['baseline_monthly_kwh']:.1f} kWh/month")
                lines.append(f"   - Estimated reduction: {intv['default_reduction']*100:.0f}%")
                lines.append(f"   - Estimated monthly savings: {est_save:.1f} kWh (≈ ₹{est_save*tariff:,.0f})")
                lines.append(f"   - Confidence: {intv.get('confidence', 'Estimate')}\n")
            lines.append("⚠️ *These are estimated savings based on assumed reduction percentages. "
                        "Actual savings depend on specific conditions. Some savings may overlap; "
                        "do not simply add them together.*")
            return "\n".join(lines)
        # Generic tips if no data
        return _knowledge_base_entry('savings')

    # ── Prioritise measures ──
    if _matches(msg, ['priorit', 'first', 'which', 'start', 'order', 'pehle', 'shuru'],
                ['measure', 'save', 'improv', 'step', 'recommend', 'kare', 'energy']):
        return _knowledge_base_entry('prioritize')

    # ── Climate zone ──
    if _matches(msg, ['climate', 'zone', 'jalvayu'],
                ['which', 'my', 'what', 'build', 'india', 'kya', 'kaun']):
        bp = context.get('building_profile', {})
        cz = bp.get('climate_zone', '')
        city = bp.get('city', '')
        if cz:
            response = f"Your building is in the **{cz}** climate zone"
            if city:
                response += f" (city: {city})"
            response += ".\n\n"
            response += _get_climate_info(cz)
            return response
        return _knowledge_base_entry('climate_zones')

    # ── Methodology / how calculated / assumptions ──
    if _matches(msg, ['method', 'formula', 'calculat', 'how', 'assumption', 'kaise'],
                ['work', 'done', 'calculat', 'energy', 'use', 'hota', 'formula']):
        return _knowledge_base_entry('methodology')

    # ── Indian codes (general) ──
    if _matches(msg, ['code', 'standard', 'regulation', 'niyam', 'manak'],
                ['india', 'apply', 'which', 'build', 'energy', 'relevant', 'kya', 'kaun']):
        return _code_response_for_building(context, 'general')

    # ── Eco Niwas Samhita ──
    if _matches(msg, ['eco niwas', 'niwas samhita', 'ens', 'eco-niwas'],
                []):
        return _code_response_for_building(context, 'ens')

    # ── ECBC / ECSBC ──
    if _matches(msg, ['ecbc', 'ecsbc', 'commercial code', 'energy conservation building'],
                []):
        return _code_response_for_building(context, 'ecbc')

    # ── BEE star labels ──
    if _matches(msg, ['bee', 'star', 'label', 'rating', 'star rating'],
                ['applia', 'effici', 'buy', 'kharid', 'best']):
        return _knowledge_base_entry('bee_star')

    # ── NBC ──
    if _matches(msg, ['national building code', 'nbc', 'bis'],
                []):
        return _code_response_for_building(context, 'nbc')

    # ── Solar ──
    if _matches(msg, ['solar', 'rooftop', 'photovoltaic', 'pv', 'renewable', 'saur'],
                []):
        return _knowledge_base_entry('solar')

    # ── AC / cooling ──
    if _matches(msg, ['ac', 'air condition', 'cool', 'thanda'],
                ['tip', 'save', 'effici', 'use', 'set', 'best', 'reduce', 'improve']):
        return _knowledge_base_entry('ac_cooling')

    # ── Lighting ──
    if _matches(msg, ['light', 'led', 'cfl', 'bulb', 'lamp', 'tube', 'batti'],
                []):
        return _knowledge_base_entry('lighting')

    # ── Water heating / geyser ──
    if _matches(msg, ['geyser', 'water heat', 'hot water', 'garam pani'],
                []):
        return _knowledge_base_entry('water_heating')

    # ── Ventilation ──
    if _matches(msg, ['ventilat', 'air flow', 'cross ventil', 'hawa'],
                []):
        return _knowledge_base_entry('ventilation')

    # ── Units explanation ──
    if _matches(msg, ['unit', 'kwh', 'watt', 'kw', 'what is kwh', 'what is unit'],
                []):
        return _knowledge_base_entry('units')

    # ── Report ──
    if _matches(msg, ['report', 'pdf', 'download', 'generate'],
                []):
        return _knowledge_base_entry('report')

    # ── Payback ──
    if _matches(msg, ['payback', 'roi', 'return on investment', 'cost benefit'],
                []):
        return _knowledge_base_entry('payback')

    # ── How does energy audit work ──
    if _matches(msg, ['energy audit', 'audit process', 'how', 'what is'],
                ['work', 'audit', 'mean', 'process', 'step', 'kaise']):
        return _knowledge_base_entry('audit_process')

    # ── Greetings ──
    if _matches(msg, ['hello', 'hi', 'hey', 'namaste', 'namaskar', 'help', 'madad'],
                []):
        bp = context.get('building_profile', {})
        name = bp.get('name', '')
        greeting = "Hello! 👋 I'm the EcoAudit AI Assistant."
        if hinglish:
            greeting = "Namaste! 👋 Main EcoAudit AI Assistant hoon."
        if name:
            greeting += f" I can see you're working on **{name}**."
        greeting += ("\n\nI can help you with:\n"
                    "- 📊 Understanding your energy consumption\n"
                    "- 💡 Energy-saving recommendations\n"
                    "- 📜 Indian energy codes and standards\n"
                    "- 🔍 Interpreting audit findings\n"
                    "- 📋 Bill vs. calculated comparison\n"
                    "- 🏗️ Building envelope observations\n\n"
                    "Ask me anything, or try one of the suggested questions above!")
        return greeting

    return None


# ─── Follow-up Response Handler ─────────────────────────────────────

def _followup_response(msg: str, chat_history: List[Dict[str, str]],
                       context: Dict[str, Any] = None) -> Optional[str]:
    """Handle follow-up questions using conversation context."""
    followup_words = ['why', 'explain', 'how', 'what', 'more', 'detail',
                      'mean', 'example', 'kyun', 'kaise', 'kya', 'samjhao',
                      'this', 'that', 'it', 'these', 'those',
                      'what if', 'change', 'instead']

    is_followup = any(w in msg for w in followup_words) and len(msg.split()) < 15

    if not is_followup:
        return None

    # Get the last assistant message for context
    last_assistant = None
    for m in reversed(chat_history):
        if m.get('role') == 'assistant':
            last_assistant = m.get('content', '')
            break

    if not last_assistant:
        return None

    # Simple follow-up handling for demo mode
    if any(w in msg for w in ['why', 'kyun', 'reason', 'kaise']):
        if 'consumer' in last_assistant.lower() or 'consuming' in last_assistant.lower():
            return ("The appliances that consume the most energy typically have either:\n"
                    "- **High rated power** (e.g., ACs at 1500W, geysers at 2000W)\n"
                    "- **Long operating hours** (e.g., refrigerators at 24h/day, fans at 10h/day)\n"
                    "- **Both** (e.g., an AC running 8+ hours/day)\n\n"
                    "Energy consumption = Power × Time. So even a low-power device like a "
                    "refrigerator (150W) can be a significant consumer because it runs 24/7.\n\n"
                    "*Check the appliance inventory table for the specific power ratings and "
                    "usage hours contributing to each appliance's consumption.*")
        if 'bill' in last_assistant.lower() or 'discrep' in last_assistant.lower():
            return ("Common reasons for discrepancies between calculated and billed consumption:\n\n"
                    "**If calculated > billed:**\n"
                    "- Rated power overestimates actual draw (duty cycles, inverter technology)\n"
                    "- Actual usage hours are lower than estimated\n"
                    "- Some appliances aren't used every day\n\n"
                    "**If billed > calculated:**\n"
                    "- Some appliances may be missing from the inventory\n"
                    "- Standby power isn't fully accounted for\n"
                    "- Common-area loads may be included in the bill\n"
                    "- Seasonal usage variations\n\n"
                    "*The calculated estimate uses rated power × assumed hours, while bills "
                    "measure actual energy drawn through the meter.*")

    if any(w in msg for w in ['more', 'detail', 'explain', 'samjhao', 'batao']):
        return ("I'd be happy to explain further! In demo mode, my ability to handle "
                "complex follow-up questions is limited.\n\n"
                "**You can:**\n"
                "- Ask a more specific question (e.g., \"How much does the AC consume?\")\n"
                "- Navigate to the relevant page for detailed charts and data\n"
                "- Try one of the suggested questions above\n\n"
                "*For fully conversational follow-up support, configure an AI API key "
                "(Google Gemini or OpenAI) in the `.env` file.*")

    return None


# ─── Keyword Matching Helpers ───────────────────────────────────────

def _matches(msg: str, primary_keywords: List[str],
             secondary_keywords: List[str]) -> bool:
    """Check if message matches a category using fuzzy keyword scoring.

    Returns True if at least one primary keyword matches AND
    (no secondary keywords required OR at least one secondary matches).
    """
    msg_lower = msg.lower()

    primary_hit = any(_fuzzy_in(kw, msg_lower) for kw in primary_keywords)
    if not primary_hit:
        return False

    if not secondary_keywords:
        return True

    return any(_fuzzy_in(kw, msg_lower) for kw in secondary_keywords)


def _fuzzy_in(keyword: str, text: str) -> bool:
    """Check if keyword appears in text, with basic fuzzy matching."""
    if keyword in text:
        return True
    # Handle common misspellings by checking partial matches
    if len(keyword) >= 4:
        # Check if most of the keyword characters appear in sequence
        return keyword[:len(keyword)-1] in text
    return False


def _no_data_response(missing_data: str, topic: str, hinglish: bool = False) -> str:
    """Generate a response when required data is not available."""
    if hinglish:
        return (f"Abhi {missing_data} enter nahi kiya gaya hai, isliye {topic} "
                f"ke baare mein specific jaankari dena mushkil hai.\n\n"
                f"Kripya pehle apna data enter karein ya sidebar mein "
                f"**📥 Load Sample Building** button dabayein.\n\n"
                f"Tab tak, main general energy audit ke sawaalon ka jawab de sakta hoon!")
    return (f"No {missing_data} has been entered yet, so I can't provide specific "
            f"information about {topic}.\n\n"
            f"Please enter your data in the relevant section, or click "
            f"**📥 Load Sample Building** in the sidebar to try with demo data.\n\n"
            f"In the meantime, I can answer general questions about energy audits, "
            f"Indian energy codes, and energy-saving tips!")


# ─── Code Reference Responses ──────────────────────────────────────

def _code_response_for_building(context: Dict[str, Any], code_type: str) -> str:
    """Build a code-reference response contextualised to the current building."""
    bp = context.get('building_profile', {}) if context else {}
    building_type = bp.get('building_type', 'residential building')
    city = bp.get('city', '')
    state = bp.get('state', '')
    climate_zone = bp.get('climate_zone', '')
    location = f"{city}, {state}" if city and state else (city or state or 'India')

    if code_type == 'ens':
        response = f"""### 📜 Eco Niwas Samhita (ENS) — Residential Energy Code

**Full Name:** Eco Niwas Samhita (Energy Conservation Building Code for Residential Buildings)
**Issuing Authority:** Bureau of Energy Efficiency (BEE), Ministry of Power, Government of India

**Part I (2018) — Building Envelope:**
- Covers thermal performance of walls, roofs, windows, and doors
- Introduces the Residential Envelope Transmittance Value (RETV)
- Applies to five climate zones of India

**Part II (2021) — Electro-Mechanical & Renewable Energy Systems:**
- Covers lighting, air conditioning, and solar energy systems
- Sets efficiency requirements for building services

**Applicability to your building ({building_type} in {location}):**
- ENS is the **primary energy code for residential buildings** in India
- It may apply to your {building_type.lower()}, subject to state-level adoption"""
        if climate_zone:
            response += f"\n- Your climate zone ({climate_zone}) is one of the five zones addressed by ENS"
        response += f"""
- **Important:** Adoption is by state governments — it may be mandatory in some states and voluntary in others
- Check with your local building authority for the current adoption status in {state if state else 'your state'}

**Official Source:** https://beeindia.gov.in/en/programmes/eco-niwas-samhita

⚠️ *This is an educational summary. Specific clause numbers, threshold values, and mandatory status should be verified from the official BEE publication and your state building bylaws.*"""
        return response

    if code_type == 'ecbc':
        return f"""### 📜 ECBC and ECSBC — Commercial Building Energy Codes

**ECBC 2017** (Energy Conservation Building Code):
- **Primarily for commercial buildings** with connected load ≥100 kW or contract demand ≥120 kVA
- Three compliance tiers: ECBC (minimum), ECBC+, SuperECBC
- Covers envelope, HVAC, lighting, electrical systems
- **NOT directly applicable to individual residences** like your {building_type.lower()}

**ECSBC 2023** (Energy Conservation and Sustainable Building Code):
- Updated code superseding ECBC 2017
- Adds sustainability provisions (water, materials, waste)
- May include provisions for larger residential complexes
- Verify specific residential applicability from the official document

**For your {building_type} in {location}:**
- **Eco Niwas Samhita (ENS)** is the relevant residential code, not ECBC/ECSBC
- ECBC/ECSBC may apply only if your building is part of a large mixed-use development with commercial loads meeting the threshold

**Official Source:** https://beeindia.gov.in/en/programmes/energy-conservation-building-codes

⚠️ *Do not apply ECBC commercial thresholds to private residences. Consult the official BEE publications for accurate applicability criteria.*"""

    if code_type == 'nbc':
        return f"""### 📜 National Building Code of India (NBC)

**Full Name:** National Building Code of India (SP 7:2016)
**Issuing Authority:** Bureau of Indian Standards (BIS)
**Edition:** 2016

**Subject:** Comprehensive building code covering planning, design, construction, and maintenance of all types of buildings.

**Energy-relevant sections:**
- **Part 8:** Building Services (electrical installations, plumbing, air conditioning)
- **Part 11:** Approach to Sustainability (energy, water, materials, waste, indoor environment)

**Applicability to your {building_type} in {location}:**
- NBC is a national reference standard applicable to all buildings including residences
- However, specific energy-performance requirements for residences are more directly covered by **Eco Niwas Samhita**
- NBC provides the broader framework for building planning, safety, and services
- Mandatory enforcement depends on local building authority adoption

**Official Source:** https://www.bis.gov.in/

⚠️ *NBC is a comprehensive multi-part standard. Verify specific clause references from the official BIS publication. Energy-specific residential provisions are better referenced through ENS.*"""

    # General: which codes apply
    response = f"""### 📜 Indian Energy Codes Applicable to Your Building

For a **{building_type}** in **{location}**"""
    if climate_zone:
        response += f" ({climate_zone} climate zone)"
    response += """, the following codes and standards may be relevant:

**1. Eco Niwas Samhita (ENS)** — ⭐ Most directly applicable
- BEE's residential building energy code
- Part I (2018): Building envelope
- Part II (2021): Electro-mechanical systems
- Adoption depends on state government implementation
- 🔗 https://beeindia.gov.in/en/programmes/eco-niwas-samhita

**2. BEE Standards & Labelling Programme** — Directly applicable
- Star ratings for ACs, refrigerators, fans, geysers, LED lamps, etc.
- Mandatory labelling for some appliances, voluntary for others
- 🔗 https://beestarlabel.com/

**3. National Building Code (NBC 2016)** — General framework
- Part 11 covers sustainability including energy provisions
- Broad applicability but not residential-energy-specific
- 🔗 https://www.bis.gov.in/

**4. ECBC 2017 / ECSBC 2023** — Primarily for commercial buildings
- NOT directly applicable to individual residences
- May apply to large mixed-use complexes
- 🔗 https://beeindia.gov.in/en/programmes/energy-conservation-building-codes

**5. Indian Electricity Rules and Safety Standards**
- Relevant only for electrical safety, not energy efficiency
- 🔗 https://cea.nic.in/

"""
    if state:
        response += f"\n**Note:** Check whether {state} has adopted ENS or equivalent state-level energy provisions. Not all states have mandated residential energy codes.\n"
    response += "\n⚠️ *This is educational guidance. Code applicability, mandatory status, and specific provisions depend on state-level adoption. For formal compliance assessment, consult a BEE-certified energy auditor.*"
    return response


# ─── Climate Zone Info ──────────────────────────────────────────────

def _get_climate_info(zone: str) -> str:
    """Return climate-zone-specific guidance."""
    z = zone.lower()
    if 'hot' in z and 'dry' in z:
        return ("**Hot-Dry Climate Zone**\n"
                "- High temperatures with low humidity for most of the year\n"
                "- Example cities: Jaipur, Jodhpur, Ahmedabad\n"
                "- **Key priorities:** Roof insulation, external shading, light-coloured surfaces, "
                "reducing west-facing glazing, thermal mass for night cooling\n"
                "- Eco Niwas Samhita has specific RETV limits for this zone")
    if 'warm' in z and 'humid' in z:
        return ("**Warm-Humid Climate Zone**\n"
                "- Warm temperatures with consistently high humidity\n"
                "- Example cities: Chennai, Mumbai, Kolkata, Thiruvananthapuram\n"
                "- **Key priorities:** Ventilation, dehumidification, shading from rain and sun, "
                "reflective roofing\n"
                "- Natural ventilation is especially important in this zone")
    if 'composite' in z:
        return ("**Composite Climate Zone**\n"
                "- Significant seasonal variation — neither purely hot-dry, warm-humid, temperate, nor cold\n"
                "- Example cities: New Delhi, Lucknow, Allahabad, Patna\n"
                "- **Key priorities:** Balanced approach for summer cooling and winter comfort, "
                "adaptable shading, moderate insulation\n"
                "- Most of northern India falls in this zone")
    if 'temperate' in z:
        return ("**Temperate Climate Zone**\n"
                "- Moderate temperatures throughout the year\n"
                "- Example cities: Bengaluru, Pune\n"
                "- **Key priorities:** Maximise natural ventilation and daylight, minimal "
                "cooling/heating needs\n"
                "- Energy focus can be on lighting and appliance efficiency")
    if 'cold' in z:
        return ("**Cold Climate Zone**\n"
                "- Low temperatures for a significant part of the year\n"
                "- Example cities: Shimla, Srinagar, Leh, Darjeeling\n"
                "- **Key priorities:** Insulation, airtightness, passive solar heating, "
                "double-glazed windows\n"
                "- Heating is the dominant energy concern")
    return ("India has five climate zones as defined by BEE/ENS: "
            "Composite, Hot-Dry, Warm-Humid, Temperate, and Cold. "
            "Each zone has different energy priorities for building design.")


# ─── Static Knowledge Base ──────────────────────────────────────────

def _knowledge_base_entry(topic: str) -> str:
    """Return a curated knowledge-base entry for a given topic."""
    entries = {
        'savings': """### 💡 Practical Ways to Reduce Your Electricity Bill

**1. Low Cost, High Impact (Do First):**
- Switch off appliances when not in use
- Set AC to 24–26°C (each degree lower increases consumption by ~3–5%)
- Clean AC filters regularly (dirty filters increase consumption by 5–15%)
- Use natural ventilation when weather permits
- Reduce geyser usage time; set thermostat to 50–55°C
- Unplug standby electronics (chargers, set-top boxes)

**2. Moderate Cost, Good Returns:**
- Replace incandescent/CFL lights with LED (saves 60–80% lighting energy)
- Replace old ceiling fans with BEE 5-star or BLDC fans (28–35W vs 70–80W)
- Install timer switches for geysers and outdoor lights
- Seal gaps around windows and doors

**3. Higher Investment, Long-term Savings:**
- Replace old AC with 5-star inverter AC
- Install a solar water heater
- Evaluate rooftop solar PV
- Improve roof or wall insulation
- Upgrade to energy-efficient refrigerator

*Actual savings depend on your specific usage patterns, building characteristics, and local climate.*""",

        'prioritize': """### 📋 How to Prioritise Energy-Saving Measures

**General principle:** Start with free behavioural changes → low-cost upgrades → larger investments with payback analysis.

**Priority 1 — No/Low Cost:**
- Switch off unused appliances and lights
- Set AC to 24°C
- Clean AC filters
- Reduce geyser heating time
- Use natural ventilation

**Priority 2 — Moderate Cost:**
- Replace incandescent/CFL lights with LEDs
- Replace conventional fans with BLDC fans
- Seal gaps around doors/windows
- Install timer switches

**Priority 3 — Higher Investment:**
- Upgrade to 5-star inverter AC
- Solar water heater installation
- Rooftop solar PV evaluation
- Roof/wall insulation improvement
- Efficient refrigerator upgrade

*Check the Recommendations & Savings page for estimated savings specific to your building's appliance inventory.*""",

        'methodology': """### 📐 Calculation Methodology and Assumptions

The energy consumption estimates in this audit use the following formulas:

**Daily Consumption** = Quantity × Rated Power (W) × Hours Used per Day ÷ 1000 → kWh

**Monthly Consumption** = Quantity × Rated Power (W) × Hours/Day × Days/Month ÷ 1000 → kWh

**Annual Consumption** = Monthly Consumption × 12

**Electricity Cost** = Consumption (kWh) × Tariff (₹/kWh)

**Key Assumptions:**
1. **Rated power** is used as a proxy for actual power draw. Actual draw may be lower for thermostat-controlled appliances (ACs, refrigerators, water heaters) due to duty cycles.
2. **Usage hours** are user-estimated averages, not continuous measurements.
3. **Electricity tariff** is a flat rate. Actual tariffs may have slab structures, time-of-day rates, or seasonal variations.
4. **Annual projection** assumes the monthly usage pattern remains constant, which may not reflect seasonal variations (e.g., higher AC use in summer).
5. **Savings estimates** use assumed reduction percentages, not guaranteed outcomes.

*For more accurate consumption data, consider using an energy meter or power monitor on individual appliances.*""",

        'units': """### 📏 Understanding Energy Units

**Watt (W):** A unit of **power** — the rate at which an appliance uses energy.
- Example: A 100W bulb uses energy at 100 watts

**Kilowatt (kW):** 1 kW = 1000 W
- Example: A 1500W geyser = 1.5 kW

**Kilowatt-hour (kWh):** A unit of **energy** — the total energy used over time.
- 1 kWh = using 1000 watts for 1 hour
- This is what your electricity meter measures
- Often called a "unit" on electricity bills in India

**How to calculate:**
- A 100W bulb running for 10 hours: 100 × 10 ÷ 1000 = **1 kWh**
- A 1500W geyser running for 30 minutes: 1500 × 0.5 ÷ 1000 = **0.75 kWh**

**Electricity Cost:**
- Cost = kWh consumed × Tariff (₹/kWh)
- If tariff is ₹7/kWh and you use 300 kWh/month: Cost = **₹2,100/month**
- Note: Actual bills also include fixed charges, taxes, and may use slab-based tariffs""",

        'report': """### 📄 About the Energy Audit Report

The downloadable PDF report includes:

1. **Scope and Methodology** — Audit approach and calculation methods
2. **Building Profile** — Your building details as entered
3. **Appliance Inventory** — All listed appliances with consumption estimates
4. **Consumption Summary** — Daily, monthly, and annual estimates
5. **Bill Comparison** — Calculated vs. billed consumption (if bill data entered)
6. **Audit Findings** — Categorised observations by confidence level
7. **Envelope Assessment** — Preliminary building envelope observations
8. **Recommendations** — Potential energy-saving interventions with estimated savings
9. **Code References** — Relevant Indian energy conservation standards
10. **Limitations** — What the audit covers and doesn't cover

**To generate the report:**
1. Enter your building profile (or load sample data)
2. Add your appliances
3. Navigate to **📄 Download Audit Report** in the sidebar
4. Click the download button

The report is generated from your actual entered data, not from hardcoded results. It works without AI API access.""",

        'solar': """### ☀️ Rooftop Solar for Residential Buildings in India

**Potential Benefits:**
- Can offset 30–80% of electricity consumption depending on system size and location
- Net metering policies in many states allow feeding excess power to the grid
- Government subsidies available under PM Surya Ghar scheme and state-level programmes

**Key Considerations:**
- Roof area, orientation (south-facing is ideal), and shading affect generation
- Typical residential systems: 1–10 kWp
- Approximate cost: ₹45,000–65,000 per kWp (after subsidy — varies by state and system size)
- Payback period: typically 4–7 years depending on tariff and generation

**Important Notes:**
- These are general estimates. Actual solar generation depends on your specific location, roof conditions, and weather
- A professional solar assessment is recommended before installation
- Check your state electricity board's net metering policy
- Ensure structural adequacy of the roof for panel weight

*Consult a reputable solar installer for a site-specific proposal.*""",

        'ac_cooling': """### ❄️ Tips for Efficient Air Conditioning

1. **Set thermostat to 24–26°C** — BEE recommends 24°C. Each degree lower increases consumption by ~3–5%.
2. **Regular maintenance** — Clean or replace filters every 1–2 months. Dirty filters increase consumption by 5–15%.
3. **Seal the room** — Close doors and windows while AC is running. Seal gaps with weather stripping.
4. **Use fans together** — A ceiling fan allows you to set the AC 2–3°C higher while maintaining comfort.
5. **Inverter technology** — Inverter ACs adjust compressor speed and are more efficient at part loads.
6. **Right sizing** — An oversized AC short-cycles and wastes energy. Choose the right tonnage for your room.
7. **Avoid heat sources** — Keep heat-generating appliances away from the AC thermostat sensor.
8. **Curtains and blinds** — Block direct sunlight, especially on east and west-facing windows.

*A 5-star AC can be 20–30% more efficient than a 3-star AC of the same capacity. Check the BEE star label year, as criteria are revised periodically.*""",

        'lighting': """### 💡 Efficient Lighting for Residential Buildings

**LED vs. Other Technologies:**

| Type | Typical Power | Lumens/Watt | Lifespan |
|------|--------------|-------------|----------|
| Incandescent | 60W | 10–15 | 1,000 hrs |
| CFL | 14W | 50–70 | 8,000 hrs |
| LED | 7–10W | 80–120 | 25,000+ hrs |

**Key Recommendations:**
1. Replace all incandescent and CFL bulbs with LEDs — saves 60–80% lighting energy
2. Use task lighting instead of illuminating entire rooms
3. Install occupancy sensors in bathrooms and corridors
4. Maximise natural daylight during daytime
5. Choose warm white (2700–3000K) for living areas and cool white (4000–6500K) for work areas
6. Look for BEE star-rated LED lamps for verified efficiency

*Replacing 10 × 60W incandescent bulbs with 10 × 9W LEDs could save ~92 kWh/month (illustrative example at 6 hrs/day usage).*""",

        'water_heating': """### 🚿 Water Heating Efficiency

**Electric water heaters (geysers)** are high-power appliances (typically 1500–3000W):

**Tips to reduce consumption:**
1. Reduce heating duration — 15–20 minutes is usually sufficient
2. Set thermostat to 50–55°C (not maximum)
3. Use a timer to avoid keeping the geyser on unnecessarily
4. Choose the right capacity — larger tanks lose more standby heat
5. Choose BEE 5-star rated geysers (better insulation)
6. Consider a **solar water heater** — can reduce electric water-heating energy by 60–80%

**Solar water heater benefits in India:**
- Works well in most Indian climates (except consistently cloudy regions)
- Typical payback: 3–5 years
- Government subsidies may be available

*A BEE 5-star geyser has better insulation reducing standby heat loss compared to lower-rated models.*""",

        'ventilation': """### 🌬️ Natural Ventilation and Air Flow

**Benefits of good natural ventilation:**
- Reduces dependency on mechanical cooling (AC)
- Improves indoor air quality
- Zero energy cost

**Strategies:**
1. **Cross-ventilation** — Open windows on opposite sides of a room to create airflow
2. **Stack ventilation** — Use stairwells and height differences to create natural updraft
3. **Ceiling fans** — Supplement natural ventilation; BLDC fans use only 28–35W
4. **Window design** — Larger, well-placed windows improve airflow
5. **Avoid obstructions** — Don't block windows with furniture

**When to use AC vs. ventilation:**
- Use natural ventilation when outdoor temperature is below 28–30°C
- Combine fans with open windows during moderate weather
- Switch to AC only during peak summer or high humidity

*Eco Niwas Samhita considers ventilation as part of building envelope design.*""",

        'bee_star': """### ⭐ BEE Standards & Labelling Programme

**How it works:**
- Appliances rated from 1 star (least efficient) to 5 stars (most efficient)
- The label shows annual energy consumption in kWh for easy comparison
- Higher stars = lower energy bills for the same performance

**Mandatory labelling** (must have star label):
- Room air conditioners (split & window)
- Refrigerators (frost-free & direct cool)
- Ceiling fans
- Electric geysers
- Tubular fluorescent lamps

**Voluntary labelling** (optional):
- LED lamps, TVs, washing machines, computers, etc.

**Tips:**
- Star ratings are revised periodically — a 5-star from 2018 may not meet 2024 5-star criteria
- Always check the year/schedule on the label
- BLDC motor fans (28–35W) are significantly more efficient than conventional fans (70–80W)

**Official website:** https://beestarlabel.com/""",

        'audit_process': """### 🔍 How Does a Residential Energy Audit Work?

A residential energy audit systematically examines how energy is used in a home to identify waste and improvement opportunities.

**Typical Steps:**

1. **Building Information Collection**
   - Building type, age, area, construction materials
   - Location and climate zone
   - Occupancy patterns

2. **Appliance Inventory**
   - List all electrical appliances
   - Note rated power, quantity, and estimated usage hours
   - Identify efficiency ratings (BEE star labels)

3. **Energy Consumption Analysis**
   - Calculate appliance-wise estimated consumption
   - Compare with actual electricity bills
   - Identify high-consuming appliances

4. **Building Envelope Assessment**
   - Evaluate roof, walls, windows, and insulation
   - Assess natural ventilation and solar heat gain
   - Note construction quality and age-related deterioration

5. **Findings and Recommendations**
   - Identify energy-saving opportunities
   - Prioritise by cost, impact, and ease of implementation
   - Estimate potential savings

6. **Reporting**
   - Document methodology, findings, and recommendations
   - Reference applicable codes and standards

*EcoAudit AI performs steps 1–6 as a preliminary educational assessment. A professional BEE-certified auditor would add instrumented measurements, thermal imaging, and detailed code compliance analysis.*""",

        'payback': """### 💰 Understanding Payback Period

**What is payback period?**
The time it takes for an energy-saving investment to pay for itself through reduced electricity bills.

**Formula:**
Payback (months) = Implementation Cost (₹) ÷ Monthly Savings (₹/month)

**Example:**
- Replacing 10 old fans with BLDC fans: Cost ≈ ₹25,000
- Monthly saving: ≈ 30 kWh × ₹7/kWh = ₹210/month
- Payback: ₹25,000 ÷ ₹210 ≈ 119 months (~10 years)

**Important Notes:**
- Payback calculation requires both cost and credible savings estimates
- Shorter payback = better financial return
- Consider equipment lifespan — a measure with 10-year payback is still worthwhile if the equipment lasts 15+ years
- Don't forget maintenance cost savings and comfort improvements
- Subsidies and incentives can significantly reduce payback period

*The Recommendations & Savings page lets you adjust reduction percentages and implementation costs to see payback estimates.*""",

        'climate_zones': """### 🌡️ Indian Climate Zones (as per BEE/ENS)

India has **five climate zones** that affect building energy requirements:

1. **Composite** — New Delhi, Lucknow, Allahabad, Patna
   - Significant seasonal variation; needs balanced cooling and winter comfort

2. **Hot-Dry** — Jaipur, Jodhpur, Ahmedabad
   - High temperatures, low humidity; prioritise insulation and shading

3. **Warm-Humid** — Chennai, Mumbai, Kolkata
   - Warm with high humidity; prioritise ventilation and dehumidification

4. **Temperate** — Bengaluru, Pune
   - Moderate year-round; maximise natural ventilation and daylight

5. **Cold** — Shimla, Srinagar, Leh
   - Low temperatures; prioritise insulation, airtightness, passive solar heating

Each zone has different building envelope requirements under Eco Niwas Samhita.""",
    }

    return entries.get(topic, _fallback_response())


def _match_knowledge_base(msg: str, context: Dict[str, Any] = None) -> str:
    """Match against the static knowledge base using keyword scoring."""

    if any(phrase in msg for phrase in (
        'what is ecoaudit', 'what does ecoaudit', 'what is eco audit',
        'what does eco audit', 'purpose of ecoaudit', 'purpose of eco audit',
        'what is this app', 'what does this app do', 'what is this system',
    )):
        return ("**EcoAudit AI** is an educational residential energy-audit app. "
                "It helps you enter a building profile, list appliances and "
                "electricity bills, estimate energy use and costs, review "
                "audit findings, explore Indian energy-code references, see "
                "energy-saving recommendations, and download a PDF audit report.\n\n"
                "Its consumption figures are calculated estimates based on "
                "the data and usage assumptions entered in the app; they are "
                "not instrument measurements or a certified compliance audit. "
                "The AI Assistant can answer general questions and, when live "
                "API credentials are configured, use the current audit context "
                "to make relevant answers building-specific.")

    scoring = [
        (['reduce', 'bill', 'save', 'saving', 'lower', 'cut', 'decrease', 'electricity bill',
          'bachat', 'kam', 'kaise kam'], 'savings'),
        (['eco niwas', 'ens', 'niwas samhita', 'residential code'], 'ens_code'),
        (['bee', 'star', 'label', 'rating', 'star rating'], 'bee_star'),
        (['solar', 'panel', 'rooftop', 'photovoltaic', 'pv', 'renewable', 'saur'], 'solar'),
        (['ac', 'air condition', 'cooling', 'temperature', 'thermostat', 'thanda'], 'ac_cooling'),
        (['light', 'led', 'bulb', 'cfl', 'tube', 'lamp', 'batti'], 'lighting'),
        (['geyser', 'water heater', 'hot water', 'garam pani'], 'water_heating'),
        (['ventilat', 'air flow', 'cross ventil', 'hawa'], 'ventilation'),
        (['ecbc', 'ecsbc', 'commercial code', 'building code energy'], 'ecbc_code'),
        (['national building code', 'nbc', 'bureau of indian standards'], 'nbc_code'),
        (['priorit', 'first', 'most important', 'which measure', 'where to start', 'pehle'], 'prioritize'),
        (['unit', 'kwh', 'watt', 'kw', 'explain unit', 'what is kwh'], 'units'),
        (['report', 'pdf', 'download', 'generate report'], 'report'),
        (['payback', 'roi', 'return on investment', 'cost benefit'], 'payback'),
        (['method', 'formula', 'assumption', 'how calculated', 'methodology'], 'methodology'),
        (['energy audit', 'audit process', 'what is audit', 'how audit'], 'audit_process'),
        (['climate', 'zone', 'jalvayu', 'weather'], 'climate_zones'),
        (['code', 'standard', 'regulation', 'india', 'niyam'], 'general_codes'),
    ]

    best_topic = None
    best_score = 0

    for keywords, topic in scoring:
        score = sum(1 for kw in keywords if kw in msg)
        if score > best_score:
            best_score = score
            best_topic = topic

    if best_topic and best_score > 0:
        # Code topics get contextualised responses
        if best_topic == 'ens_code':
            return _code_response_for_building(context, 'ens')
        if best_topic == 'ecbc_code':
            return _code_response_for_building(context, 'ecbc')
        if best_topic == 'nbc_code':
            return _code_response_for_building(context, 'nbc')
        if best_topic == 'general_codes':
            return _code_response_for_building(context, 'general')
        return _knowledge_base_entry(best_topic)

    # Check for Hinglish greetings
    if _is_hinglish(msg):
        bp = (context or {}).get('building_profile', {})
        name = bp.get('name', '')
        resp = "Namaste! 👋 Main EcoAudit AI Assistant hoon."
        if name:
            resp += f" Aap **{name}** par kaam kar rahe hain."
        resp += ("\n\nMain aapki madad kar sakta hoon:\n"
                "- 📊 Bijli ki kharchi samajhne mein\n"
                "- 💡 Energy bachat ke tips\n"
                "- 📜 Indian energy codes aur standards\n"
                "- 🔍 Audit findings samajhne mein\n\n"
                "Kripya apna sawaal poochein! Suggested questions bhi try kar sakte hain.\n\n"
                "*Yeh demo mode hai — curated knowledge base se jawaab deta hai. "
                "AI mode ke liye `.env` file mein API key set karein.*")
        return resp

    return _fallback_response()


def _fallback_response() -> str:
    """Return a helpful fallback when no topic matches."""
    return """I appreciate your question! In **demo mode**, I can answer questions about:

- 📊 **Your energy consumption** — appliance-wise breakdown, total usage, costs
- 💰 **Electricity bills** — bill analysis, calculated vs. billed comparison
- 🔍 **Audit findings** — observations from your building data
- 💡 **Energy-saving tips** — practical recommendations for reducing consumption
- 📜 **Indian energy codes** — Eco Niwas Samhita, ECBC, BEE star labels, NBC
- 🏗️ **Building envelope** — roof, walls, windows, insulation, ventilation
- 📐 **Methodology** — how calculations work, assumptions used
- 📄 **Audit report** — how to generate and download the PDF report

**Try asking a more specific question**, such as:
- "What are my top consuming appliances?"
- "Which Indian energy codes apply to my building?"
- "How can I reduce my electricity bill?"

*Note: Demo mode uses a curated knowledge base with keyword matching. For fully conversational AI responses, configure a Google Gemini or OpenAI API key in the `.env` file.*"""
