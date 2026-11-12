from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, model_validator

from car_radio.domain.models import RadioMessage, Topic, UrgencyLevel


class QuestionKey(StrEnum):
    TOPIC = "topic"
    URGENCY = "urgency"
    BOX_REQUEST = "box_request"


class RadioContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    version: str
    topic_instructions: str
    topic_criteria: dict[Topic, str]
    urgency_instructions: str
    urgency_criteria: dict[UrgencyLevel, str]
    box_request_instructions: str

    @model_validator(mode="after")
    def _cover_every_option(self) -> Self:
        if missing := set(Topic) - self.topic_criteria.keys():
            raise ValueError(f"topic criteria missing: {sorted(missing)}")
        if missing := set(UrgencyLevel) - self.urgency_criteria.keys():
            raise ValueError(f"urgency criteria missing: {sorted(missing)}")
        return self

    @property
    def urgency_scale(self) -> list[str]:
        return [self.urgency_criteria[level] for level in sorted(UrgencyLevel)]

    def state_for(self, message: RadioMessage) -> dict[str, Any]:
        context = message.context
        return {
            "driver_radio": message.text,
            "race_context": {
                **context.model_dump(mode="json"),
                "laps_remaining": context.laps_remaining,
            },
        }


RADIO_CONTRACT_V1 = RadioContract(
    version="radio-v1",
    topic_instructions=(
        "Which topic best describes what the driver says in `driver_radio`?"
    ),
    topic_criteria={
        Topic.TYRES: (
            "Grip, wear, degradation, graining, blistering, tyre temperatures "
            "or the tyre compound."
        ),
        Topic.CAR_ISSUE: (
            "A mechanical, power unit, brake, gearbox, hydraulic, electrical "
            "or damage problem with the car."
        ),
        Topic.STRATEGY: (
            "Pit stop timing, pace targets, fuel or energy management, "
            "or questions about the race plan."
        ),
        Topic.WEATHER: "Rain, wind, or grip changing because of the weather.",
        Topic.TRACK_INCIDENT: (
            "Debris, a crash, a car stopped on track, flags, a safety car "
            "or another driver's dangerous move."
        ),
        Topic.COMPLAINT: (
            "Frustration about another driver, the team, blue flags or a penalty, "
            "without asking for any action."
        ),
        Topic.GENERAL: "Acknowledgements, small talk or anything else.",
    },
    urgency_instructions=(
        "How soon does the pit wall need to act on `driver_radio`, "
        "considering `race_context`?"
    ),
    urgency_criteria={
        UrgencyLevel.INFO: "No action needed, the message is informational.",
        UrgencyLevel.MONITOR: "Keep watching it over the next few laps.",
        UrgencyLevel.SOON: "Act within the next one or two laps.",
        UrgencyLevel.NOW: "Act on this lap, safety or the race result is at stake.",
    },
    box_request_instructions=(
        "Is the driver in `driver_radio` asking for or suggesting a pit stop right now?"
    ),
)

DEFAULT_CONTRACT = RADIO_CONTRACT_V1
