import pytest
from pydantic import ValidationError

from car_radio.domain.models import PitWallCall, Topic, UrgencyLevel
from car_radio.domain.pit_wall import (
    BoxCutoffs,
    EscalationCutoffs,
    PitWall,
    RuleName,
)
from tests.conftest import ReadingFactory


@pytest.fixture
def pit_wall() -> PitWall:
    return PitWall()


def test_confirmed_box_request_calls_the_driver_in(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    decision = pit_wall.decide(make_reading(topic=Topic.TYRES, box_request=0.93))

    assert decision.call is PitWallCall.BOX_BOX
    assert decision.rule is RuleName.BOX_CONFIRMED


@pytest.mark.parametrize("topic", [Topic.CAR_ISSUE, Topic.TRACK_INCIDENT])
def test_safety_topics_escalate_at_moderate_urgency(
    pit_wall: PitWall, make_reading: ReadingFactory, topic: Topic
) -> None:
    decision = pit_wall.decide(make_reading(topic=topic, urgency=1.2))

    assert decision.call is PitWallCall.ENGINEER_NOW
    assert decision.rule is RuleName.SAFETY_ESCALATION


def test_non_safety_topic_at_moderate_urgency_is_only_logged(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    decision = pit_wall.decide(make_reading(topic=Topic.COMPLAINT, urgency=1.2))

    assert decision.call is PitWallCall.LOG


def test_any_topic_escalates_near_the_top_of_the_scale(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    decision = pit_wall.decide(make_reading(topic=Topic.WEATHER, urgency=2.7))

    assert decision.call is PitWallCall.ENGINEER_NOW
    assert decision.rule is RuleName.URGENT_ESCALATION


def test_escalation_beats_an_ambiguous_box_request(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    reading = make_reading(
        topic=Topic.CAR_ISSUE, urgency=UrgencyLevel.NOW, box_request=0.5
    )

    assert pit_wall.decide(reading).call is PitWallCall.ENGINEER_NOW


def test_grey_zone_box_request_asks_the_driver_to_repeat(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    decision = pit_wall.decide(make_reading(topic=Topic.TYRES, box_request=0.5))

    assert decision.call is PitWallCall.SAY_AGAIN
    assert decision.rule is RuleName.AMBIGUOUS_BOX


@pytest.mark.parametrize("box_request", [0.2, 0.8])
def test_cutoff_bounds_are_not_ambiguous(
    pit_wall: PitWall, make_reading: ReadingFactory, box_request: float
) -> None:
    decision = pit_wall.decide(make_reading(box_request=box_request))

    assert decision.call is not PitWallCall.SAY_AGAIN


def test_calm_message_is_logged(
    pit_wall: PitWall, make_reading: ReadingFactory
) -> None:
    decision = pit_wall.decide(make_reading())

    assert decision.call is PitWallCall.LOG
    assert decision.rule is RuleName.ROUTINE


def test_custom_cutoffs_change_the_decision(make_reading: ReadingFactory) -> None:
    strict = PitWall(box=BoxCutoffs(confirm=0.95, reject=0.05))

    assert strict.decide(make_reading(box_request=0.9)).call is PitWallCall.SAY_AGAIN


@pytest.mark.parametrize(("confirm", "reject"), [(0.5, 0.5), (0.3, 0.7)])
def test_box_cutoffs_reject_overlapping_bounds(confirm: float, reject: float) -> None:
    with pytest.raises(ValidationError, match="reject cutoff must be lower"):
        BoxCutoffs(confirm=confirm, reject=reject)


def test_safety_cutoff_cannot_exceed_urgent_cutoff() -> None:
    with pytest.raises(ValidationError, match="safety cutoff cannot be above"):
        EscalationCutoffs(urgent=1.5, safety=2.0)
