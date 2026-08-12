GUI v0.17 / Coupling Stage 7 (2026-07-28)

- Connected the ECMO workspace to DynamicCoupledVaEcmoPatient.
- Added a one-second GUI simulation refresh loop.
- Learner-facing patient flow, total flow, MAP, P1/P2/P3, patient PaO2, and patient PaCO2 now use the Stage-6 displayed/trended state.
- True post-oxygenator PO2/PCO2 and venous CDI remain distinct circuit measurements.
- Added patient MAP, patient arterial gas, and effective venous volume information to the visual console.
- Added coupled-patient advisories to the persistent bottom strip.
- Preserved the original EcmoWorkspaceModel.state interface for older benches while exposing coupled_state and dynamic snapshots for the live GUI.
