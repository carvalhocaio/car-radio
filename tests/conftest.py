from collections.abc import Callable

import pytest

from car_radio.domain.models import RadioReading, Topic, UrgencyLevel

ReadingFactory = Callable[..., RadioReading]


@pytest.fixture
def make_reading() -> ReadingFactory:
    def factory(
        topic: Topic = Topic.GENERAL,
        urgency: float = UrgencyLevel.INFO,
        box_request: float = 0.0,
    ) -> RadioReading:
        return RadioReading(
            topic=topic,
            topic_confidence=0.9,
            topic_probabilities={topic: 0.9},
            urgency=urgency,
            urgency_probabilities={UrgencyLevel(round(urgency)): 0.9},
            box_request=box_request,
        )

    return factory
