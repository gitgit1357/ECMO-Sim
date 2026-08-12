from __future__ import annotations

from collections import deque
import tkinter as tk
from typing import Deque, Iterable, Optional

from .telemetry import MonitorFrame


class DetachableNeonatalMonitor:
    """
    Temporary Tk monitor for development and validation.

    It consumes MonitorFrame objects only. It has no access to the circulation
    model, cannot modify physiology, and can be deleted from a deployment with
    no effect on the engine.
    """

    def __init__(self, frames: Iterable[MonitorFrame], playback_speed: float = 1.0) -> None:
        self._frames = iter(frames)
        self.playback_speed = max(float(playback_speed), 0.1)
        self.root = tk.Tk()
        self.root.title("Standalone Neonatal Circulation Monitor")
        self.root.geometry("980x620")
        self.root.configure(bg="#101418")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.running = True
        self.current: Optional[MonitorFrame] = None
        self._last_time: Optional[float] = None
        self.aortic_trace: Deque[float] = deque(maxlen=600)
        self.pa_trace: Deque[float] = deque(maxlen=600)
        self._build()

    def _build(self) -> None:
        header = tk.Label(
            self.root,
            text="NORMAL TERM NEONATE • INDEPENDENT ENGINE",
            fg="#d7e2ea",
            bg="#101418",
            font=("Arial", 16, "bold"),
        )
        header.pack(pady=(12, 4))

        cards = tk.Frame(self.root, bg="#101418")
        cards.pack(fill="x", padx=20)
        self.labels = {}
        for key, title in [
            ("heart_rate_bpm", "HR"),
            ("arterial", "ARTERIAL"),
            ("map", "MAP"),
            ("native_output_ml_min", "NATIVE CO"),
            ("pulmonary_pressure_mmhg", "PA"),
            ("right_atrial_pressure_mmhg", "CVP"),
        ]:
            card = tk.Frame(cards, bg="#182128", bd=1, relief="solid")
            card.pack(side="left", expand=True, fill="both", padx=4, pady=8)
            tk.Label(card, text=title, fg="#91a4b1", bg="#182128", font=("Arial", 10, "bold")).pack(pady=(8, 2))
            value = tk.Label(card, text="--", fg="#e7f3f8", bg="#182128", font=("Consolas", 20, "bold"))
            value.pack(pady=(0, 8))
            self.labels[key] = value

        self.canvas = tk.Canvas(self.root, bg="#070a0c", highlightthickness=0, height=390)
        self.canvas.pack(fill="both", expand=True, padx=20, pady=10)

        footer = tk.Label(
            self.root,
            text="DISPLAY-ONLY ADAPTER • numeric tiles: rolling 15-second average • waveforms: real-time",
            fg="#71838e",
            bg="#101418",
            font=("Arial", 9),
        )
        footer.pack(pady=(0, 10))

    def close(self) -> None:
        self.running = False
        self.root.destroy()

    def _draw_trace(self, values: Deque[float], y_top: float, y_bottom: float, min_v: float, max_v: float) -> None:
        if len(values) < 2:
            return
        width = max(self.canvas.winfo_width(), 100)
        span = max(max_v - min_v, 1e-6)
        points = []
        for i, value in enumerate(values):
            x = i * width / max(values.maxlen - 1, 1)
            normalized = (value - min_v) / span
            y = y_bottom - normalized * (y_bottom - y_top)
            points.extend((x, y))
        self.canvas.create_line(*points, fill="#d9edf7", width=2, smooth=True)

    def _render(self, frame: MonitorFrame) -> None:
        v = frame.values
        ao = v["aortic_pressure_mmhg"]
        pa = v["pulmonary_pressure_mmhg"]
        self.aortic_trace.append(ao)
        self.pa_trace.append(pa)
        systolic = v.get("arterial_systolic_mmhg")
        diastolic = v.get("arterial_diastolic_mmhg")
        map_est = v.get("map_mmhg")

        self.labels["heart_rate_bpm"].config(text=f"{v.get('display_heart_rate_bpm', v['heart_rate_bpm']):.0f}")
        if systolic is None or diastolic is None or map_est is None:
            self.labels["arterial"].config(text="--/--")
            self.labels["map"].config(text="--")
            self.labels["native_output_ml_min"].config(text="--")
            self.labels["pulmonary_pressure_mmhg"].config(text="--")
            self.labels["right_atrial_pressure_mmhg"].config(text="--")
        else:
            self.labels["arterial"].config(text=f"{systolic:.0f}/{diastolic:.0f}")
            self.labels["map"].config(text=f"{map_est:.0f}")
            self.labels["native_output_ml_min"].config(text=f"{v['display_native_output_ml_min']:.0f} mL/m")
            self.labels["pulmonary_pressure_mmhg"].config(text=f"{v['mean_pa_mmhg']:.0f}")
            self.labels["right_atrial_pressure_mmhg"].config(text=f"{v['mean_ra_mmhg']:.1f}")

        self.canvas.delete("all")
        h = max(self.canvas.winfo_height(), 300)
        self.canvas.create_text(12, 15, anchor="w", text="Aortic pressure", fill="#9fb3bf", font=("Arial", 10, "bold"))
        self.canvas.create_text(12, h / 2 + 15, anchor="w", text="Pulmonary artery pressure", fill="#9fb3bf", font=("Arial", 10, "bold"))
        self.canvas.create_line(0, h / 2, self.canvas.winfo_width(), h / 2, fill="#26323a")
        self._draw_trace(self.aortic_trace, 30, h / 2 - 15, 20, 80)
        self._draw_trace(self.pa_trace, h / 2 + 30, h - 15, 0, 40)

    def _advance(self) -> None:
        if not self.running:
            return
        try:
            frame = next(self._frames)
        except StopIteration:
            self.running = False
            return
        self._render(frame)
        if self._last_time is None:
            delay_ms = 5
        else:
            delay_ms = max(1, int(1000.0 * (frame.time_s - self._last_time) / self.playback_speed))
        self._last_time = frame.time_s
        self.root.after(delay_ms, self._advance)

    def run(self) -> None:
        self.root.after(10, self._advance)
        self.root.mainloop()
