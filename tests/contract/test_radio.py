import pytest
from pydantic import ValidationError

from car_radio.contract.radio import RADIO_CONTRACT_V1, RadioContract
from car_radio.domain.models import (
    Compound,
    RaceContext,
    RadioMessage,
    Topic,
    UrgencyLevel,
)


@pytest.fixture
def message() -> RadioMessage:
    return RadioMessage(
        driver="LEC",
        text="Rears are gone, I can't hold him",
        context=RaceContext(
            lap=40,
            total_laps=57,
            compound=Compound.SOFT,
            tyre_age_laps=24,
            position=3,
            gap_ahead_seconds=1.8,
        ),
    )


def test_urgency_scale_runs_from_lowest_to_highest_level() -> None:
    scale = RADIO_CONTRACT_V1.urgency_scale

    assert len(scale) == len(UrgencyLevel)
    assert scale[0] == RADIO_CONTRACT_V1.urgency_criteria[UrgencyLevel.INFO]
    assert scale[-1] == RADIO_CONTRACT_V1.urgency_criteria[UrgencyLevel.NOW]


def test_state_names_match_what_the_instructions_reference(
    message: RadioMessage,
) -> None:
    state = RADIO_CONTRACT_V1.state_for(message)

    for key in state:
        assert f"`{key}`" in (
            RADIO_CONTRACT_V1.topic_instructions
            + RADIO_CONTRACT_V1.urgency_instructions
            + RADIO_CONTRACT_V1.box_request_instructions
        )


def test_state_carries_race_context_with_laps_remaining(
    message: RadioMessage,
) -> None:
    state = RADIO_CONTRACT_V1.state_for(message)

    assert state["driver_radio"] == message.text
    assert state["race_context"]["laps_remaining"] == 17
    assert state["race_context"]["compound"] == "soft"


def test_state_leaves_out_the_driver_code(message: RadioMessage) -> None:
    assert message.driver not in str(RADIO_CONTRACT_V1.state_for(message))


def test_contract_must_describe_every_topic() -> None:
    data = RADIO_CONTRACT_V1.model_dump()
    del data["topic_criteria"][Topic.WEATHER]

    with pytest.raises(ValidationError, match="topic criteria missing"):
        RadioContract.model_validate(data)


def test_contract_must_describe_every_urgency_level() -> None:
    data = RADIO_CONTRACT_V1.model_dump()
    del data["urgency_criteria"][UrgencyLevel.SOON]

    with pytest.raises(ValidationError, match="urgency criteria missing"):
        RadioContract.model_validate(data)
