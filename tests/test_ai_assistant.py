"""Offline tests for live AI routing, prompts, history, and error behavior."""
import sys
import types

import pytest

from modules import ai_assistant


class FakeResponse:
    output_text = "A generated answer."


class FakeResponsesAPI:
    def __init__(self, exception=None):
        self.calls = []
        self.exception = exception

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exception:
            raise self.exception
        return FakeResponse()


@pytest.fixture
def fake_openai(monkeypatch):
    api = FakeResponsesAPI()
    client_instances = []

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs['api_key'] == 'test-key'
            self.responses = api
            client_instances.append(self)

    module = types.ModuleType('openai')
    module.OpenAI = FakeClient
    monkeypatch.setitem(sys.modules, 'openai', module)
    monkeypatch.setattr(ai_assistant, '_get_openai_key', lambda: 'test-key')
    monkeypatch.setattr(ai_assistant, 'get_ai_provider', lambda: 'openai')
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-4.1-mini')
    return api


@pytest.mark.parametrize('question', [
    'Why is the sky blue?',
    'Explain Python list comprehensions with an example.',
    'How should I interpret the sample building estimate?',
])
def test_arbitrary_questions_use_responses_api(question, fake_openai):
    context = {'building_profile': {'name': 'Sample Flat'}, 'is_sample_data': True,
               'consumption_summary': {'total_monthly_kwh': 120}}
    result = ai_assistant.get_ai_response(question, context, [])
    assert result['response'] == 'A generated answer.'
    assert result['mode'] == 'AI-Powered (OpenAI — gpt-4.1-mini)'
    call = fake_openai.calls[0]
    assert call['input'] == [{'role': 'user', 'content': question}]
    assert 'Sample Flat' in call['instructions']
    assert 'calculated by the app as estimates' in call['instructions']
    assert 'illustrative sample data' in call['instructions']


def test_prompt_answers_arbitrary_questions_and_adds_relevant_ecoaudit_context():
    prompt = ai_assistant._build_system_prompt({'building_profile': {'name': 'Home'}})
    assert 'Generate a fresh, relevant answer to the actual question' in prompt
    assert 'Do not force an EcoAudit connection into unrelated questions' in prompt
    assert 'briefly explain how they relate to the answer' in prompt


def test_prompt_localizes_for_indian_users_and_honors_language_choice():
    prompt = ai_assistant._build_system_prompt({
        'response_language': 'Hinglish',
        'building_profile': {'state': 'Maharashtra'},
    })
    assert 'Localize for India' in prompt
    assert '₹' in prompt
    assert 'Respond in: Hinglish' in prompt


def test_gemini_uses_low_thinking_effort_for_faster_responses(monkeypatch):
    calls = {}

    class Models:
        def generate_content(self, **kwargs):
            calls.update(kwargs)
            return types.SimpleNamespace(text='Fast generated response.')

    class Client:
        def __init__(self, **kwargs):
            self.models = Models()

    genai_module = types.ModuleType('google.genai')
    genai_module.Client = Client
    types_module = types.ModuleType('google.genai.types')
    types_module.ThinkingConfig = lambda **kwargs: kwargs
    types_module.GenerateContentConfig = lambda **kwargs: kwargs
    google_module = types.ModuleType('google')
    google_module.__path__ = []
    google_module.genai = genai_module
    monkeypatch.setitem(sys.modules, 'google', google_module)
    monkeypatch.setitem(sys.modules, 'google.genai', genai_module)
    monkeypatch.setitem(sys.modules, 'google.genai.types', types_module)
    monkeypatch.setattr(ai_assistant, '_get_google_key', lambda: 'test-key')
    monkeypatch.setattr(ai_assistant, 'get_ai_provider', lambda: 'google')
    monkeypatch.setenv('GOOGLE_MODEL', 'gemini-3.8-flash')

    result = ai_assistant.get_ai_response('Explain kWh briefly.')
    assert result['response'] == 'Fast generated response.'
    assert calls['config']['thinking_config'] == {'thinking_level': 'low'}
    assert calls['config']['max_output_tokens'] == 700


def test_followup_sends_prior_turns_and_current_question(fake_openai):
    history = [
        {'role': 'user', 'content': 'I have a 120 kWh monthly estimate.'},
        {'role': 'assistant', 'content': 'That is an appliance-based estimate.'},
    ]
    ai_assistant.get_ai_response('Why is it only an estimate?', {}, history)
    assert fake_openai.calls[0]['input'] == history + [
        {'role': 'user', 'content': 'Why is it only an estimate?'}
    ]


def test_verified_code_references_are_available_without_inventing_clauses(fake_openai):
    ai_assistant.get_ai_response(
        'Which standard should I read?',
        {'verified_code_references': [{
            'name': 'Eco Niwas Samhita (ENS)', 'edition': '2018',
            'issuing_authority': 'BEE', 'official_source': 'https://beeindia.gov.in/',
            'verification_note': 'Verify exact clauses from official publication.',
        }]},
    )
    instructions = fake_openai.calls[0]['instructions']
    assert 'Eco Niwas Samhita (ENS)' in instructions
    assert 'Verify exact clauses from official publication.' in instructions
    assert 'Never guarantee compliance or savings' in instructions
def test_missing_credentials_is_explicit_demo(monkeypatch):
    monkeypatch.setattr(ai_assistant, '_get_google_key', lambda: '')
    monkeypatch.setattr(ai_assistant, '_get_openai_key', lambda: '')
    result = ai_assistant.get_ai_response('What is a kilowatt-hour?')
    available, status = ai_assistant.check_ai_availability()
    assert result['mode'].startswith('Demo Mode')
    assert not available
    assert 'not generative AI' in status


def test_ecoaudit_product_question_works_without_building_data(monkeypatch):
    monkeypatch.setattr(ai_assistant, '_get_google_key', lambda: '')
    monkeypatch.setattr(ai_assistant, '_get_openai_key', lambda: '')
    result = ai_assistant.get_ai_response('What is EcoAudit used for?')
    assert result['mode'] == 'Demo Mode (Product Information)'
    assert 'educational residential energy-audit app' in result['response']
    assert 'PDF audit report' in result['response']


def test_api_error_does_not_fall_back_to_demo(fake_openai):
    fake_openai.exception = ConnectionError('network unavailable')
    result = ai_assistant.get_ai_response('Tell me a joke.')
    assert result['error']
    assert 'couldn\'t get a live response' in result['response']
    assert 'Demo Mode' not in result['mode']


def test_unsupported_model_rejected_before_api_call(fake_openai, monkeypatch):
    monkeypatch.setenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    result = ai_assistant.get_ai_response('Hello')
    assert result['error'] == 'Unsupported OpenAI Responses API model.'
    assert not fake_openai.calls
