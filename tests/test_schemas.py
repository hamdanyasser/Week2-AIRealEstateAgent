import pytest
from pydantic import ValidationError

from app.schemas.features import ExtractedFeatures
from app.schemas.response import ExtractionResponse, PredictionResponse


def test_extracted_features_report_present_and_missing_aliases() -> None:
    features = ExtractedFeatures(
        BedroomAbvGr=3,
        YearBuilt=1960,
        Neighborhood='OldTown',
    )

    assert features.present_fields() == [
        'BedroomAbvGr',
        'YearBuilt',
        'Neighborhood',
    ]
    assert 'GrLivArea' in features.missing_fields()
    assert len(features.missing_fields()) == 9


def test_extraction_response_computes_completeness_metadata() -> None:
    features = ExtractedFeatures(
        BedroomAbvGr=3,
        Neighborhood='OldTown',
    )

    response = ExtractionResponse.from_features(
        query='3 bedroom home in OldTown',
        prompt_version='v2',
        features=features,
    )

    assert response.present_features == ['BedroomAbvGr', 'Neighborhood']
    assert response.missing_features[0] == 'GrLivArea'
    assert response.completeness_ratio == pytest.approx(2 / 12)
    assert response.is_complete is False


def test_prediction_response_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        PredictionResponse(
            query='test query',
            extracted_features=ExtractedFeatures(),
            missing_features=['GrLivArea'],
            predicted_price=100000,
            interpretation='A concise explanation.',
            model_name='RandomForestRegressor',
            unexpected='boom',
        )
