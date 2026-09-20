"""Raspberry Pi Codec Zero button and status-LED adapter."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from voicebox.audio.cues import SilentStatusCues, StatusCues
from voicebox.hardware.controls import ControlEvent

logger = logging.getLogger(__name__)

ButtonFactory = Callable[..., Any]
LedFactory = Callable[..., Any]


class CodecZeroControls:
    """Map the Codec Zero button and LEDs to provider-neutral controls."""

    BUTTON_PIN = 27
    GREEN_LED_PIN = 23
    RED_LED_PIN = 24

    def __init__(
        self,
        cues: StatusCues | None = None,
        *,
        button_factory: ButtonFactory | None = None,
        led_factory: LedFactory | None = None,
    ) -> None:
        if button_factory is None or led_factory is None:
            try:
                from gpiozero import LED, Button
            except ImportError as exc:
                raise RuntimeError(
                    "Codec Zero controls require GPIO Zero (`sudo apt install python3-gpiozero`)."
                ) from exc
            button_factory = button_factory or Button
            led_factory = led_factory or LED

        self._button = button_factory(
            self.BUTTON_PIN,
            pull_up=True,
            bounce_time=0.05,
        )
        self._green = led_factory(self.GREEN_LED_PIN)
        self._red = led_factory(self.RED_LED_PIN)
        self._cues = cues or SilentStatusCues()
        self._events: asyncio.Queue[ControlEvent] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def next_event(self) -> ControlEvent:
        self._bind_callbacks()
        return await self._events.get()

    async def set_status(self, status: str) -> None:
        self._stop_led_patterns()
        if status in {"idle", "sent", "cancelled"}:
            self._green.on()
            self._red.off()
        elif status == "recording":
            self._green.off()
            self._red.on()
        elif status in {"sending", "limit", "busy"}:
            self._green.on()
            self._red.on()
        elif status == "offline":
            self._green.off()
            self._red.blink(on_time=0.2, off_time=0.8, background=True)
        elif status == "error":
            self._green.off()
            self._red.blink(on_time=0.15, off_time=0.15, background=True)
        try:
            await self._cues.play(status)
        except Exception:
            logger.exception("Could not play the %s status cue", status)

    async def close(self) -> None:
        self._button.close()
        self._green.close()
        self._red.close()

    def _bind_callbacks(self) -> None:
        if self._loop is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._button.when_pressed = lambda: self._emit(ControlEvent.PRESS)
        self._button.when_released = lambda: self._emit(ControlEvent.RELEASE)

    def _emit(self, event: ControlEvent) -> None:
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._events.put_nowait, event)

    def _stop_led_patterns(self) -> None:
        self._green.off()
        self._red.off()
