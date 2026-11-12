import pytest
from pydantic import ValidationError

from car_radio.domain.models import Compound, RaceContext, RadioMessage


def make_context(**overrides: object) -> RaceContext:
    defaults: dict[str, object] = {
        "lap": 30,
        "total_laps": 57,
        "compound": Compound.MEDIUM,
        "tyre_age_laps": 18,
        "position": 4,
    }
    return RaceContext.model_validate(defaults | overrides)


def test_laps_remaining_counts_down_to_the_flag() -> None:
    assert make_context().laps_remaining == 27


def test_lap_cannot_exceed_race_distance() -> None:
    with pytest.raises(ValidationError, match="lap cannot exceed total_laps"):
        make_context(lap=58)


@pytest.mark.parametrize("driver", ["ver", "VERS", "V3R", ""])
def test_driver_must_be_a_three_letter_code(driver: str) -> None:
    with pytest.raises(ValidationError):
        RadioMessage(driver=driver, text="Box, box", context=make_context())


def test_radio_message_is_immutable() -> None:
    message = RadioMessage(driver="NOR", text="Tyres are gone", context=make_context())

    with pytest.raises(ValidationError):
        message.text = "All good"
