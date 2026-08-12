from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import math
import tkinter as tk
from tkinter import ttk
from typing import Optional

from neoecmo import EcmoConsoleControls, EcmoConsoleState, ShuntLineConfiguration, run_ecmo_console
from neoecmocoupling import (
    CoupledVaEcmoPatient,
    DynamicCoupledSnapshot,
    DynamicCoupledVaEcmoPatient,
)
from neopatient import AirwayPort, UnifiedNeonatalPatient, UnifiedPatientConfig
from neoventilator import PressureControlSettings
from neoevents import EventRecord, EventStream
from neolabs import LabQueue, LabResult
from .ux_policy import (
    SIMULATOR_ADVISORY_LABEL,
    ecmo_shortcut_allowed,
    physiology_latency_text,
)


@dataclass(frozen=True)
class WorkspaceInputs:
    """Learner-adjustable controls represented by the current ECMO console."""

    pump_running: bool = False
    commanded_rpm: float = 3000.0
    bridge_clamp_position: float = 0.0
    shunt_configuration: ShuntLineConfiguration = ShuntLineConfiguration.OPEN
    shunt_scuffing_active: bool = False
    shunt_ckrt_blood_flow_ml_min: float = 0.0
    shunt_ckrt_net_ultrafiltration_rate_ml_min: float = 0.0
    fdo2: float = 1.0
    sweep_gas_flow_ml_min: float = 600.0
    native_venous_saturation: float = 0.65
    native_venous_paco2_mmhg: float = 55.0


@dataclass(frozen=True)
class WorkspaceSnapshot:
    inputs: WorkspaceInputs
    state: EcmoConsoleState
    dynamic: DynamicCoupledSnapshot

    @property
    def coupled_state(self) -> EcmoConsoleState:
        return self.dynamic.true.volume_limited_ecmo.closed_loop.ecmo_state

    @property
    def applied_rpm(self) -> float:
        return self.coupled_state.circuit.rpm

    @property
    def status_text(self) -> str:
        return "RUNNING" if self.inputs.pump_running and self.applied_rpm > 0.0 else "STOPPED"


class EcmoWorkspaceModel:
    """GUI adapter for the time-stepped coupled neonatal patient and VA-ECMO circuit."""

    def __init__(self, inputs: WorkspaceInputs = WorkspaceInputs()) -> None:
        self.inputs = inputs
        patient = UnifiedNeonatalPatient(
            UnifiedPatientConfig(weight_kg=3.0, lung_run_s=1.0, circulation_run_s=1.0, native_physiology_async=True, native_physiology_executor="process")
        )
        coupled = CoupledVaEcmoPatient(patient, self._controls())
        self.dynamic = DynamicCoupledVaEcmoPatient(coupled)
        self.events = EventStream()
        self.labs = LabQueue()
        self._reported_lab_result_ids: set[str] = set()
        self.events.emit(
            event_type="system.lifecycle",
            source="system",
            target="ecmo_workspace",
            action="initialized",
            new_value={"pump_running": inputs.pump_running, "commanded_rpm": inputs.commanded_rpm},
            metadata={"simulation_time_s": 0.0},
        )

    def _controls(self) -> EcmoConsoleControls:
        applied_rpm = self.inputs.commanded_rpm if self.inputs.pump_running else 0.0
        return EcmoConsoleControls(
            rpm=max(0.0, applied_rpm),
            bridge_clamp_position=min(max(self.inputs.bridge_clamp_position, 0.0), 1.0),
            bridge_target_flow_ml_min=None,
            shunt_configuration=self.inputs.shunt_configuration,
            shunt_scuffing_active=self.inputs.shunt_scuffing_active,
            shunt_ckrt_blood_flow_ml_min=max(0.0, self.inputs.shunt_ckrt_blood_flow_ml_min),
            shunt_ckrt_net_ultrafiltration_rate_ml_min=max(0.0, self.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min),
            fdo2=min(max(self.inputs.fdo2, 0.21), 1.0),
            sweep_gas_flow_ml_min=max(0.0, self.inputs.sweep_gas_flow_ml_min),
        )

    @staticmethod
    def _workspace_snapshot(inputs: WorkspaceInputs, dynamic: DynamicCoupledSnapshot) -> WorkspaceSnapshot:
        # Preserve the original headless workspace contract for existing benches.
        # The GUI itself reads coupled_state/dynamic for live patient interaction.
        applied_rpm = inputs.commanded_rpm if inputs.pump_running else 0.0
        controls = EcmoConsoleControls(
            rpm=max(0.0, applied_rpm),
            bridge_clamp_position=min(max(inputs.bridge_clamp_position, 0.0), 1.0),
            bridge_target_flow_ml_min=None,
            shunt_configuration=inputs.shunt_configuration,
            shunt_scuffing_active=inputs.shunt_scuffing_active,
            shunt_ckrt_blood_flow_ml_min=max(0.0, inputs.shunt_ckrt_blood_flow_ml_min),
            shunt_ckrt_net_ultrafiltration_rate_ml_min=max(0.0, inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min),
            fdo2=min(max(inputs.fdo2, 0.21), 1.0),
            sweep_gas_flow_ml_min=max(0.0, inputs.sweep_gas_flow_ml_min),
        )
        state = run_ecmo_console(
            controls,
            native_venous_saturation=min(max(inputs.native_venous_saturation, 0.0), 1.0),
            native_venous_paco2_mmhg=max(0.0, inputs.native_venous_paco2_mmhg),
        )
        return WorkspaceSnapshot(inputs=inputs, state=state, dynamic=dynamic)

    def update(self, *, event_source: str = "learner", **changes: object) -> WorkspaceSnapshot:
        old_inputs = self.inputs
        self.inputs = replace(self.inputs, **changes)
        self.dynamic.set_controls(self._controls())
        snapshot = self.solve()
        simulation_time_s = float(snapshot.dynamic.elapsed_s)
        for field_name, requested_value in changes.items():
            old_value = getattr(old_inputs, field_name)
            new_value = getattr(self.inputs, field_name)
            if old_value == new_value:
                continue
            if isinstance(old_value, ShuntLineConfiguration):
                old_value = old_value.value
            if isinstance(new_value, ShuntLineConfiguration):
                new_value = new_value.value
            self.events.emit(
                event_type="control.changed",
                source=event_source,
                target="ecmo_console",
                action=f"set_{field_name}",
                old_value=old_value,
                new_value=new_value,
                metadata={"simulation_time_s": simulation_time_s},
            )
        return snapshot

    def solve(self) -> WorkspaceSnapshot:
        return self._workspace_snapshot(self.inputs, self.dynamic.snapshot())

    def _report_new_lab_results(self, snapshot: WorkspaceSnapshot) -> None:
        now = float(snapshot.dynamic.elapsed_s)
        for result in self.labs.available(now):
            if result.result_id in self._reported_lab_result_ids:
                continue
            self._reported_lab_result_ids.add(result.result_id)
            self.events.emit(
                event_type="diagnostic.result_available",
                source="system",
                target="labs",
                action="result_available",
                new_value={"result_id": result.result_id, "panel_id": result.panel_id},
                metadata={
                    "simulation_time_s": now,
                    "sample_time_s": result.sample_time_s,
                    "available_time_s": result.available_time_s,
                    "sample_site": result.sample_site,
                },
            )

    def advance(self, dt_s: float) -> WorkspaceSnapshot:
        # Native physiology is an equilibrium update, not N seconds of
        # evolution. While a recalculation is required/in flight, keep the
        # GUI and circuit responsive but do not advance simulation time on a
        # stale native state. A zero-time snapshot polls/commits worker results.
        patient = self.dynamic.coupled.patient
        applied_dt_s = 0.0 if patient.native_physiology_update_pending else dt_s
        snapshot = self._workspace_snapshot(self.inputs, self.dynamic.advance(applied_dt_s))
        self._report_new_lab_results(snapshot)
        return snapshot

    def order_diagnostic(
        self,
        panel_id: str,
        *,
        turnaround_s: float = 30.0,
        event_source: str = "learner",
    ) -> LabResult:
        """Collect a frozen diagnostic sample from authoritative current state.

        Phase 2c rejects collection while native physiology is pending rather
        than silently freezing a stale last-known patient state.  The default
        turnaround is an orchestration placeholder, not a clinical lab SLA.
        """
        if self.native_physiology_update_pending:
            raise RuntimeError("native physiology is updating; wait for a current state before collecting a diagnostic sample")
        if not math.isfinite(float(turnaround_s)) or float(turnaround_s) < 0.0:
            raise ValueError("turnaround_s must be finite and non-negative")
        snapshot = self.solve()
        sample_time_s = float(snapshot.dynamic.elapsed_s)
        patient = snapshot.dynamic.true.patient
        if panel_id == "patient_arterial_gas":
            panel_name = "Patient arterial gas (partial)"
            site = "patient_arterial"
            values = {
                "pao2_mmhg": float(patient.pao2_mmhg),
                "paco2_mmhg": float(patient.paco2_mmhg),
                "sao2_pct": float(patient.sao2_pct),
            }
            units = {"pao2_mmhg": "mmHg", "paco2_mmhg": "mmHg", "sao2_pct": "%"}
            metadata = {
                "missing_analytes": ["pH", "HCO3", "base_excess", "lactate"],
                "validation_status": "partial_authoritative_state",
            }
        elif panel_id == "post_oxygenator_gas":
            panel_name = "Post-oxygenator gas assessment"
            site = "ecmo_post_oxygenator"
            state = snapshot.coupled_state
            values = {
                "po2_mmhg": float(state.post_oxygenator_po2_mmhg),
                "pco2_mmhg": float(state.post_oxygenator_paco2_mmhg),
                "o2_saturation_pct": float(state.post_oxygenator_saturation * 100.0),
            }
            units = {"po2_mmhg": "mmHg", "pco2_mmhg": "mmHg", "o2_saturation_pct": "%"}
            metadata = {"validation_status": "model_output_not_device_validated"}
        else:
            raise KeyError(f"unsupported diagnostic panel: {panel_id}")
        result = self.labs.order(
            panel_id=panel_id, panel_name=panel_name, sample_site=site,
            sample_time_s=sample_time_s, turnaround_s=float(turnaround_s),
            values=values, units=units, metadata=metadata,
        )
        self.events.emit(
            event_type="diagnostic.ordered",
            source=event_source,
            target="labs",
            action="collect_sample",
            new_value={"result_id": result.result_id, "panel_id": panel_id},
            metadata={
                "simulation_time_s": sample_time_s,
                "sample_time_s": result.sample_time_s,
                "available_time_s": result.available_time_s,
                "sample_site": result.sample_site,
                "turnaround_status": "simulation_placeholder",
            },
        )
        if result.is_available(sample_time_s):
            self._report_new_lab_results(snapshot)
        return result

    @property
    def lab_results(self) -> tuple[LabResult, ...]:
        return self.labs.results

    def apply_intravascular_volume(
        self,
        volume_ml: float,
        *,
        intravascular_fraction: float = 1.0,
        event_source: str = "learner",
    ) -> WorkspaceSnapshot:
        """Apply a learner volume intervention through the patient mechanism.

        Phase 2b intentionally exposes generic intravascular input rather than
        claiming a blood-product or crystalloid formulation that the backend
        does not yet model.
        """
        volume_ml = float(volume_ml)
        if not math.isfinite(volume_ml) or volume_ml <= 0.0:
            raise ValueError("volume_ml must be a finite value greater than zero")
        fraction = float(intravascular_fraction)
        if not math.isfinite(fraction) or not 0.0 <= fraction <= 1.0:
            raise ValueError("intravascular_fraction must be between 0 and 1")
        patient = self.dynamic.coupled.patient
        before = patient.snapshot()
        patient.add_intravascular_input(volume_ml, intravascular_fraction=fraction)
        snapshot = self.solve()
        after = patient.snapshot()
        self.events.emit(
            event_type="intervention.applied",
            source=event_source,
            target="patient",
            action="add_intravascular_volume",
            old_value={"blood_volume_fraction": before.blood_volume_fraction},
            new_value={"blood_volume_fraction": after.blood_volume_fraction},
            metadata={
                "simulation_time_s": float(snapshot.dynamic.elapsed_s),
                "mechanism_id": "patient.add_intravascular_input",
                "volume_ml": volume_ml,
                "intravascular_fraction": fraction,
            },
        )
        return snapshot

    def apply_ckrt_prescription(
        self,
        *,
        blood_flow_ml_min: float,
        net_ultrafiltration_rate_ml_min: float,
        event_source: str = "learner",
    ) -> WorkspaceSnapshot:
        """Store CKRT blood-flow/net-UF controls on the ECMO circuit.

        The existing coupled backend gates patient fluid removal on CKRT being
        selected in the shunt AND blood flow being greater than zero. This UI
        method does not bypass that activation rule.
        """
        blood_flow = float(blood_flow_ml_min)
        net_uf = float(net_ultrafiltration_rate_ml_min)
        if not math.isfinite(blood_flow) or blood_flow < 0.0:
            raise ValueError("blood_flow_ml_min must be finite and non-negative")
        if not math.isfinite(net_uf) or net_uf < 0.0:
            raise ValueError("net_ultrafiltration_rate_ml_min must be finite and non-negative")
        old = {
            "blood_flow_ml_min": self.inputs.shunt_ckrt_blood_flow_ml_min,
            "net_ultrafiltration_rate_ml_min": self.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min,
        }
        snapshot = self.update(
            event_source=event_source,
            shunt_ckrt_blood_flow_ml_min=blood_flow,
            shunt_ckrt_net_ultrafiltration_rate_ml_min=net_uf,
        )
        active = (
            snapshot.inputs.shunt_configuration == ShuntLineConfiguration.CKRT
            and blood_flow > 0.0
        )
        self.events.emit(
            event_type="intervention.applied",
            source=event_source,
            target="ckrt",
            action="set_ckrt_prescription",
            old_value=old,
            new_value={
                "blood_flow_ml_min": blood_flow,
                "net_ultrafiltration_rate_ml_min": net_uf,
            },
            metadata={
                "simulation_time_s": float(snapshot.dynamic.elapsed_s),
                "mechanism_id": "ecmo.ckrt_prescription",
                "active": active,
                "activation_requires": "shunt_configuration=CKRT and blood_flow_ml_min>0",
            },
        )
        return snapshot

    def apply_pressure_control_ventilator(
        self,
        settings: PressureControlSettings,
        *,
        event_source: str = "learner",
    ) -> WorkspaceSnapshot:
        patient = self.dynamic.coupled.patient
        old_airway = patient.airway
        patient.set_airway(replace(old_airway, fio2=settings.fio2, pressure_control=settings))
        snapshot = self.solve()
        self.events.emit(
            event_type="control.changed",
            source=event_source,
            target="ventilator",
            action="apply_pressure_control",
            old_value=self._airway_event_value(old_airway),
            new_value=self._airway_event_value(patient.airway),
            metadata={
                "simulation_time_s": float(snapshot.dynamic.elapsed_s),
                "mechanism_id": "airway.pressure_control",
                "validation_status": "reduced_order_pressure_control",
            },
        )
        return snapshot

    def remove_pressure_control_ventilator(self, *, event_source: str = "learner") -> WorkspaceSnapshot:
        patient = self.dynamic.coupled.patient
        old_airway = patient.airway
        patient.set_airway(replace(old_airway, pressure_control=None))
        snapshot = self.solve()
        if old_airway.pressure_control is not None:
            self.events.emit(
                event_type="control.changed",
                source=event_source,
                target="ventilator",
                action="remove_pressure_control",
                old_value=self._airway_event_value(old_airway),
                new_value=self._airway_event_value(patient.airway),
                metadata={
                    "simulation_time_s": float(snapshot.dynamic.elapsed_s),
                    "mechanism_id": "airway.pressure_control",
                },
            )
        return snapshot

    @staticmethod
    def _airway_event_value(airway: AirwayPort) -> dict[str, object]:
        pc = airway.pressure_control
        if pc is None:
            return {
                "mode": "native",
                "peep_cmh2o": airway.peep_cmh2o,
                "airway_opening_pressure_cmh2o": airway.airway_opening_pressure_cmh2o,
                "fio2": airway.fio2,
            }
        return {
            "mode": "pressure_control",
            "pip_cmh2o": pc.pip_cmh2o,
            "peep_cmh2o": pc.peep_cmh2o,
            "rate_bpm": pc.rate_bpm,
            "inspiratory_time_s": pc.inspiratory_time_s,
            "fio2": pc.fio2,
        }

    @property
    def ventilator_settings(self) -> PressureControlSettings | None:
        return self.dynamic.coupled.patient.airway.pressure_control

    @property
    def event_records(self) -> tuple[EventRecord, ...]:
        return self.events.records

    def record_event(
        self,
        *,
        event_type: str,
        source: str,
        target: str,
        action: str,
        old_value: object = None,
        new_value: object = None,
        revision: int | None = None,
        metadata: Optional[dict[str, object]] = None,
    ) -> EventRecord:
        event_metadata = dict(metadata or {})
        event_metadata.setdefault("simulation_time_s", float(self.dynamic.elapsed_s))
        return self.events.emit(
            event_type=event_type, source=source, target=target, action=action,
            old_value=old_value, new_value=new_value, revision=revision, metadata=event_metadata,
        )

    @property
    def native_physiology_update_pending(self) -> bool:
        return self.dynamic.coupled.patient.native_physiology_update_pending

    def close(self) -> None:
        self.dynamic.coupled.patient.shutdown()


