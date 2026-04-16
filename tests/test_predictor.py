import pandas as pd
from unittest.mock import Mock

from app.ml.pipeline import SELECTED_FEATURES
from app.ml.predictor import features_to_dataframe, predict_price
from app.schemas.features import ExtractedFeatures


class DummyPipeline:
    def __init__(self) -> None:
        self.frames = []

    def predict(self, frame):  # noqa: ANN001 - sklearn-like API surface
        self.frames.append(frame.copy())
        return [245000.0]


def test_features_to_dataframe_matches_training_schema() -> None:
    features = ExtractedFeatures(
        BedroomAbvGr=3,
        Neighborhood='OldTown',
    )

    frame = features_to_dataframe(features)

    assert list(frame.columns) == SELECTED_FEATURES
    assert frame.loc[0, 'Neighborhood'] == 'OldTown'
    assert frame.loc[0, 'BedroomAbvGr'] == 3
    assert pd.isna(frame.loc[0, 'GrLivArea'])


def test_predict_price_returns_pipeline_prediction(monkeypatch) -> None:
    pipeline = DummyPipeline()
    monkeypatch.setattr('app.ml.predictor.load_model', Mock(return_value=pipeline))

    price = predict_price(
        ExtractedFeatures(
            BedroomAbvGr=3,
            Neighborhood='OldTown',
        )
    )

    assert price == 245000.0
    assert list(pipeline.frames[0].columns) == SELECTED_FEATURES
