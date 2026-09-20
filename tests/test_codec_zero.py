from __future__ import annotations

import asyncio
from typing import Any

from voicebox.hardware.codec_zero import CodecZeroControls
from voicebox.hardware.controls import ControlEvent


class FakeButton:
    def __init__(self, pin: int, **options: Any) -> None:
        self.pin = pin
        self.options = options
        self.when_pressed: Any = None
        self.when_released: Any = None
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeLed:
    def __init__(self, pin: int) -> None:
        self.pin = pin
        self.value = False
        self.blinks: list[dict[str, Any]] = []
        self.closed = False

    def on(self) -> None:
        self.value = True

    def off(self) -> None:
        self.value = False

    def blink(self, **options: Any) -> None:
        self.blinks.append(options)

    def close(self) -> None:
        self.closed = True


class SilentCues:
    async def play(self, status: str) -> None:
        pass


def build_controls() -> tuple[CodecZeroControls, FakeButton, dict[int, FakeLed]]:
    buttons: list[FakeButton] = []
    leds: dict[int, FakeLed] = {}

    def button_factory(pin: int, **options: Any) -> FakeButton:
        button = FakeButton(pin, **options)
        buttons.append(button)
        return button

    def led_factory(pin: int) -> FakeLed:
        led = FakeLed(pin)
        leds[pin] = led
        return led

    controls = CodecZeroControls(
        SilentCues(),
        button_factory=button_factory,
        led_factory=led_factory,
    )
    return controls, buttons[0], leds


async def test_codec_zero_emits_press_and_release_events() -> None:
    controls, button, _ = build_controls()
    pressed = asyncio.create_task(controls.next_event())
    await asyncio.sleep(0)

    button.when_pressed()

    assert await pressed is ControlEvent.PRESS

    released = asyncio.create_task(controls.next_event())
    await asyncio.sleep(0)
    button.when_released()

    assert await released is ControlEvent.RELEASE


async def test_codec_zero_maps_recording_and_offline_leds() -> None:
    controls, _, leds = build_controls()
    green = leds[CodecZeroControls.GREEN_LED_PIN]
    red = leds[CodecZeroControls.RED_LED_PIN]

    await controls.set_status("recording")

    assert not green.value
    assert red.value

    await controls.set_status("offline")

    assert not green.value
    assert red.blinks[-1] == {"on_time": 0.2, "off_time": 0.8, "background": True}


async def test_codec_zero_releases_gpio_devices() -> None:
    controls, button, leds = build_controls()

    await controls.close()

    assert button.closed
    assert all(led.closed for led in leds.values())
