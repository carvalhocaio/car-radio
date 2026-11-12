from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from car_radio.domain.models import (
    DomainModel,
    PitWallCall,
    RadioReading,
    Topic,
    UrgencyLevel,
)


class BoxCutoffs(BaseModel):
    confirm: float = Field(default=0.8, ge=0, le=1)
    reject: float = Field(default=0.2, ge=0, le=1)

    @model_validator(mode="after")
    def _reject_below_confirm(self) -> Self:
        if self.reject >= self.confirm:
            raise ValueError("reject cutoff must be lower than confirm cutoff")
        return self


class EscalationCutoffs(BaseModel):
    urgent: float = Field(default=2.5, ge=UrgencyLevel.INFO, le=UrgencyLevel.NOW)
    safety: float = Field(default=1.0, ge=UrgencyLevel.INFO, le=UrgencyLevel.NOW)

    @model_validator(mode="after")
    def _safety_not_above_urgent(self) -> Self:
        if self.safety > self.urgent:
            raise ValueError("safety cutoff cannot be above urgent cutoff")
        return self


class RuleName(StrEnum):
    BOX_CONFIRMED = "box_confirmed"
    SAFETY_ESCALATION = "safety_escalation"
    URGENT_ESCALATION = "urgent_escalation"
    AMBIGUOUS_BOX = "ambiguous_box"
    ROUTINE = "routine"


SAFETY_TOPICS = frozenset({Topic.CAR_ISSUE, Topic.TRACK_INCIDENT})


class PitWallDecision(DomainModel):
    call: PitWallCall
    rule: RuleName


@dataclass(frozen=True, slots=True)
class Rule:
    name: RuleName
    call: PitWallCall
    applies: Callable[[RadioReading], bool]


class PitWall:
    def __init__(
        self,
        box: BoxCutoffs | None = None,
        escalation: EscalationCutoffs | None = None,
    ) -> None:
        self._rules = self._build_rules(
            box or BoxCutoffs(), escalation or EscalationCutoffs()
        )

    def decide(self, reading: RadioReading) -> PitWallDecision:
        rule = next(rule for rule in self._rules if rule.applies(reading))
        return PitWallDecision(call=rule.call, rule=rule.name)

    @staticmethod
    def _build_rules(box: BoxCutoffs, escalation: EscalationCutoffs) -> Sequence[Rule]:
        return (
            Rule(
                RuleName.BOX_CONFIRMED,
                PitWallCall.BOX_BOX,
                lambda r: r.box_request >= box.confirm,
            ),
            Rule(
                RuleName.SAFETY_ESCALATION,
                PitWallCall.ENGINEER_NOW,
                lambda r: r.topic in SAFETY_TOPICS and r.urgency >= escalation.safety,
            ),
            Rule(
                RuleName.URGENT_ESCALATION,
                PitWallCall.ENGINEER_NOW,
                lambda r: r.urgency >= escalation.urgent,
            ),
            Rule(
                RuleName.AMBIGUOUS_BOX,
                PitWallCall.SAY_AGAIN,
                lambda r: box.reject < r.box_request < box.confirm,
            ),
            Rule(RuleName.ROUTINE, PitWallCall.LOG, lambda _: True),
        )
