from typing import Protocol

from car_radio.domain.models import RadioMessage, RadioReading


class ClassifierError(Exception):
    pass


class ClassifierUnavailableError(ClassifierError):
    pass


class ClassifierRateLimitedError(ClassifierError):
    pass


class ClassifierRejectError(ClassifierError):
    pass


class RadioClassifier(Protocol):
    async def read(self, message: RadioMessage) -> RadioReading: ...
