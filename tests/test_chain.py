from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import openai

from app.chain.stage1 import extract_features
from app.chain.stage2 import interpret_prediction
from app.schemas.features import ExtractedFeatures


def make_response(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def make_client(create_callable) -> SimpleNamespace:
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create_callable),
        )
    )


def test_stage1_returns_empty_features_on_garbage_json(monkeypatch) -> None:
    monkeypatch.setattr(
        'app.chain.stage1.get_client',
        Mock(return_value=make_client(Mock(return_value=make_response('not json')))),
    )
    monkeypatch.setattr(
        'app.chain.stage1.get_settings',
        Mock(return_value=SimpleNamespace(model_name='gpt-4o-mini')),
    )

    features = extract_features('3 bedroom ranch in OldTown')

    assert len(features.missing_fields()) == 12


def test_stage1_returns_empty_features_on_validation_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        'app.chain.stage1.get_client',
        Mock(
            return_value=make_client(
                Mock(return_value=make_response('{"OverallQual": 99}'))
            )
        ),
    )
    monkeypatch.setattr(
        'app.chain.stage1.get_settings',
        Mock(return_value=SimpleNamespace(model_name='gpt-4o-mini')),
    )

    features = extract_features('excellent home')

    assert features.to_model_input()['OverallQual'] is None
    assert len(features.missing_fields()) == 12


def test_stage2_returns_stats_fallback_on_api_error(monkeypatch) -> None:
    api_error = openai.APIError(
        'boom',
        request=httpx.Request('POST', 'https://api.openai.com/v1/chat/completions'),
        body=None,
    )
    monkeypatch.setattr(
        'app.chain.stage2.get_client',
        Mock(return_value=make_client(Mock(side_effect=api_error))),
    )
    monkeypatch.setattr(
        'app.chain.stage2.get_settings',
        Mock(return_value=SimpleNamespace(model_name='gpt-4o-mini')),
    )

    text = interpret_prediction(
        query='3 bedroom ranch in OldTown',
        features=ExtractedFeatures(BedroomAbvGr=3, Neighborhood='OldTown'),
        predicted_price=200000,
        stats={'price': {'median': 160000}},
    )

    assert text == 'The model predicts $200,000, above the training-set median of $160,000.'
