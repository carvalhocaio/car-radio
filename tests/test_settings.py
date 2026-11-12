import pytest
from pydantic import ValidationError

from car_radio.settings import (
    OPENROUTER_BASE_URL,
    BoxCutoffs,
    ClassifierBackend,
    ClassifierSettings,
    Settings,
)


def make_classifier(**overrides: object) -> ClassifierSettings:
    return ClassifierSettings.model_validate({"api_key": "secret", **overrides})


def test_openrouter_is_default_backend_with_its_base_url() -> None:
    classifier = make_classifier()

    assert classifier.backend is ClassifierBackend.OPENROUTER
    assert classifier.resolved_base_url == OPENROUTER_BASE_URL


def test_typesafe_backend_falls_back_to_sdk_default_url() -> None:
    assert make_classifier(backend="typesafe").resolved_base_url is None


def test_explicit_base_url_wins_over_backend_default() -> None:
    classifier = make_classifier(base_url="http://localhost:9000")

    assert classifier.resolved_base_url == "http://localhost:9000"


def test_self_hosted_requires_base_url() -> None:
    with pytest.raises(ValidationError, match="base_url is required"):
        make_classifier(backend="self_hosted")


def test_api_key_is_never_exposed_in_repr() -> None:
    assert "secret" not in repr(make_classifier())


@pytest.mark.parametrize(("confirm", "reject"), [(0.5, 0.5), (0.3, 0.7)])
def test_box_cutoffs_reject_overlapping_bounds(confirm: float, reject: float) -> None:
    with pytest.raises(ValidationError, match="reject cutoff must be lower"):
        BoxCutoffs(confirm=confirm, reject=reject)


def test_settings_load_nested_values_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CAR_RADIO_CLASSIFIER__API_KEY", "from-env")
    monkeypatch.setenv("CAR_RADIO_CLASSIFIER__BACKEND", "typesafe")
    monkeypatch.setenv("CAR_RADIO_BOX_CUTOFFS__CONFIRM", "0.9")

    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.classifier.api_key.get_secret_value() == "from-env"
    assert settings.classifier.backend is ClassifierBackend.TYPESAFE
    assert settings.box_cutoffs.confirm == 0.9
    assert settings.box_cutoffs.reject == 0.2
