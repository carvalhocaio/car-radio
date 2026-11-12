from enum import IntEnum, StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Topic(StrEnum):
    TYRES = "tyres"
    CAR_ISSUE = "car_issue"
    STRATEGY = "strategy"
    WEATHER = "weather"
    TRACK_INCIDENT = "track_incident"
    COMPLAINT = "complaint"
    GENERAL = "general"


class UrgencyLevel(IntEnum):
    INFO = 0
    MONITOR = 1
    SOON = 2
    NOW = 3


class Compound(StrEnum):
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"
    INTERMEDIATE = "intermediate"
    WET = "wet"


class PitWallCall(StrEnum):
    BOX_BOX = "box_box"
    ENGINEER_NOW = "engineer_now"
    SAY_AGAIN = "say_again"
    LOG = "log"


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True)


Probability = float


class RaceContext(DomainModel):
    lap: int = Field(ge=1)
    total_laps: int = Field(ge=1)
    compound: Compound
    tyre_age_laps: int = Field(ge=0)
    position: int = Field(ge=1)
    gap_ahead_seconds: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _lap_within_race(self) -> Self:
        if self.lap > self.total_laps:
            raise ValueError("lap cannot exceed total_laps")
        return self

    @property
    def laps_remaing(self) -> int:
        return self.total_laps - self.lap


class RadioMessage(DomainModel):
    driver: str = Field(pattern=r"^[A-Z]{3}$")
    text: str = Field(min_length=1, max_length=500)
    context: RaceContext


class RadioReading(DomainModel):
    topic: Topic
    topic_confidence: Probability = Field(ge=0, le=1)
    topic_probabilities: dict[Topic, Probability]
    urgency: float = Field(ge=UrgencyLevel.INFO, le=UrgencyLevel.NOW)
    urgency_probabilities: dict[UrgencyLevel, Probability]
    box_request: Probability = Field(ge=0, le=1)