class TelemetryTile(tk.Frame):
    def __init__(self, parent: tk.Misc, label: str, *, accent: str = "#5bd5e8") -> None:
        super().__init__(parent, bg="#101a20", highlightbackground="#33434d", highlightthickness=1)
        tk.Label(self, text=label, bg="#101a20", fg="#94a8b2", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        self.value = tk.Label(self, text="--", bg="#101a20", fg=accent, font=("Consolas", 17, "bold"))
        self.value.pack(anchor="w", padx=10, pady=(2, 9))

    def set(self, text: str) -> None:
        self.value.configure(text=text)


class EcmoWorkspace:
    """Tabbed learner workspace with a compact, console-inspired ECMO page."""

    POSITIONING_LABEL = "SIMULATION / TRAINING ONLY"

    BG = "#070c10"
    SCREEN = "#0a1217"
    SCREEN_2 = "#101a20"
    TEXT = "#eef8fb"
    MUTED = "#91a7b1"
    CYAN = "#51d6e8"
    BLUE = "#4b8fff"
    GREEN = "#55dc98"
    YELLOW = "#f0d84d"
    RED = "#ff6565"
    ORANGE = "#ff985c"
    BEZEL = "#9da4a7"
    NAV = "#d7dbdd"
    NAV_ACTIVE = "#176ad1"
    CONTROL = "#1a262d"

    def __init__(self, model: Optional[EcmoWorkspaceModel] = None) -> None:
        self.model = model or EcmoWorkspaceModel()
        self.root = tk.Tk()
        self.root.title("Neonatal ECMO Learner Workspace")
        self.root.geometry("1440x900")
        self.root.minsize(1080, 680)
        self.root.configure(bg=self.BG)
        self._last_snapshot: Optional[WorkspaceSnapshot] = None
        self._known_available_lab_result_ids: set[str] = set()
        self._unread_lab_result_ids: set[str] = set()
        from .patient_monitor import learner_patient_reading
        self._learner_patient_project = learner_patient_reading
        self._configure_styles()
        self._build_header()
        self._build_status_ribbon()
        self._build_body()
        self._build_event_strip()
        self._bind_shortcuts()
        self.root.bind("<Configure>", self._on_workspace_resize, add="+")
        self._apply_snapshot(self.model.solve(), log_action=False)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._schedule_refresh()

    def _on_workspace_resize(self, event) -> None:
        """Adjust presentation density only; never simulation/model state."""
        if event.widget is not self.root or not hasattr(self, "nav"):
            return
        compact = event.width < 1240
        nav_width = 112 if compact else 132
        wraplength = 92 if compact else 108
        self.nav.configure(width=nav_width)
        for button in self.nav_buttons.values():
            button.configure(wraplength=wraplength)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Console.TButton", font=("Segoe UI", 7, "bold"), padding=(4, 2))
        style.configure("Compact.TButton", font=("Segoe UI", 7, "bold"), padding=(2, 1))
        style.configure("TCombobox", fieldbackground="#e7eaeb", foreground="#172127")

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=self.BG, padx=18, pady=9)
        header.pack(fill="x")
        tk.Label(header, text="NEONATAL ECMO LEARNER WORKSTATION", bg=self.BG, fg=self.TEXT, font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(header, text=self.POSITIONING_LABEL, bg="#23303a", fg=self.MUTED, padx=10, pady=3, font=("Segoe UI", 8, "bold")).pack(side="left", padx=14)
        self.header_status = tk.Label(header, text="STOPPED", bg="#402020", fg=self.RED, padx=12, pady=4, font=("Segoe UI", 10, "bold"))
        self.header_status.pack(side="right")
        self.header_compute_status = tk.Label(
            header, text="", bg="#493b13", fg=self.YELLOW, padx=10, pady=3,
            font=("Segoe UI", 8, "bold"),
        )
        self.header_compute_status.pack(side="right", padx=(0, 8))

    def _build_status_ribbon(self) -> None:
        """Persistent learner-state ribbon sourced only from learner_patient_reading."""
        ribbon = tk.Frame(self.root, bg="#0d171d", padx=18, pady=6, highlightbackground="#263840", highlightthickness=1)
        ribbon.pack(fill="x", padx=14, pady=(0, 6))
        self.status_ribbon_frame = ribbon
        self.status_ribbon_labels: dict[str, tk.Label] = {}
        specs = [
            ("map", "MAP", self.ORANGE),
            ("spo2", "SpO₂", self.GREEN),
            ("ecmo_flow", "ECMO PATIENT FLOW", self.YELLOW),
        ]
        for key, label, color in specs:
            box = tk.Frame(ribbon, bg="#0d171d")
            box.pack(side="left", padx=(0, 28))
            tk.Label(box, text=label, bg="#0d171d", fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
            value = tk.Label(box, text="--", bg="#0d171d", fg=color, font=("Consolas", 11, "bold"))
            value.pack(side="left", padx=(7, 0))
            self.status_ribbon_labels[key] = value
        self.ribbon_compute_status = tk.Label(
            ribbon, text="CURRENT", bg="#17372b", fg=self.GREEN, padx=8, pady=2, font=("Segoe UI", 7, "bold")
        )
        self.ribbon_compute_status.pack(side="right")

    def _build_body(self) -> None:
        shell = tk.Frame(self.root, bg=self.BEZEL, padx=7, pady=7)
        shell.pack(fill="both", expand=True, padx=14)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        self.nav = tk.Frame(shell, bg=self.NAV, width=132)
        self.nav.grid(row=0, column=0, sticky="nsw")
        self.nav.grid_propagate(False)

        self.pages = tk.Frame(shell, bg=self.SCREEN)
        self.pages.grid(row=0, column=1, sticky="nsew")
        self.pages.rowconfigure(0, weight=1)
        self.pages.columnconfigure(0, weight=1)

        self.page_frames: dict[str, tk.Frame] = {}
        page_specs = [
            ("ECMO", "ECMO Console"),
            ("MON", "Patient Monitor"),
            ("VENT", "Ventilator"),
            ("LABS", "Labs & Diagnostics"),
            ("ACT", "Interventions"),
            ("LOG", "Debrief"),
        ]
        self.nav_buttons: dict[str, tk.Button] = {}
        self._nav_base_labels = dict(page_specs)
        for index, (key, label) in enumerate(page_specs):
            btn = tk.Button(
                self.nav,
                text=label,
                command=lambda k=key: self._show_page(k),
                bg=self.NAV_ACTIVE if index == 0 else self.NAV,
                fg="white" if index == 0 else "#3d4a50",
                activebackground="#4387dc",
                activeforeground="white",
                relief="flat",
                bd=0,
                wraplength=108,
                font=("Segoe UI", 9, "bold"),
                padx=8,
                pady=12,
            )
            btn.pack(fill="x", padx=6, pady=(7 if index == 0 else 2, 0))
            self.nav_buttons[key] = btn

        tk.Frame(self.nav, bg="#8f989c", height=1).pack(fill="x", padx=8, pady=8)
        self.nav_runtime = tk.Label(self.nav, text="ECMO\n00:00", bg=self.NAV, fg="#37566b", font=("Consolas", 11, "bold"))
        self.nav_runtime.pack(fill="x", pady=4)
        tk.Label(self.nav, text="POWER", bg=self.NAV, fg="#506068", font=("Segoe UI", 7, "bold")).pack(pady=(14, 2))
        tk.Label(self.nav, text="100%", bg="#4ebf69", fg="white", padx=14, pady=5, font=("Consolas", 10, "bold")).pack()

        console = tk.Frame(self.pages, bg=self.SCREEN)
        console.grid(row=0, column=0, sticky="nsew")
        self.page_frames["ECMO"] = console
        self._build_console_page(console)

        monitor = tk.Frame(self.pages, bg=self.SCREEN)
        monitor.grid(row=0, column=0, sticky="nsew")
        self.page_frames["MON"] = monitor
        self._build_patient_monitor_page(monitor)

        interventions = tk.Frame(self.pages, bg=self.SCREEN)
        interventions.grid(row=0, column=0, sticky="nsew")
        self.page_frames["ACT"] = interventions
        self._build_interventions_page(interventions)

        labs = tk.Frame(self.pages, bg=self.SCREEN)
        labs.grid(row=0, column=0, sticky="nsew")
        self.page_frames["LABS"] = labs
        self._build_labs_page(labs)

        ventilator = tk.Frame(self.pages, bg=self.SCREEN)
        ventilator.grid(row=0, column=0, sticky="nsew")
        self.page_frames["VENT"] = ventilator
        self._build_ventilator_page(ventilator)

        log_page = tk.Frame(self.pages, bg=self.SCREEN)
        log_page.grid(row=0, column=0, sticky="nsew")
        self.page_frames["LOG"] = log_page
        self._build_scenario_log_page(log_page)

        self._show_page("ECMO")

    def _show_page(self, key: str) -> None:
        self._active_page_key = key
        self.page_frames[key].tkraise()
        if key == "LABS" and hasattr(self, "lab_results_text"):
            self._refresh_lab_results(self._last_snapshot or self.model.solve())
        for button_key, button in self.nav_buttons.items():
            active = button_key == key
            button.configure(bg=self.NAV_ACTIVE if active else self.NAV, fg="white" if active else "#3d4a50")
        if self._last_snapshot is not None:
            self._refresh_nav_attention(self._last_snapshot)

    def _build_scenario_log_page(self, parent: tk.Frame) -> None:
        from .scenario_log import debrief_entries

        self._scenario_log_project = debrief_entries
        self._scenario_log_source_count = -1
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)
        title.grid(row=0, column=0, sticky="ew")
        tk.Label(title, text="DEBRIEF — EVENT TIMELINE", bg=self.SCREEN, fg=self.TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(
            title, text="LEARNER VIEW", bg="#17372b", fg=self.GREEN, padx=10, pady=3,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right")

        body = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=4)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)
        tk.Label(
            body,
            text=("Read-only chronological record projected from the canonical immutable event stream. "
                  "It shows recorded learner-visible events only. It does not score performance, infer diagnoses, "
                  "interpret decisions, or replay historical physiology."),
            bg=self.SCREEN, fg=self.MUTED, justify="left", wraplength=1040, font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        table_frame = tk.Frame(body, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        columns = ("time", "type", "source", "target", "action", "detail")
        self.scenario_log_tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "time": "SIM TIME", "type": "EVENT", "source": "SOURCE",
            "target": "TARGET", "action": "ACTION", "detail": "DETAIL",
        }
        widths = {"time": 78, "type": 165, "source": 80, "target": 130, "action": 180, "detail": 410}
        for key in columns:
            self.scenario_log_tree.heading(key, text=headings[key])
            self.scenario_log_tree.column(key, width=widths[key], minwidth=60, anchor="w", stretch=(key == "detail"))
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.scenario_log_tree.yview)
        self.scenario_log_tree.configure(yscrollcommand=scrollbar.set)
        self.scenario_log_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.scenario_log_status = tk.Label(
            body, text="0 debrief events", bg=self.SCREEN, fg=self.MUTED,
            font=("Segoe UI", 8),
        )
        self.scenario_log_status.grid(row=2, column=0, sticky="w", pady=(7, 0))

    def _refresh_scenario_log(self) -> None:
        source_count = len(self.model.event_records)
        if source_count == self._scenario_log_source_count:
            return
        entries = self._scenario_log_project(self.model.event_records)
        self.scenario_log_tree.delete(*self.scenario_log_tree.get_children())
        for entry in entries:
            self.scenario_log_tree.insert(
                "", "end",
                values=(entry.simulation_time_text, entry.event_type, entry.source, entry.target, entry.action, entry.detail),
            )
        self._scenario_log_source_count = source_count
        hidden_count = source_count - len(entries)
        suffix = f" • {hidden_count} internal event{'s' if hidden_count != 1 else ''} withheld" if hidden_count else ""
        self.scenario_log_status.configure(text=f"{len(entries)} debrief event{'s' if len(entries) != 1 else ''}{suffix}")
        children = self.scenario_log_tree.get_children()
        if children:
            self.scenario_log_tree.see(children[-1])

    def _apply_status_ribbon(self, reading) -> None:
        if not hasattr(self, "status_ribbon_labels"):
            return
        self.status_ribbon_labels["map"].configure(text=f"{reading.map_mmhg:.0f} mmHg")
        self.status_ribbon_labels["spo2"].configure(text=f"{reading.spo2_pct:.1f}%")
        self.status_ribbon_labels["ecmo_flow"].configure(text=f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f} L/min")
        if reading.physiology_updating:
            self.ribbon_compute_status.configure(text="PHYSIOLOGY UPDATING • LAST COMMITTED VALUES", bg="#493b13", fg=self.YELLOW)
        else:
            self.ribbon_compute_status.configure(text="CURRENT", bg="#17372b", fg=self.GREEN)

    def _build_patient_monitor_page(self, parent: tk.Frame) -> None:
        self._patient_monitor_project = self._learner_patient_project
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)
        title.grid(row=0, column=0, sticky="ew")
        tk.Label(title, text="PATIENT MONITOR", bg=self.SCREEN, fg=self.TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
        self.monitor_status = tk.Label(title, text="LIVE", bg="#17372b", fg=self.GREEN, padx=10, pady=3, font=("Segoe UI", 8, "bold"))
        self.monitor_status.pack(side="right")

        primary = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=4)
        primary.grid(row=1, column=0, sticky="ew")
        for col in range(6):
            primary.columnconfigure(col, weight=1)
        self.patient_monitor_tiles: dict[str, TelemetryTile] = {}
        specs = [
            ("bp", "ARTERIAL BP", self.ORANGE),
            ("map", "MAP", self.ORANGE),
            ("spo2", "SpO₂", self.GREEN),
            ("cvp", "CVP", self.CYAN),
            ("pao2", "PaO₂", self.GREEN),
            ("paco2", "PaCO₂", self.GREEN),
            ("native_co", "NATIVE CO", self.YELLOW),
            ("ecmo_flow", "ECMO PATIENT FLOW", self.YELLOW),
            ("urine", "URINE OUTPUT", self.CYAN),
            ("fluid", "NET FLUID", self.CYAN),
            ("blood_volume", "BLOOD VOLUME", self.CYAN),
            ("runtime", "SIM TIME", self.MUTED),
        ]
        for index, (key, label, accent) in enumerate(specs):
            tile = TelemetryTile(primary, label, accent=accent)
            tile.grid(row=index // 6, column=index % 6, sticky="nsew", padx=3, pady=3)
            self.patient_monitor_tiles[key] = tile

        details = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=18, pady=14)
        details.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 16))
        tk.Label(details, text="MONITOR CHANNEL STATUS", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(
            details,
            text="Read-only Phase 2a display. Values are projected from the authoritative coupled-patient snapshot; this page contains no physiology or treatment logic.",
            bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=920, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 12))
        self.monitor_channel_note = tk.Label(
            details,
            text="HR: unavailable — unified patient HR is not yet integrated.    Temperature: unavailable — patient temperature state is not yet integrated.    Waveforms: not implemented in Phase 2a.",
            bg=self.SCREEN_2, fg=self.YELLOW, justify="left", wraplength=980, font=("Segoe UI", 9, "bold"),
        )
        self.monitor_channel_note.pack(anchor="w")

    def _apply_patient_monitor_snapshot(self, snapshot: WorkspaceSnapshot, *, reading=None) -> None:
        if not hasattr(self, "patient_monitor_tiles"):
            return
        if reading is None:
            reading = self._patient_monitor_project(
                snapshot, physiology_updating=self.model.native_physiology_update_pending
            )
        elapsed = int(reading.simulation_time_s)
        values = {
            "bp": f"{reading.systolic_mmhg:.0f}/{reading.diastolic_mmhg:.0f}",
            "map": f"{reading.map_mmhg:.0f} mmHg",
            "spo2": f"{reading.spo2_pct:.1f}%",
            "cvp": f"{reading.cvp_mmhg:.1f} mmHg",
            "pao2": f"{reading.pao2_mmhg:.0f} mmHg",
            "paco2": f"{reading.paco2_mmhg:.0f} mmHg",
            "native_co": f"{reading.native_cardiac_output_ml_min:.0f} mL/min",
            "ecmo_flow": f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f} L/min",
            "urine": f"{reading.urine_ml_kg_hr:.2f} mL/kg/h",
            "fluid": f"{reading.net_body_fluid_ml:+.1f} mL",
            "blood_volume": f"{reading.blood_volume_fraction * 100.0:.1f}%",
            "runtime": f"{elapsed // 60:02d}:{elapsed % 60:02d}",
        }
        for key, value in values.items():
            self.patient_monitor_tiles[key].set(value)
        if reading.physiology_updating:
            self.monitor_status.configure(text="UPDATING", bg="#493b13", fg=self.YELLOW)
        else:
            self.monitor_status.configure(text="LIVE", bg="#17372b", fg=self.GREEN)

    def _build_labs_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(3, weight=1)

        title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)
        title.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(title, text="LABS & DIAGNOSTICS", bg=self.SCREEN, fg=self.TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(title, text="PHASE 2c", bg="#17372b", fg=self.GREEN, padx=10, pady=3, font=("Segoe UI", 8, "bold")).pack(side="right")

        patient = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        patient.grid(row=1, column=0, sticky="nsew", padx=(20, 6), pady=6)
        self.patient_lab_order_frame = patient
        tk.Label(patient, text="PATIENT ARTERIAL GAS — PARTIAL", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(patient, text="Freezes PaO₂, PaCO₂, and SaO₂ at collection time. pH, HCO₃⁻, base excess, and lactate are unavailable because the unified patient does not yet own those states.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=430, font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 9))
        ttk.Button(patient, text="ORDER PATIENT GAS", style="Console.TButton", command=lambda: self._order_lab("patient_arterial_gas")).pack(anchor="w")

        postoxy = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        postoxy.grid(row=1, column=1, sticky="nsew", padx=(6, 20), pady=6)
        self.postoxy_lab_order_frame = postoxy
        tk.Label(postoxy, text="POST-OXYGENATOR GAS", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(postoxy, text="Freezes the modeled post-oxygenator PO₂, PCO₂, and O₂ saturation at collection time. These are model outputs and are not device-validated transfer targets.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=430, font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 9))
        ttk.Button(postoxy, text="ORDER POST-OXY GAS", style="Console.TButton", command=lambda: self._order_lab("post_oxygenator_gas")).pack(anchor="w")

        context = tk.Frame(parent, bg="#0d171d", highlightbackground="#33434d", highlightthickness=1, padx=14, pady=8)
        context.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(4, 4))
        self.lab_context_frame = context
        tk.Label(context, text="CURRENT PATIENT CONTEXT", bg="#0d171d", fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(context, text="live context • not a frozen lab value", bg="#0d171d", fg=self.MUTED, font=("Segoe UI", 7, "bold")).pack(side="left", padx=(8, 14))
        self.lab_context_labels: dict[str, tk.Label] = {}
        for key, label, color in [("map", "MAP", self.ORANGE), ("spo2", "SpO₂", self.GREEN), ("flow", "ECMO PATIENT FLOW", self.YELLOW), ("pao2", "PaO₂", self.GREEN), ("paco2", "PaCO₂", self.GREEN)]:
            box = tk.Frame(context, bg="#0d171d")
            box.pack(side="left", padx=(0, 12))
            tk.Label(box, text=label, bg="#0d171d", fg=self.MUTED, font=("Segoe UI", 7, "bold")).pack(side="left")
            value = tk.Label(box, text="--", bg="#0d171d", fg=color, font=("Consolas", 8, "bold"))
            value.pack(side="left", padx=(4, 0))
            self.lab_context_labels[key] = value

        results = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=12)
        results.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=(4, 16))
        results.rowconfigure(1, weight=1)
        results.columnconfigure(0, weight=1)
        head = tk.Frame(results, bg=self.SCREEN_2)
        head.grid(row=0, column=0, sticky="ew")
        tk.Label(head, text="ORDERED RESULTS", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(side="left")
        self.lab_status = tk.Label(head, text="30 s simulation turnaround placeholder", bg=self.SCREEN_2, fg=self.YELLOW, font=("Segoe UI", 8, "bold"))
        self.lab_status.pack(side="right")
        self.lab_results_text = tk.Text(results, height=12, bg="#0d151a", fg="#cbd7dc", insertbackground="white", relief="flat", font=("Consolas", 9), wrap="word")
        self.lab_results_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.lab_results_text.configure(state="disabled")
        self._refresh_lab_results(self.model.solve())

    def _apply_labs_context(self, reading) -> None:
        if not hasattr(self, "lab_context_labels"):
            return
        values = {
            "map": f"{reading.map_mmhg:.0f} mmHg",
            "spo2": f"{reading.spo2_pct:.1f}%",
            "flow": f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f} L/min",
            "pao2": f"{reading.pao2_mmhg:.0f}",
            "paco2": f"{reading.paco2_mmhg:.0f}",
        }
        for key, value in values.items():
            self.lab_context_labels[key].configure(text=value)

    def _order_lab(self, panel_id: str) -> None:
        try:
            result = self.model.order_diagnostic(panel_id, turnaround_s=30.0)
        except (RuntimeError, ValueError, KeyError) as exc:
            self.lab_status.configure(text=f"Order rejected — {exc}", fg=self.RED)
            self._log(f"Diagnostic order rejected: {exc}")
            return
        self.lab_status.configure(text=f"{result.result_id} collected; result pending", fg=self.YELLOW)
        self._refresh_lab_results(self.model.solve())
        self._log(f"Ordered {result.panel_name}; sample frozen at simulation time {result.sample_time_s:.0f} s.")

    @staticmethod
    def _format_lab_value(name: str, value: object, unit: str) -> str:
        if isinstance(value, float):
            text = f"{value:.1f}"
        else:
            text = str(value)
        return f"{name}: {text}{(' ' + unit) if unit else ''}"

    def _refresh_lab_results(self, snapshot: WorkspaceSnapshot) -> None:
        if not hasattr(self, "lab_results_text"):
            return
        now = float(snapshot.dynamic.elapsed_s)
        available_ids = {result.result_id for result in self.model.lab_results if result.is_available(now)}
        newly_available = available_ids - self._known_available_lab_result_ids
        self._unread_lab_result_ids.update(newly_available)
        self._known_available_lab_result_ids.update(available_ids)
        lines: list[str] = []
        for result in reversed(self.model.lab_results):
            sample = f"{int(result.sample_time_s) // 60:02d}:{int(result.sample_time_s) % 60:02d}"
            if result.is_available(now):
                available = f"{int(result.available_time_s) // 60:02d}:{int(result.available_time_s) % 60:02d}"
                lines.append(f"{result.result_id}  RESULT  {result.panel_name}  [{result.sample_site}]  sample {sample} / available {available}")
                for name, value in result.values.items():
                    lines.append("    " + self._format_lab_value(name, value, result.units.get(name, "")))
            else:
                remaining = max(0.0, result.available_time_s - now)
                lines.append(f"{result.result_id}  PENDING  {result.panel_name}  [{result.sample_site}]  sample {sample}  ({remaining:.0f} s remaining)")
        if not lines:
            lines = ["No diagnostics ordered."]
        self.lab_results_text.configure(state="normal")
        self.lab_results_text.delete("1.0", "end")
        self.lab_results_text.insert("1.0", "\n".join(lines))
        self.lab_results_text.configure(state="disabled")
        if getattr(self, "_active_page_key", None) == "LABS":
            # The available results above have now actually rendered in the
            # learner-visible Ordered Results view. Clear every contributing ID.
            self._unread_lab_result_ids.difference_update(available_ids)

    def _build_ventilator_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)

        title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)
        title.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(title, text="VENTILATOR", bg=self.SCREEN, fg=self.TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
        self.ventilator_mode_status = tk.Label(title, text="NATIVE", bg="#4a4220", fg=self.YELLOW, padx=10, pady=3, font=("Segoe UI", 8, "bold"))
        self.ventilator_mode_status.pack(side="right")

        controls = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        controls.grid(row=1, column=0, sticky="nsew", padx=(20, 6), pady=6)
        self.ventilator_controls_frame = controls
        tk.Label(controls, text="PRESSURE CONTROL", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(controls, text="Production pressure waveform driving the authoritative lung model. Applying these controls changes native physiology; values are not monitor-number patches.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=430, font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 10))

        grid = tk.Frame(controls, bg=self.SCREEN_2)
        grid.pack(fill="x")
        labels = [("PIP cmH₂O", "vent_pip_var", "10"), ("PEEP cmH₂O", "vent_peep_var", "5"), ("Rate /min", "vent_rate_var", "40"), ("Ti s", "vent_ti_var", "0.35"), ("FiO₂ %", "vent_fio2_var", "40")]
        for idx, (label, attr, default) in enumerate(labels):
            tk.Label(grid, text=label, bg=self.SCREEN_2, fg=self.MUTED, font=("Segoe UI", 8, "bold")).grid(row=idx, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            setattr(self, attr, var)
            tk.Entry(grid, textvariable=var, justify="center", width=10, font=("Consolas", 10)).grid(row=idx, column=1, sticky="w", padx=8, pady=3)

        buttons = tk.Frame(controls, bg=self.SCREEN_2)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="APPLY PRESSURE CONTROL", style="Console.TButton", command=self._apply_pressure_control).pack(side="left")
        ttk.Button(buttons, text="REMOVE PRESSURE CONTROL", style="Console.TButton", command=self._remove_pressure_control).pack(side="left", padx=(8, 0))
        self.ventilator_action_status = tk.Label(controls, text="Native/spontaneous lung model active", bg=self.SCREEN_2, fg=self.YELLOW, font=("Segoe UI", 8, "bold"))
        self.ventilator_action_status.pack(anchor="w", pady=(10, 0))

        readback = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        readback.grid(row=1, column=1, sticky="nsew", padx=(6, 20), pady=6)
        self.ventilator_readback_frame = readback
        tk.Label(readback, text="MODELED DELIVERY / PATIENT RESPONSE", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.ventilator_readback_labels: dict[str, tk.Label] = {}
        for key, label in [("mode", "Mode"), ("rr", "Respiratory rate"), ("vt", "Tidal volume"), ("mv", "Minute ventilation"), ("ie", "I:E"), ("pao2", "Patient PaO₂"), ("paco2", "Patient PaCO₂"), ("map", "MAP"), ("cvp", "CVP"), ("native_co", "Native cardiac output")]:
            row = tk.Frame(readback, bg=self.SCREEN_2)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=self.SCREEN_2, fg=self.MUTED, width=22, anchor="w", font=("Segoe UI", 8, "bold")).pack(side="left")
            value = tk.Label(row, text="--", bg=self.SCREEN_2, fg=self.CYAN, anchor="e", font=("Consolas", 10, "bold"))
            value.pack(side="right")
            self.ventilator_readback_labels[key] = value
        self.ventilator_cbc07_disclosure = tk.Label(
            readback,
            text=("PEEP can also reduce ECMO PATIENT FLOW through the simulator's intrathoracic-relative preload proxy. "
                  "This is a bounded educational coupling, not a validated quantitative PEEP-to-ECMO drainage prediction; measured CVP may rise while effective drainage preload falls."),
            bg=self.SCREEN_2, fg=self.YELLOW, justify="left", wraplength=460, font=("Segoe UI", 7, "bold"),
        )
        self.ventilator_cbc07_disclosure.pack(anchor="w", pady=(8, 0))

        unavailable = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        unavailable.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=20, pady=(8, 16))
        tk.Label(unavailable, text="PHASE 2d BOUNDARY", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(unavailable, text="Supported now: deterministic pressure-control PIP/PEEP/rate/Ti/FiO₂ through the unified patient. Not yet modeled: volume control, pressure support/synchrony, ventilator alarms, ETCO₂, dynamic waveform display, recruitment/derecruitment state, and validated device-specific delivered-volume accuracy.", bg=self.SCREEN_2, fg=self.YELLOW, justify="left", wraplength=980, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 0))

    def _apply_pressure_control(self) -> None:
        try:
            settings = PressureControlSettings(
                pip_cmh2o=float(self.vent_pip_var.get()),
                peep_cmh2o=float(self.vent_peep_var.get()),
                rate_bpm=float(self.vent_rate_var.get()),
                inspiratory_time_s=float(self.vent_ti_var.get()),
                fio2=float(self.vent_fio2_var.get()) / 100.0,
            )
            snapshot = self.model.apply_pressure_control_ventilator(settings)
        except ValueError as exc:
            self.ventilator_action_status.configure(text=f"Rejected — {exc}", fg=self.RED)
            self._log(f"Ventilator setting rejected: {exc}")
            return
        self._apply_snapshot(snapshot, log_action=False)
        self.ventilator_action_status.configure(text="Pressure control applied; physiology recalculation requested", fg=self.GREEN)
        self._log(f"Pressure control applied: PIP {settings.pip_cmh2o:.1f}, PEEP {settings.peep_cmh2o:.1f}, RR {settings.rate_bpm:.0f}, Ti {settings.inspiratory_time_s:.2f}, FiO₂ {settings.fio2:.2f}.")

    def _remove_pressure_control(self) -> None:
        snapshot = self.model.remove_pressure_control_ventilator()
        self._apply_snapshot(snapshot, log_action=False)
        self.ventilator_action_status.configure(text="Native/spontaneous lung model active", fg=self.YELLOW)
        self._log("Pressure-control ventilator removed; native/spontaneous lung model active.")

    def _apply_ventilator_snapshot(self, snapshot: WorkspaceSnapshot, *, reading=None) -> None:
        if not hasattr(self, "ventilator_readback_labels"):
            return
        if reading is None:
            reading = self._learner_patient_project(snapshot, physiology_updating=self.model.native_physiology_update_pending)
        patient = snapshot.dynamic.true.patient
        settings = self.model.ventilator_settings
        if settings is None:
            self.ventilator_mode_status.configure(text="NATIVE", bg="#4a4220", fg=self.YELLOW)
            mode_text = "Native/spontaneous"
            ie_text = "--"
        else:
            self.ventilator_mode_status.configure(text="PRESSURE CONTROL", bg="#17372b", fg=self.GREEN)
            mode_text = "Pressure control"
            ie_text = settings.ie_ratio_text
            self.vent_pip_var.set(f"{settings.pip_cmh2o:.1f}")
            self.vent_peep_var.set(f"{settings.peep_cmh2o:.1f}")
            self.vent_rate_var.set(f"{settings.rate_bpm:.0f}")
            self.vent_ti_var.set(f"{settings.inspiratory_time_s:.2f}")
            self.vent_fio2_var.set(f"{settings.fio2 * 100:.0f}")
        pending = self.model.native_physiology_update_pending
        suffix = " (updating)" if pending else ""
        values = {
            "mode": mode_text + suffix,
            "rr": f"{patient.respiratory_rate_bpm:.0f} /min",
            "vt": f"{patient.tidal_volume_ml:.1f} mL",
            "mv": f"{patient.minute_ventilation_ml_min:.0f} mL/min",
            "ie": ie_text,
            "pao2": f"{reading.pao2_mmhg:.1f} mmHg",
            "paco2": f"{reading.paco2_mmhg:.1f} mmHg",
            "map": f"{reading.map_mmhg:.0f} mmHg",
            "cvp": f"{reading.cvp_mmhg:.1f} mmHg",
            "native_co": f"{reading.native_cardiac_output_ml_min:.0f} mL/min",
        }
        for key, value in values.items():
            self.ventilator_readback_labels[key].configure(text=value)

    def _build_interventions_page(self, parent: tk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(3, weight=1)

        title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)
        title.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(title, text="INTERVENTIONS", bg=self.SCREEN, fg=self.TEXT, font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(title, text="PHASE 2b", bg="#17372b", fg=self.GREEN, padx=10, pady=3, font=("Segoe UI", 8, "bold")).pack(side="right")

        volume = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        volume.grid(row=1, column=0, sticky="nsew", padx=(20, 6), pady=6)
        self.volume_intervention_frame = volume
        tk.Label(volume, text="INTRAVASCULAR VOLUME", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(volume, text="Generic volume input through the authoritative patient volume mechanism. Fluid/blood-product composition is not yet modeled.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=430, font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 10))
        row = tk.Frame(volume, bg=self.SCREEN_2)
        row.pack(fill="x")
        tk.Label(row, text="Volume (mL)", bg=self.SCREEN_2, fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        self.volume_intervention_var = tk.StringVar(value="10")
        tk.Entry(row, textvariable=self.volume_intervention_var, justify="center", width=10, font=("Consolas", 10)).pack(side="left", padx=8)
        ttk.Button(row, text="GIVE VOLUME", style="Console.TButton", command=self._apply_volume_intervention).pack(side="left")
        self.volume_intervention_status = tk.Label(volume, text="Ready", bg=self.SCREEN_2, fg=self.GREEN, font=("Segoe UI", 8, "bold"))
        self.volume_intervention_status.pack(anchor="w", pady=(10, 0))

        ckrt = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=14)
        ckrt.grid(row=1, column=1, sticky="nsew", padx=(6, 20), pady=6)
        self.ckrt_intervention_frame = ckrt
        tk.Label(ckrt, text="CKRT PRESCRIPTION", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(ckrt, text="Sets CKRT blood flow and net ultrafiltration. Patient UF is active only when the ECMO shunt is configured CKRT and CKRT blood flow is > 0.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=430, font=("Segoe UI", 8)).pack(anchor="w", pady=(4, 8))
        ckrow = tk.Frame(ckrt, bg=self.SCREEN_2)
        ckrow.pack(fill="x")
        tk.Label(ckrow, text="Blood flow mL/min", bg=self.SCREEN_2, fg=self.MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(ckrow, text="Net UF mL/min", bg=self.SCREEN_2, fg=self.MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.ckrt_blood_flow_var = tk.StringVar(value="0")
        self.ckrt_uf_var = tk.StringVar(value="0")
        tk.Entry(ckrow, textvariable=self.ckrt_blood_flow_var, width=12, justify="center", font=("Consolas", 10)).grid(row=1, column=0, sticky="ew")
        tk.Entry(ckrow, textvariable=self.ckrt_uf_var, width=12, justify="center", font=("Consolas", 10)).grid(row=1, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(ckrt, text="APPLY CKRT PRESCRIPTION", style="Console.TButton", command=self._apply_ckrt_intervention).pack(anchor="w", pady=(8, 0))
        self.ckrt_intervention_status = tk.Label(ckrt, text="Inactive — shunt configuration is OPEN", bg=self.SCREEN_2, fg=self.YELLOW, font=("Segoe UI", 8, "bold"))
        self.ckrt_intervention_status.pack(anchor="w", pady=(8, 0))

        readback = tk.Frame(parent, bg="#0d171d", highlightbackground="#33434d", highlightthickness=1, padx=14, pady=8)
        readback.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(4, 4))
        self.intervention_readback_frame = readback
        tk.Label(readback, text="LIVE PATIENT READBACK", bg="#0d171d", fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 12))
        self.intervention_readback_labels: dict[str, tk.Label] = {}
        for key, label, color in [("map", "MAP", self.ORANGE), ("cvp", "CVP", self.CYAN), ("flow", "ECMO PATIENT FLOW", self.YELLOW), ("urine", "URINE", self.CYAN), ("fluid", "NET FLUID", self.CYAN), ("blood", "BLOOD VOLUME", self.CYAN)]:
            box = tk.Frame(readback, bg="#0d171d")
            box.pack(side="left", padx=(0, 12))
            tk.Label(box, text=label, bg="#0d171d", fg=self.MUTED, font=("Segoe UI", 7, "bold")).pack(side="left")
            value = tk.Label(box, text="--", bg="#0d171d", fg=color, font=("Consolas", 8, "bold"))
            value.pack(side="left", padx=(4, 0))
            self.intervention_readback_labels[key] = value

        unavailable = tk.Frame(parent, bg=self.SCREEN_2, highlightbackground="#33434d", highlightthickness=1, padx=16, pady=10)
        unavailable.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=(4, 16))
        tk.Label(unavailable, text="NOT YET AVAILABLE", bg=self.SCREEN_2, fg=self.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(unavailable, text="Vasoactive / inotrope therapy    •    Sedation / analgesia    •    Calcium / electrolyte therapy    •    Blood-component-specific transfusion", bg=self.SCREEN_2, fg=self.YELLOW, justify="left", wraplength=980, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 5))
        tk.Label(unavailable, text="These controls remain unavailable until the unified patient owns clinically defensible mechanisms. Phase 2b does not patch MAP, HR, electrolytes, or monitor values directly.", bg=self.SCREEN_2, fg=self.MUTED, justify="left", wraplength=980, font=("Segoe UI", 8)).pack(anchor="w")

    def _apply_volume_intervention(self) -> None:
        try:
            volume_ml = float(self.volume_intervention_var.get())
            snapshot = self.model.apply_intravascular_volume(volume_ml)
        except ValueError as exc:
            self.volume_intervention_status.configure(text=f"Rejected — {exc}", fg=self.RED)
            self._log(f"Volume intervention rejected: {exc}")
            return
        self._apply_snapshot(snapshot, log_action=False)
        self.volume_intervention_status.configure(text=f"Applied {volume_ml:.1f} mL", fg=self.GREEN)
        self._log(f"Intravascular volume intervention applied: {volume_ml:.1f} mL.")

    def _apply_ckrt_intervention(self) -> None:
        try:
            blood_flow = float(self.ckrt_blood_flow_var.get())
            net_uf = float(self.ckrt_uf_var.get())
            snapshot = self.model.apply_ckrt_prescription(
                blood_flow_ml_min=blood_flow,
                net_ultrafiltration_rate_ml_min=net_uf,
            )
        except ValueError as exc:
            self.ckrt_intervention_status.configure(text=f"Rejected — {exc}", fg=self.RED)
            self._log(f"CKRT prescription rejected: {exc}")
            return
        self._apply_snapshot(snapshot, log_action=False)
        active = snapshot.inputs.shunt_configuration == ShuntLineConfiguration.CKRT and blood_flow > 0.0
        if active:
            text = f"ACTIVE — Qb {blood_flow:.1f} mL/min; net UF {net_uf:.3f} mL/min"
            color = self.GREEN
        else:
            text = f"STORED / INACTIVE — select CKRT shunt and Qb > 0 (Qb {blood_flow:.1f}, UF {net_uf:.3f})"
            color = self.YELLOW
        self.ckrt_intervention_status.configure(text=text, fg=color)
        self._log(f"CKRT prescription set: blood flow {blood_flow:.1f} mL/min, net UF {net_uf:.3f} mL/min; {'active' if active else 'inactive'}.")

    def _apply_interventions_snapshot(self, snapshot: WorkspaceSnapshot, *, reading=None) -> None:
        if not hasattr(self, "ckrt_blood_flow_var"):
            return
        if reading is None:
            reading = self._learner_patient_project(snapshot, physiology_updating=self.model.native_physiology_update_pending)
        self.ckrt_blood_flow_var.set(f"{snapshot.inputs.shunt_ckrt_blood_flow_ml_min:.1f}")
        self.ckrt_uf_var.set(f"{snapshot.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min:.3f}")
        active = (
            snapshot.inputs.shunt_configuration == ShuntLineConfiguration.CKRT
            and snapshot.inputs.shunt_ckrt_blood_flow_ml_min > 0.0
        )
        if active:
            self.ckrt_intervention_status.configure(
                text=f"ACTIVE — Qb {snapshot.inputs.shunt_ckrt_blood_flow_ml_min:.1f} mL/min; net UF {snapshot.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min:.3f} mL/min",
                fg=self.GREEN,
            )
        else:
            self.ckrt_intervention_status.configure(
                text=f"Inactive — shunt {snapshot.inputs.shunt_configuration.value}; Qb {snapshot.inputs.shunt_ckrt_blood_flow_ml_min:.1f} mL/min",
                fg=self.YELLOW,
            )
        if hasattr(self, "intervention_readback_labels"):
            ivals = {
                "map": f"{reading.map_mmhg:.0f} mmHg",
                "cvp": f"{reading.cvp_mmhg:.1f} mmHg",
                "flow": f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f} L/min",
                "urine": f"{reading.urine_ml_kg_hr:.2f} mL/kg/h",
                "fluid": f"{reading.net_body_fluid_ml:+.1f} mL",
                "blood": f"{reading.blood_volume_fraction * 100.0:.1f}%",
            }
            for key, value in ivals.items():
                self.intervention_readback_labels[key].configure(text=value)

    def _refresh_nav_attention(self, snapshot: WorkspaceSnapshot) -> None:
        if not hasattr(self, "nav_buttons"):
            return
        labels = dict(self._nav_base_labels)
        if self._unread_lab_result_ids:
            labels["LABS"] = labels["LABS"] + "\nRESULT READY"
        qb = snapshot.inputs.shunt_ckrt_blood_flow_ml_min
        uf = snapshot.inputs.shunt_ckrt_net_ultrafiltration_rate_ml_min
        ckrt_active = snapshot.inputs.shunt_configuration == ShuntLineConfiguration.CKRT and qb > 0.0
        stored = qb > 0.0 or uf > 0.0
        if stored and not ckrt_active:
            labels["ACT"] = labels["ACT"] + "\nCHECK CKRT"
        for key, label in labels.items():
            self.nav_buttons[key].configure(text=label)

    def _build_console_page(self, parent: tk.Frame) -> None:
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        self.telemetry_bar = tk.Frame(parent, bg=self.SCREEN, padx=8, pady=7)
        self.telemetry_bar.grid(row=0, column=0, sticky="ew")
        self.telemetry_tiles: dict[str, TelemetryTile] = {}
        specs = [
            ("fdo2", "FdO₂", self.CYAN), ("sweep", "SWEEP", self.CYAN),
            ("postpo2", "POST-OXY PO₂", self.GREEN), ("postpco2", "POST-OXY PCO₂", self.GREEN),
            ("cdi", "VEN CDI SvO₂", self.GREEN), ("total", "TOTAL FLOW", self.YELLOW),
            ("patient", "ECMO PATIENT FLOW", self.YELLOW),
            ("map", "MAP", self.ORANGE), ("artpo2", "PATIENT PaO₂", self.ORANGE),
            ("artpco2", "PATIENT PaCO₂", self.ORANGE), ("p1", "P1", self.CYAN),
            ("p2", "P2", self.CYAN), ("p3", "P3", self.CYAN), ("dp", "OXY ΔP", self.CYAN),
        ]
        columns = 7
        for col in range(columns):
            self.telemetry_bar.columnconfigure(col, weight=1)
        for index, (key, label, accent) in enumerate(specs):
            tile = TelemetryTile(self.telemetry_bar, label, accent=accent)
            tile.grid(row=index // columns, column=index % columns, sticky="nsew", padx=3, pady=3)
            self.telemetry_tiles[key] = tile

        stage = tk.Frame(parent, bg=self.SCREEN)
        stage.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 7))
        stage.columnconfigure(0, weight=44)
        stage.columnconfigure(1, weight=56)
        stage.rowconfigure(0, weight=1)

        gauge_panel = tk.Frame(stage, bg=self.SCREEN)
        gauge_panel.grid(row=0, column=0, sticky="nsew")
        gauge_panel.rowconfigure(0, weight=1)
        gauge_panel.columnconfigure(0, weight=1)
        self.gauge = tk.Canvas(gauge_panel, bg=self.SCREEN, highlightthickness=0, width=450, height=430)
        self.gauge.grid(row=0, column=0, sticky="nsew")
        self.gauge.bind("<Configure>", lambda _event: self._redraw_gauge())

        circuit_panel = tk.Frame(stage, bg=self.SCREEN)
        circuit_panel.grid(row=0, column=1, sticky="nsew")
        circuit_panel.rowconfigure(0, weight=1)
        circuit_panel.columnconfigure(0, weight=1)
        self.circuit_canvas = tk.Canvas(circuit_panel, bg=self.SCREEN, highlightthickness=0, width=560, height=430)
        self.circuit_canvas.grid(row=0, column=0, sticky="nsew")
        self.circuit_canvas.bind("<Configure>", lambda _event: self._redraw_circuit())

        controls = tk.Frame(parent, bg="#121c22", padx=6, pady=4)
        controls.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
        for col in range(4):
            controls.columnconfigure(col, weight=1)
        self._build_pump_control(controls, 0)
        self._build_sweep_control(controls, 1)
        self._build_fdo2_control(controls, 2)
        self._build_bridge_control(controls, 3)
        self._build_shunt_control(controls)

    def _control_group(self, parent: tk.Frame, column: int, title: str, *, row: int = 0, columnspan: int = 1) -> tk.Frame:
        box = tk.Frame(parent, bg=self.CONTROL, highlightbackground="#364650", highlightthickness=1, padx=3, pady=2)
        box.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=2, pady=(0, 2) if row == 0 else (1, 0))
        tk.Label(box, text=title, bg=self.CONTROL, fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        return box

    def _build_pump_control(self, parent: tk.Frame, column: int) -> None:
        box = self._control_group(parent, column, "PUMP / RPM")
        self.run_button = ttk.Button(box, text="START PUMP", style="Console.TButton", command=self._toggle_pump)
        self.run_button.pack(fill="x", pady=(2, 2))
        row = tk.Frame(box, bg=self.CONTROL)
        row.pack(fill="x", pady=(1,0))
        ttk.Button(row, text="−100", style="Compact.TButton", command=lambda: self._nudge_rpm(-100)).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="−50", style="Compact.TButton", command=lambda: self._nudge_rpm(-50)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(row, text="+50", style="Compact.TButton", command=lambda: self._nudge_rpm(50)).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="+100", style="Compact.TButton", command=lambda: self._nudge_rpm(100)).pack(side="left", expand=True, fill="x", padx=(2, 0))
        self.rpm_entry_var = tk.StringVar(value="3000")
        self._entry_row(box, self.rpm_entry_var, self._set_rpm_from_entry)

    def _build_sweep_control(self, parent: tk.Frame, column: int) -> None:
        box = self._control_group(parent, column, "SWEEP  L/min")
        self.sweep_display = tk.Label(box, text="0.60", bg=self.CONTROL, fg=self.CYAN, font=("Consolas", 14, "bold"))
        self.sweep_display.pack()
        row = tk.Frame(box, bg=self.CONTROL)
        row.pack(fill="x", pady=(1,0))
        for amount in (-0.10, -0.05, 0.05, 0.10):
            ttk.Button(row, text=f"{amount:+.2f}", style="Compact.TButton", command=lambda n=amount: self._nudge_sweep(n)).pack(side="left", expand=True, fill="x", padx=1)
        self.sweep_entry_var = tk.StringVar(value="0.60")
        self._entry_row(box, self.sweep_entry_var, self._set_sweep_from_entry)

    def _build_fdo2_control(self, parent: tk.Frame, column: int) -> None:
        box = self._control_group(parent, column, "FdO₂  %")
        self.fdo2_display = tk.Label(box, text="100", bg=self.CONTROL, fg=self.CYAN, font=("Consolas", 14, "bold"))
        self.fdo2_display.pack()
        row = tk.Frame(box, bg=self.CONTROL)
        row.pack(fill="x", pady=(1,0))
        for amount in (-10, -5, 5, 10):
            ttk.Button(row, text=f"{amount:+d}", style="Compact.TButton", command=lambda n=amount: self._nudge_fdo2(n)).pack(side="left", expand=True, fill="x", padx=1)
        self.fdo2_entry_var = tk.StringVar(value="100")
        self._entry_row(box, self.fdo2_entry_var, self._set_fdo2_from_entry)

    def _build_bridge_control(self, parent: tk.Frame, column: int) -> None:
        box = self._control_group(parent, column, "BRIDGE")
        self.bridge_value_label = tk.Label(box, text="0%", bg=self.CONTROL, fg=self.YELLOW, font=("Consolas", 14, "bold"))
        self.bridge_value_label.pack()
        row = tk.Frame(box, bg=self.CONTROL)
        row.pack(fill="x", pady=(1,0))
        for text, value in [("CLOSE", 0), ("−10", -10), ("+10", 10), ("OPEN", 100)]:
            command = (lambda v=value: self._set_bridge(v)) if value in (0, 100) else (lambda v=value: self._nudge_bridge(v))
            ttk.Button(row, text=text, style="Compact.TButton", command=command).pack(side="left", expand=True, fill="x", padx=1)
        tk.Label(box, text="Clamp opening", bg=self.CONTROL, fg=self.MUTED, font=("Segoe UI", 6)).pack(pady=(2, 0))

    def _build_shunt_control(self, parent: tk.Frame) -> None:
        box = self._control_group(parent, 0, "SHUNT / SAFETY", row=1, columnspan=4)
        row = tk.Frame(box, bg=self.CONTROL)
        row.pack(fill="x", pady=(1, 0))

        tk.Label(row, text="Shunt configuration", bg=self.CONTROL, fg=self.MUTED, font=("Segoe UI", 7, "bold")).pack(side="left", padx=(0, 6))
        self.shunt_var = tk.StringVar(value=self.model.inputs.shunt_configuration.value)
        shunt = ttk.Combobox(row, textvariable=self.shunt_var, values=[item.value for item in ShuntLineConfiguration], state="readonly", font=("Segoe UI", 7), width=14)
        shunt.pack(side="left", padx=(0, 8))
        shunt.bind("<<ComboboxSelected>>", lambda _event: self._shunt_changed())

        self.scuffing_var = tk.BooleanVar(value=self.model.inputs.shunt_scuffing_active)
        tk.Checkbutton(row, text="Scuffing active", variable=self.scuffing_var, command=self._scuffing_changed, bg=self.CONTROL, fg=self.TEXT, selectcolor=self.SCREEN_2, activebackground=self.CONTROL, activeforeground=self.TEXT, font=("Segoe UI", 7)).pack(side="left", padx=(0, 10))

        tk.Label(row, text="Clamps / bubble reset — NOT YET MODELED", bg=self.CONTROL, fg=self.ORANGE, font=("Segoe UI", 6, "bold")).pack(side="left")

    def _entry_row(self, parent: tk.Frame, variable: tk.StringVar, command) -> None:
        row = tk.Frame(parent, bg=self.CONTROL)
        row.pack(fill="x", pady=(1, 0))
        tk.Entry(row, textvariable=variable, justify="center", font=("Consolas", 8), width=6).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="SET", style="Compact.TButton", command=command).pack(side="left", padx=(4, 0))

    def _redraw_gauge(self) -> None:
        if not hasattr(self, "gauge"):
            return
        c = self.gauge
        c.delete("all")
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 300)
        size = min(w * 0.88, h * 0.88)
        cx, cy = w * 0.5, h * 0.52
        r = size * 0.43
        c.create_text(18, 18, text="PUMP MANAGER", fill=self.TEXT, anchor="nw", font=("Segoe UI", 12, "bold"))
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=135, extent=270, style="arc", outline="#627681", width=8)
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=135, extent=180, style="arc", outline=self.GREEN, width=8)
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=315, extent=45, style="arc", outline=self.YELLOW, width=8)
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=360, extent=45, style="arc", outline=self.RED, width=8)
        for value in range(0, 6001, 600):
            angle = math.radians(225 - (value / 6000.0) * 270)
            x1 = cx + (r - 14) * math.cos(angle); y1 = cy - (r - 14) * math.sin(angle)
            x2 = cx + r * math.cos(angle); y2 = cy - r * math.sin(angle)
            c.create_line(x1, y1, x2, y2, fill="#d9e5e8", width=2)
            tx = cx + (r - 31) * math.cos(angle); ty = cy - (r - 31) * math.sin(angle)
            c.create_text(tx, ty, text=str(value), fill=self.MUTED, font=("Consolas", 7))
        c.create_text(cx, cy-r*0.45, text="ECMO PATIENT FLOW", fill=self.MUTED, font=("Segoe UI", 10, "bold"))
        c.create_text(cx, cy-r*0.03, text=getattr(self, "_gauge_flow", "0.000"), fill=self.YELLOW, font=("Consolas", max(25, int(size*0.075)), "bold"))
        c.create_text(cx+r*0.45, cy+r*0.03, text="L/min", fill=self.MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(cx, cy+r*0.22, text=f"{getattr(self, '_gauge_rpm', '0')} RPM", fill=self.TEXT, font=("Consolas", 14, "bold"))
        c.create_text(cx, cy+r*0.40, text=getattr(self, "_gauge_status", "STOPPED"), fill=self.GREEN if getattr(self, "_gauge_status", "STOPPED") == "RUNNING" else self.RED, font=("Segoe UI", 10, "bold"))
        c.create_text(cx, cy+r*0.51, text=f"Total circuit {getattr(self, '_gauge_total_flow', '0.000')} L/min", fill=self.MUTED, font=("Segoe UI", 8, "bold"))
        # commanded-RPM marker
        rpm = min(max(float(getattr(self, "_commanded_rpm", 0.0)), 0.0), 6000.0)
        angle = math.radians(225 - (rpm / 6000.0) * 270)
        mx = cx + (r + 4) * math.cos(angle); my = cy - (r + 4) * math.sin(angle)
        c.create_polygon(mx, my, mx-7, my-13, mx+7, my-13, fill=self.ORANGE, outline="")
        c.create_text(cx-r*0.42, cy+r*0.62, text=f"P1  {getattr(self, '_gauge_p1', '--')} mmHg", fill=self.CYAN, font=("Consolas", 10, "bold"))
        c.create_text(cx+r*0.42, cy+r*0.62, text=f"P2  {getattr(self, '_gauge_p2', '--')} mmHg", fill=self.CYAN, font=("Consolas", 10, "bold"))

    def _redraw_circuit(self) -> None:
        if not hasattr(self, "circuit_canvas"):
            return
        c = self.circuit_canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 380), max(c.winfo_height(), 300)
        c.create_text(20, 18, text="PATIENT / CIRCUIT", fill=self.TEXT, anchor="nw", font=("Segoe UI", 12, "bold"))
        c.create_text(w-20, 20, text="ORIGINAL SIMULATION VIEW", fill=self.MUTED, anchor="ne", font=("Segoe UI", 7, "bold"))

        # Patient outline, deliberately original and schematic.
        px, py = w*0.73, h*0.50
        c.create_oval(px-38, py-130, px+38, py-55, outline=self.BLUE, width=4)
        c.create_line(px, py-55, px, py+110, fill=self.BLUE, width=5)
        c.create_line(px, py-20, px-75, py+35, fill=self.BLUE, width=4)
        c.create_line(px, py-20, px+75, py+35, fill=self.BLUE, width=4)
        c.create_line(px, py+110, px-48, py+185, fill=self.BLUE, width=4)
        c.create_line(px, py+110, px+48, py+185, fill=self.BLUE, width=4)
        c.create_oval(px-25, py-10, px+25, py+35, outline=self.RED, width=3)
        c.create_text(px, py+12, text="♥", fill=self.RED, font=("Segoe UI Symbol", 24))

        pump_x, pump_y = w*0.22, h*0.42
        oxy_x, oxy_y = w*0.40, h*0.42
        c.create_oval(pump_x-36, pump_y-36, pump_x+36, pump_y+36, outline=self.CYAN, width=5)
        c.create_text(pump_x, pump_y, text="PUMP", fill=self.TEXT, font=("Segoe UI", 9, "bold"))
        c.create_rectangle(oxy_x-34, oxy_y-48, oxy_x+34, oxy_y+48, outline="#e7ecee", width=4)
        c.create_text(oxy_x, oxy_y, text="OXY", fill=self.TEXT, font=("Segoe UI", 10, "bold"))

        # Drainage path (blue), return path (red), bridge/shunt (yellow/cyan).
        c.create_line(px-20, py, px-125, py-10, pump_x+35, pump_y, fill=self.BLUE, width=7, smooth=True, arrow=tk.LAST)
        c.create_line(pump_x+36, pump_y, oxy_x-34, oxy_y, fill=self.CYAN, width=7, arrow=tk.LAST)
        c.create_line(oxy_x+35, oxy_y, px-10, py+5, fill=self.RED, width=7, smooth=True, arrow=tk.LAST)
        bridge_y = min(h-62, py+145)
        c.create_line(px-80, py+50, px-105, bridge_y, pump_x+5, bridge_y, pump_x+5, pump_y+34, fill=self.YELLOW, width=4, smooth=True, arrow=tk.LAST)
        c.create_text(w*0.45, bridge_y-11, text=f"BRIDGE {getattr(self, '_bridge_pct', '0')}%  •  {getattr(self, '_bridge_flow', '0')} mL/min", fill=self.YELLOW, font=("Consolas", 9, "bold"))
        c.create_line(oxy_x, oxy_y+48, oxy_x, oxy_y+92, pump_x+40, oxy_y+92, fill=self.CYAN, width=3, arrow=tk.LAST)
        c.create_text((oxy_x+pump_x)/2, oxy_y+108, text=f"SHUNT {getattr(self, '_shunt_flow', '0')} mL/min", fill=self.CYAN, font=("Consolas", 9, "bold"))

        c.create_text(px, py+58, text=f"MAP {getattr(self, '_patient_map', '--')} mmHg", fill=self.ORANGE, font=("Consolas", 10, "bold"))
        c.create_text(px, py+76, text=f"PaO₂ {getattr(self, '_patient_pao2', '--')}  PaCO₂ {getattr(self, '_patient_paco2', '--')}", fill=self.TEXT, font=("Consolas", 9, "bold"))
        c.create_text(px, py+94, text=f"VENOUS VOLUME {getattr(self, '_effective_volume', '--')}%", fill=self.MUTED, font=("Consolas", 8, "bold"))
        c.create_text(w*0.53, h-35, text=f"ECMO PATIENT FLOW  {getattr(self, '_patient_flow', '0')} mL/min", fill=self.GREEN, font=("Consolas", 14, "bold"))
        c.create_text(w*0.53, h-15, text="Blue: drainage   Red: return   Yellow: bridge", fill=self.MUTED, font=("Segoe UI", 8))

    def _build_event_strip(self) -> None:
        strip = tk.Frame(self.root, bg="#151e23", padx=12, pady=7)
        strip.pack(fill="x", padx=12, pady=(6, 10))
        tk.Label(strip, text="EVENT", bg="#151e23", fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 10))
        self.event_label = tk.Label(strip, text="Console initialized. Pump stopped; commanded RPM retained.", bg="#151e23", fg=self.TEXT, font=("Segoe UI", 9), anchor="w")
        self.event_label.pack(side="left", fill="x", expand=True)
        self.advisory_label = tk.Label(strip, text="", bg="#151e23", fg=self.ORANGE, font=("Segoe UI", 8, "bold"), anchor="e")
        self.advisory_label.pack(side="right", padx=(10, 0))
        tk.Label(
            strip, text=SIMULATOR_ADVISORY_LABEL, bg="#151e23", fg=self.MUTED,
            font=("Segoe UI", 7, "bold"),
        ).pack(side="right", padx=(12, 4))

    def _schedule_refresh(self) -> None:
        self.root.after(1000, self._refresh_tick)

    def _refresh_tick(self) -> None:
        try:
            snapshot = self.model.advance(1.0)
            self._apply_snapshot(snapshot, log_action=False)
            elapsed = int(snapshot.dynamic.elapsed_s)
            self.nav_runtime.configure(text=f"ECMO\n{elapsed // 60:02d}:{elapsed % 60:02d}")
        finally:
            if self.root.winfo_exists():
                self._schedule_refresh()

    def _bind_shortcuts(self) -> None:
        self.root.bind("<space>", self._shortcut_toggle_pump)
        self.root.bind("<Up>", lambda event: self._shortcut_nudge_rpm(event, 50))
        self.root.bind("<Down>", lambda event: self._shortcut_nudge_rpm(event, -50))

    def _ecmo_shortcut_allowed(self) -> bool:
        focus = self.root.focus_get()
        focus_class = focus.winfo_class() if focus is not None else None
        return ecmo_shortcut_allowed(
            active_page_key=getattr(self, "_active_page_key", "ECMO"),
            focus_widget_class=focus_class,
        )

    def _shortcut_toggle_pump(self, _event: object = None) -> str | None:
        if not self._ecmo_shortcut_allowed():
            return None
        self._toggle_pump()
        return "break"

    def _shortcut_nudge_rpm(self, _event: object, amount: float) -> str | None:
        if not self._ecmo_shortcut_allowed():
            return None
        self._nudge_rpm(amount)
        return "break"

    def _log(self, message: str) -> None:
        self.event_label.configure(text=f"{datetime.now().strftime('%H:%M:%S')} — {message}")

    def _toggle_pump(self) -> None:
        starting = not self.model.inputs.pump_running
        snapshot = self.model.update(pump_running=starting)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Pump {'started' if starting else 'stopped'}. Actual RPM {snapshot.applied_rpm:.0f}; total flow {snapshot.coupled_state.circuit.solved_total_flow_ml_min:.0f} mL/min.")

    def _nudge_rpm(self, amount: float) -> None:
        old = self.model.inputs.commanded_rpm
        value = min(max(old + amount, 0.0), 5000.0)
        snapshot = self.model.update(commanded_rpm=value)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Commanded RPM changed from {old:.0f} to {value:.0f}. Total flow is {snapshot.coupled_state.circuit.solved_total_flow_ml_min:.0f} mL/min.")

    def _set_rpm_from_entry(self) -> None:
        try:
            value = min(max(float(self.rpm_entry_var.get()), 0.0), 5000.0)
        except ValueError:
            self._log("RPM entry rejected: enter a numeric value from 0 to 5000.")
            return
        old = self.model.inputs.commanded_rpm
        snapshot = self.model.update(commanded_rpm=value)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Commanded RPM changed from {old:.0f} to {value:.0f}.")

    def _nudge_sweep(self, amount_l_min: float) -> None:
        old_ml = self.model.inputs.sweep_gas_flow_ml_min
        new_l = min(max(old_ml / 1000.0 + amount_l_min, 0.0), 10.0)
        snapshot = self.model.update(sweep_gas_flow_ml_min=new_l * 1000.0)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Sweep changed from {old_ml / 1000.0:.2f} to {new_l:.2f} L/min. Post-oxygenator PaCO₂ is {snapshot.coupled_state.post_oxygenator_paco2_mmhg:.1f} mmHg.")

    def _set_sweep_from_entry(self) -> None:
        try:
            new_l = min(max(float(self.sweep_entry_var.get()), 0.0), 10.0)
        except ValueError:
            self._log("Sweep entry rejected: enter a numeric value from 0.00 to 10.00 L/min.")
            return
        old_l = self.model.inputs.sweep_gas_flow_ml_min / 1000.0
        snapshot = self.model.update(sweep_gas_flow_ml_min=new_l * 1000.0)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Sweep changed from {old_l:.2f} to {new_l:.2f} L/min.")

    def _nudge_fdo2(self, amount_pct: float) -> None:
        old_pct = self.model.inputs.fdo2 * 100.0
        new_pct = min(max(old_pct + amount_pct, 21.0), 100.0)
        snapshot = self.model.update(fdo2=new_pct / 100.0)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"FdO₂ changed from {old_pct:.0f}% to {new_pct:.0f}%. Post-oxygenator saturation is {snapshot.coupled_state.post_oxygenator_saturation * 100:.1f}%.")

    def _set_fdo2_from_entry(self) -> None:
        try:
            new_pct = min(max(float(self.fdo2_entry_var.get()), 21.0), 100.0)
        except ValueError:
            self._log("FdO₂ entry rejected: enter a numeric percentage from 21 to 100.")
            return
        old_pct = self.model.inputs.fdo2 * 100.0
        snapshot = self.model.update(fdo2=new_pct / 100.0)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"FdO₂ changed from {old_pct:.0f}% to {new_pct:.0f}%.")

    def _set_bridge(self, value_pct: float) -> None:
        old_pct = self.model.inputs.bridge_clamp_position * 100.0
        snapshot = self.model.update(bridge_clamp_position=value_pct / 100.0)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Bridge opening changed from {old_pct:.0f}% to {value_pct:.0f}%. Bridge flow is {snapshot.coupled_state.circuit.solved_bridge_flow_ml_min:.0f} mL/min.")

    def _nudge_bridge(self, amount_pct: float) -> None:
        old_pct = self.model.inputs.bridge_clamp_position * 100.0
        new_pct = min(max(old_pct + amount_pct, 0.0), 100.0)
        self._set_bridge(new_pct)

    def _shunt_changed(self) -> None:
        configuration = ShuntLineConfiguration(self.shunt_var.get())
        snapshot = self.model.update(shunt_configuration=configuration)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Shunt configuration changed to {configuration.value}. Shunt flow is {snapshot.coupled_state.circuit.solved_shunt_flow_ml_min:.0f} mL/min.")

    def _scuffing_changed(self) -> None:
        active = self.scuffing_var.get()
        snapshot = self.model.update(shunt_scuffing_active=active)
        self._apply_snapshot(snapshot, log_action=False)
        self._log(f"Scuffing / filtration {'activated' if active else 'deactivated'}. Shunt flow is {snapshot.coupled_state.circuit.solved_shunt_flow_ml_min:.0f} mL/min.")

    def _apply_snapshot(self, snapshot: WorkspaceSnapshot, *, log_action: bool = False) -> None:
        self._last_snapshot = snapshot
        coupled_state = snapshot.coupled_state
        c = coupled_state.circuit
        displayed = snapshot.dynamic.displayed
        true_patient = snapshot.dynamic.true.patient
        pending = self.model.native_physiology_update_pending
        reading = self._learner_patient_project(snapshot, physiology_updating=pending)
        running = snapshot.status_text == "RUNNING"
        self.header_status.configure(text=snapshot.status_text, bg="#17372b" if running else "#402020", fg=self.GREEN if running else self.RED)
        latency_text = physiology_latency_text(pending=pending)
        self.header_compute_status.configure(text=latency_text)
        self.run_button.configure(text="STOP PUMP" if running else "START PUMP")

        rpm = snapshot.inputs.commanded_rpm
        self.rpm_entry_var.set(f"{rpm:.0f}")
        self.bridge_value_label.configure(text=f"{snapshot.inputs.bridge_clamp_position * 100:.0f}%")
        sweep_l = snapshot.inputs.sweep_gas_flow_ml_min / 1000.0
        self.sweep_display.configure(text=f"{sweep_l:.2f}")
        self.sweep_entry_var.set(f"{sweep_l:.2f}")
        fdo2_pct = snapshot.inputs.fdo2 * 100.0
        self.fdo2_display.configure(text=f"{fdo2_pct:.0f}")
        self.fdo2_entry_var.set(f"{fdo2_pct:.0f}")

        displayed_p1 = round(displayed.p1_mmhg)
        displayed_p2 = round(displayed.p2_mmhg)
        displayed_p3 = round(displayed.p3_mmhg)
        displayed_dp = displayed_p2 - displayed_p3
        values = {
            "fdo2": f"{fdo2_pct:.0f}%", "sweep": f"{sweep_l:.2f}",
            "postpo2": f"{coupled_state.post_oxygenator_cdi.po2_mmhg:.0f}" if coupled_state.post_oxygenator_cdi.po2_mmhg is not None else "--",
            "postpco2": f"{coupled_state.post_oxygenator_cdi.pco2_mmhg:.0f}" if coupled_state.post_oxygenator_cdi.pco2_mmhg is not None else "--",
            "cdi": f"{coupled_state.cdi.mixed_saturation * 100:.0f}%",
            "total": f"{displayed.total_circuit_flow_ml_min / 1000.0:.3f}",
            "patient": f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f}",
            "map": f"{reading.map_mmhg:.0f}",
            "artpo2": f"{reading.pao2_mmhg:.0f}",
            "artpco2": f"{reading.paco2_mmhg:.0f}",
            "p1": f"{displayed_p1:.0f}", "p2": f"{displayed_p2:.0f}", "p3": f"{displayed_p3:.0f}",
            "dp": f"{displayed_dp:.0f}",
        }
        for key, value in values.items():
            self.telemetry_tiles[key].set(value)

        self._gauge_flow = f"{reading.ecmo_patient_flow_ml_min / 1000.0:.3f}"
        self._gauge_total_flow = f"{displayed.total_circuit_flow_ml_min / 1000.0:.3f}"
        self._gauge_rpm = f"{c.rpm:.0f}"
        self._gauge_status = snapshot.status_text
        self._gauge_p1 = f"{displayed.p1_mmhg:.0f}"
        self._gauge_p2 = f"{displayed.p2_mmhg:.0f}"
        self._commanded_rpm = rpm
        self._bridge_pct = f"{snapshot.inputs.bridge_clamp_position * 100:.0f}"
        self._bridge_flow = f"{c.solved_bridge_flow_ml_min:.0f}"
        self._shunt_flow = f"{c.solved_shunt_flow_ml_min:.0f}"
        self._patient_flow = f"{reading.ecmo_patient_flow_ml_min:.0f}"
        self._patient_map = f"{reading.map_mmhg:.0f}"
        self._patient_pao2 = f"{reading.pao2_mmhg:.0f}"
        self._patient_paco2 = f"{reading.paco2_mmhg:.0f}"
        self._effective_volume = f"{true_patient.effective_venous_volume_fraction * 100:.0f}"
        self._displayed_dp = f"{displayed_dp:.0f}"
        advisories = list(snapshot.dynamic.advisories)
        if pending:
            advisories.append("PHYSIOLOGY UPDATING")
        if snapshot.dynamic.chatter_display_active and "DRAINAGE CHATTER" not in advisories:
            advisories.append("DRAINAGE CHATTER")
        self.advisory_label.configure(text="  |  ".join(advisories))
        self._redraw_gauge()
        self._redraw_circuit()
        self._apply_status_ribbon(reading)
        self._apply_patient_monitor_snapshot(snapshot, reading=reading)
        self._apply_ventilator_snapshot(snapshot, reading=reading)
        self._apply_interventions_snapshot(snapshot, reading=reading)
        self._apply_labs_context(reading)
        self._refresh_lab_results(snapshot)
        self._refresh_nav_attention(snapshot)
        self._refresh_scenario_log()

        if log_action:
            self._log("Console values refreshed.")

    def _close(self) -> None:
        self.model.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
