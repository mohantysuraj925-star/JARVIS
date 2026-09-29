"""Kivy Android companion for the JARVIS realtime voice WebSocket."""

from __future__ import annotations

import asyncio
import os
import queue
import struct
import threading
import time
from urllib.parse import urlsplit

import websockets
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


DEFAULT_WS_URL = "wss://your-host.example/mobile/ws"
SAMPLE_RATE = 16_000
WIRE_SAMPLE_RATE = 8_000
FRAME_MS = 40
FRAME_SAMPLES = WIRE_SAMPLE_RATE * FRAME_MS // 1000
MAX_QUEUE_FRAMES = 5

_KV = """
<JarvisRoot>:
    orientation: "vertical"
    padding: "22dp"
    spacing: "14dp"
    canvas.before:
        Color:
            rgba: 0.031, 0.004, 0.012, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "◈  JARVIS BY SURAJ"
        size_hint_y: None
        height: "52dp"
        color: 1, 0.16, 0.29, 1
        font_size: "21sp"
        bold: True
    Label:
        text: "VOICE LINK  /  8 kHz μ-law"
        size_hint_y: None
        height: "30dp"
        color: 1, 0.72, 0.2, 1
    TextInput:
        id: endpoint
        text: root.endpoint
        hint_text: "wss://your-host/mobile/ws"
        multiline: False
        size_hint_y: None
        height: "48dp"
        foreground_color: 1, 0.9, 0.92, 1
        background_color: 0.1, 0.015, 0.035, 1
        cursor_color: 1, 0.16, 0.29, 1
        padding: "12dp", "12dp"
    Label:
        text: root.status
        color: 0.79, 0.49, 0.56, 1
        halign: "left"
        valign: "top"
        text_size: self.size
    Widget:
    Button:
        text: "STOP VOICE LINK" if root.connected else "CONNECT & TALK"
        size_hint_y: None
        height: "58dp"
        background_normal: ""
        background_color: (0.63, 0.075, 0.16, 1) if root.connected else (1, 0.17, 0.29, 1)
        color: 1, 0.9, 0.92, 1
        bold: True
        on_release: root.toggle_link(endpoint.text)
    Label:
        text: "Audio is sent as 40 ms μ-law frames (about 8 KB/s)."
        size_hint_y: None
        height: "30dp"
        color: 0.54, 0.3, 0.36, 1
        font_size: "12sp"
"""


def _validate_ws_url(value: str) -> str:
    endpoint = value.strip()
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"ws", "wss"} or not parsed.hostname:
        raise ValueError("Enter a complete ws:// or wss:// server URL.")
    if parsed.scheme == "ws" and parsed.hostname not in {
        "localhost", "127.0.0.1", "::1",
    }:
        raise ValueError("Use wss:// for non-local servers.")
    return endpoint


def _mulaw_sample(sample: int) -> int:
    """Encode one signed 16-bit PCM sample into an 8-bit G.711 μ-law byte."""
    sample = max(-32768, min(32767, sample))
    sign = 0x80 if sample < 0 else 0
    magnitude = min(abs(sample), 32635) + 132
    exponent = 7
    mask = 0x4000
    while exponent > 0 and not (magnitude & mask):
        exponent -= 1
        mask >>= 1
    mantissa = (magnitude >> (exponent + 3)) & 0x0F
    return (~(sign | (exponent << 4) | mantissa)) & 0xFF


def encode_audio_frame(pcm16: bytes, sequence: int) -> bytes:
    """Downsample 16 kHz mono PCM and pack sequence + 320 μ-law samples.

    Binary wire format: uint16 little-endian sequence, then 320 μ-law bytes.
    Each frame represents 40 ms, so the audio payload is 8 KB/s.
    """
    usable = len(pcm16) - (len(pcm16) % 2)
    samples = struct.unpack(f"<{usable // 2}h", pcm16[:usable]) if usable else ()
    downsampled = samples[::2][:FRAME_SAMPLES]
    if len(downsampled) < FRAME_SAMPLES:
        downsampled = downsampled + (0,) * (FRAME_SAMPLES - len(downsampled))
    payload = bytes(_mulaw_sample(sample) for sample in downsampled)
    return struct.pack("<H", sequence & 0xFFFF) + payload


class AndroidAudioCapture:
    """Capture 16 kHz mono PCM using Android AudioRecord through pyjnius."""

    def __init__(self, output: queue.Queue[bytes]) -> None:
        self._output = output
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._capture, name="jarvis-android-audio", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _capture(self) -> None:
        try:
            from jnius import autoclass

            AudioRecord = autoclass("android.media.AudioRecord")
            AudioFormat = autoclass("android.media.AudioFormat")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            buffer_size = max(
                AudioRecord.getMinBufferSize(
                    SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                ),
                SAMPLE_RATE // 2,
            )
            recorder = AudioRecord(
                AudioSource.MIC,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                buffer_size,
            )
            if recorder.getState() != AudioRecord.STATE_INITIALIZED:
                raise RuntimeError("Android could not initialize the microphone.")
            recorder.startRecording()
            sequence = 0
            read_buffer = bytearray(FRAME_SAMPLES * 4)
            samples_per_read = len(read_buffer) // 2
            try:
                while not self._stop.is_set():
                    count = recorder.read(read_buffer, 0, len(read_buffer))
                    if count <= 0:
                        raise RuntimeError(f"AudioRecord.read failed ({count}).")
                    pcm = bytes(read_buffer[:count])
                    frame = encode_audio_frame(pcm, sequence)
                    sequence += 1
                    try:
                        self._output.put_nowait(frame)
                    except queue.Full:
                        try:
                            self._output.get_nowait()
                        except queue.Empty:
                            pass
                        self._output.put_nowait(frame)
                    expected_seconds = samples_per_read / SAMPLE_RATE
                    if expected_seconds > FRAME_MS / 1000:
                        time.sleep(0.001)
            finally:
                recorder.stop()
                recorder.release()
        except Exception as exc:
            app = App.get_running_app()
            if app is not None and app.root is not None:
                app.root._schedule_status(f"Microphone error: {exc}")


