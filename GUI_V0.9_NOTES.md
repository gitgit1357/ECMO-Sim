GUI / Coupling v0.9 changes (2026-07-28)
- Added an explicit true post-oxygenator blood state: PO2, PCO2, oxygen saturation, Hct, Hgb, and temperature.
- Added a separate post-oxygenator CDI sensor reading and sensor-state API.
- Added explicit post-oxygenator PO2 to the ECMO console and patient-delivery coupling contract.
- Updated the top telemetry ribbon to show POST PO2 and POST PCO2 from the post-oxy CDI.
- Preserved the venous CDI as a separate drainage-limb sensor.
- Kept patient arterial gases separate for later native/ECMO mixing work.
