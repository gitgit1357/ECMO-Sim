# ECMO–Patient Coupling: Stage 1 Contract

Stage 1 establishes a separate `neoecmocoupling` package. It translates and
validates values between the existing `neopatient` and `neoecmo` packages but
does not yet change either system's calculated physiology.

## Ownership

### Patient owns
- Weight
- CVP / venous drainage pressure source
- MAP / arterial return pressure environment
- Blood-volume fraction
- Native cardiac output
- Native venous oxygen and CO2 state

### ECMO circuit owns
- Total circuit flow
- Patient-directed ECMO flow
- Shunt flow
- Bridge flow
- Post-oxygenator saturation and PCO2
- P1, P2, P3 and return pressure
- External circuit fluid removal

### Future coupling coordinator will own
- Combined effective systemic perfusion
- Native-heart/ECMO interaction
- Blood mixing
- Iteration between patient pressures and circuit flow
- Time stepping and feedback

## Important current surrogate

The unified patient does not yet expose a distinct central-venous blood gas.
The Stage-1 adapter therefore uses current arterial saturation and PaCO2 as
explicit temporary translation surrogates. Stage 2 should add a true venous
blood-state output before physiologic ECMO support is applied.