class JarvisRoot(BoxLayout):
    endpoint = StringProperty(
        os.environ.get("JARVIS_MOBILE_WS_URL", DEFAULT_WS_URL)
    )
    status = StringProperty("Set your deployed WSS endpoint to connect.")
    connected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stop_event = threading.Event()
        self._audio_queue: queue.Queue[bytes] = queue.Queue(MAX_QUEUE_FRAMES)
        self._network_thread: threading.Thread | None = None
        self._network_loop: asyncio.AbstractEventLoop | None = None
        self._websocket = None
        self._capture: AndroidAudioCapture | None = None

    def set_status(self, value: str) -> None:
        self.status = value

    def toggle_link(self, endpoint: str) -> None:
        if self.connected:
            self.disconnect()
            return
        try:
            self.endpoint = _validate_ws_url(endpoint)
        except ValueError as exc:
            self.status = str(exc)
            return

        if "your-host.example" in self.endpoint:
            self.status = "Configure JARVIS_MOBILE_WS_URL with your server address."
            return

        try:
            from android.permissions import Permission, request_permissions

            request_permissions(
                [Permission.INTERNET, Permission.RECORD_AUDIO],
                self._on_permissions,
            )
        except ImportError:
            self.status = "Microphone permissions are available only in the Android APK."

    def _on_permissions(self, _permissions, grants) -> None:
        if not grants or not all(grants):
            Clock.schedule_once(
                lambda _dt: self.set_status("Microphone permission is required."),
                0,
            )
            return
        Clock.schedule_once(lambda _dt: self.connect(), 0)

    def connect(self) -> None:
        if self._network_thread and self._network_thread.is_alive():
            return
        self._stop_event.clear()
        self._audio_queue = queue.Queue(MAX_QUEUE_FRAMES)
        self._capture = AndroidAudioCapture(self._audio_queue)
        self._capture.start()
        self._network_thread = threading.Thread(
            target=self._network_worker, name="jarvis-mobile-websocket", daemon=True
        )
        self._network_thread.start()
        self.status = "Connecting to JARVIS voice service…"

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._capture is not None:
            self._capture.stop()
            self._capture = None
        if self._network_loop and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(
                self._websocket.close(), self._network_loop
            )
        self.connected = False
        self.status = "Voice link stopped."

    def _network_worker(self) -> None:
        loop = asyncio.new_event_loop()
        self._network_loop = loop
        try:
            loop.run_until_complete(self._network_session())
        except Exception as exc:
            self._schedule_status(f"Voice connection stopped: {exc}")
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            self._network_loop = None
            self._websocket = None
            Clock.schedule_once(lambda _dt: setattr(self, "connected", False), 0)

    async def _network_session(self) -> None:
        reconnect_delay = 1
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(
                    self.endpoint,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=64 * 1024,
                    max_queue=4,
                    compression=None,
                    open_timeout=10,
                ) as websocket:
                    self._websocket = websocket
                    Clock.schedule_once(
                        lambda _dt: setattr(self, "connected", True), 0
                    )
                    self._schedule_status("Connected · voice stream is live.")
                    reconnect_delay = 1
                    sender = asyncio.create_task(self._send_audio(websocket))
                    try:
                        async for message in websocket:
                            if isinstance(message, str):
                                self._schedule_status(message[:1000])
                    finally:
                        sender.cancel()
                        await asyncio.gather(sender, return_exceptions=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                if not self._stop_event.is_set():
                    self._schedule_status(
                        f"Connection issue: {exc}. Retrying in {reconnect_delay}s."
                    )
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(30, reconnect_delay * 2)
        self.connected = False

    async def _send_audio(self, websocket) -> None:
        while not self._stop_event.is_set():
            try:
                frame = await asyncio.to_thread(
                    self._audio_queue.get, True, 0.25
                )
            except queue.Empty:
                continue
            await websocket.send(frame)

    def _schedule_status(self, value: str) -> None:
        Clock.schedule_once(lambda _dt, text=value: self.set_status(text), 0)


class JarvisMobileApp(App):
    def build(self):
        self.title = "JARVIS by Suraj"
        Builder.load_string(_KV)
        return JarvisRoot()

    def on_stop(self):
        if self.root is not None:
            self.root.disconnect()


if __name__ == "__main__":
    JarvisMobileApp().run()
