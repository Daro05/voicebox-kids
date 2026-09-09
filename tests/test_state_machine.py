import pytest

from voicebox.core.state_machine import DeviceState, InvalidTransitionError, StateMachine


def test_receive_and_play_cycle_returns_to_idle() -> None:
    machine = StateMachine()

    machine.transition_to(DeviceState.RECEIVING)
    machine.transition_to(DeviceState.PLAYING)
    machine.transition_to(DeviceState.IDLE)

    assert machine.state is DeviceState.IDLE


def test_invalid_transition_is_rejected() -> None:
    machine = StateMachine()

    with pytest.raises(InvalidTransitionError):
        machine.transition_to(DeviceState.SENDING)
