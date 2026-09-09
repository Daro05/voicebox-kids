"""Small interaction state machine shared by laptop and hardware builds."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DeviceState(StrEnum):
    IDLE = "idle"
    RECEIVING = "receiving"
    PLAYING = "playing"
    RECORDING = "recording"
    SENDING = "sending"
    ERROR = "error"


class InvalidTransitionError(RuntimeError):
    """Raised when an event is invalid for the current device state."""


_TRANSITIONS: dict[DeviceState, set[DeviceState]] = {
    DeviceState.IDLE: {DeviceState.RECEIVING, DeviceState.RECORDING},
    DeviceState.RECEIVING: {DeviceState.PLAYING, DeviceState.ERROR},
    DeviceState.PLAYING: {DeviceState.IDLE, DeviceState.ERROR},
    DeviceState.RECORDING: {DeviceState.SENDING, DeviceState.ERROR},
    DeviceState.SENDING: {DeviceState.IDLE, DeviceState.ERROR},
    DeviceState.ERROR: {DeviceState.IDLE},
}


@dataclass(slots=True)
class StateMachine:
    state: DeviceState = DeviceState.IDLE

    def transition_to(self, next_state: DeviceState) -> None:
        if next_state not in _TRANSITIONS[self.state]:
            raise InvalidTransitionError(f"Cannot transition from {self.state} to {next_state}.")
        self.state = next_state
