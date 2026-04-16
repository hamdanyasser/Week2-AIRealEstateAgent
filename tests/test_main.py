from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.features import ExtractedFeatures


def test_extract_endpoint_returns_completeness_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        'app.main.extract_features',
        Mock(
            return_value=ExtractedFeatures(
                BedroomAbvGr=3,
                Neighborhood='OldTown',
            )
        ),
    )

    with TestClient(app) as client:
        response = client.post('/extract', json={'query': '3 bedroom home in OldTown'})

    assert response.status_code == 200
    body = response.json()
    assert body['present_features'] == ['BedroomAbvGr', 'Neighborhood']
    assert body['missing_features'][0] == 'GrLivArea'
    assert body['completeness_ratio'] == 2 / 12


def test_predict_uses_reviewed_features_without_reextracting(monkeypatch) -> None:
    monkeypatch.setattr(
        'app.main.extract_features',
        Mock(side_effect=AssertionError('Stage 1 should not run for reviewed features')),
    )
    monkeypatch.setattr('app.main.predict_price', Mock(return_value=250000.0))
    monkeypatch.setattr(
        'app.main.interpret_prediction',
        Mock(return_value='The model predicts $250,000, above the median.'),
    )

    with TestClient(app) as client:
        response = client.post(
            '/predict',
            json={
                'query': '3 bedroom home in OldTown',
                'reviewed_features': {
                    'BedroomAbvGr': 3,
                    'Neighborhood': 'OldTown',
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body['predicted_price'] == 250000.0
    assert body['extracted_features']['BedroomAbvGr'] == 3
    assert 'GrLivArea' in body['missing_features']
