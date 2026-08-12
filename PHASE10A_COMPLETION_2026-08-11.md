# Phase 10a — PEEP → ECMO Drainage Coupling Completion
Date: 2026-08-11
Status: **CLOSED — IMPLEMENTATION COMPLETE**

## Authorization and boundary
The project owner explicitly opened Phase 10a after the verified Phase 9a complete handoff. Phase 10b and Phase 11 remain unopened.

## Implemented mechanism
Phase 9a established one immutable venous-state boundary with measured CVP, pleural-pressure delta, effective venous volume, native mixed-venous oxygen, and the explicitly derived teaching proxy:

`intrathoracic_relative_preload_proxy_mmhg = measured CVP - pleural pressure delta`

Phase 10a changes the existing patient→ECMO adapter so the ECMO drainage hydraulic/preload boundary consumes that proxy rather than absolute measured CVP. It does not add a second venous solver, new free venous state, or a monitor-derived feedback path.

Measured CVP remains sourced from native `mean_ra_mmhg` and remains available for learner display. The important teaching distinction is now mechanically preserved: positive airway pressure can raise measured CVP while effective drainage preload falls.

## Protected behavior
At fixed canonical VA controls (3000 RPM, sweep 600 mL/min) across the existing 0/5/8/12 cmH2O PEEP regression probe:
- measured CVP rises;
- the intrathoracic-relative preload proxy falls;
- patient-directed ECMO flow falls;
- blood volume does not change merely because PEEP changed;
- the canonical 8 cmH2O flow effect is bounded to remain above 80% of baseline;
- returning PEEP to baseline in the same patient restores drainage flow/effective venous pressure to baseline.

The 80% bound is a regression catastrophe guard, not a clinical threshold or prescription.

## CBC07 / learner disclosure
CBC07 now includes the coupled VA drainage direction, boundedness, and reversal while retaining the evidence boundary: exact PEEP-to-flow magnitude is not clinically validated. The Ventilator page disclosure was updated from the obsolete “blocked/no transmural concept” wording to the Phase 10a reduced-order proxy wording.

The 2026-08-10 external evidence packet is retained as historical evidence provenance; it correctly documented that the relationship was blocked at that time. Phase 10a closes the architecture block but does not retroactively turn that packet into validation of the new quantitative coupling.

## Capability-matrix cleanup
- CBC07 row updated for Phase 10a coupled behavior.
- Phase 6b disclosure row updated to the current boundary.
- The stale FdO2 row no longer says authoritative venous oxygen is absent; Phase 9a supplied that state. The remaining coupled FdO2 work is still deferred to Phase 10b.
- Added a dedicated Phase 10a capability row.
- JSON/CSV/Markdown mirrors synchronized at 101 rows.

## Verification
- New Phase 10a tests: **5/5 passed**.
- Phase 9a structural/ownership compatibility with the migrated consumer: **6/6 passed**.
- Existing hydraulic/dynamic/gas affected tests: **16/16 passed**.
- Existing hypovolemia CBC: **2/2 passed**.
- Existing CBC07 native behavior: **4/4 passed**.
- Affected total: **33/33 passed**, executed in bounded groups.
- Capability/release matrix checks: **25/25 passed**.
- Live Tk/Xvfb Phase 6b disclosure check: **1/1 passed**.
- Collection: **538 nodes = 533 Phase-9a baseline + 5 Phase-10a nodes**.

A single combined affected invocation exceeded the execution window after 26 visible passes. It is recorded as incomplete rather than called a pass; every node in its 33-node manifest was subsequently/previously verified in bounded zero-exit groups.

## Explicit non-goals
Phase 10a does not implement:
- a validated patient/device-specific transmural CVP measurement;
- a clinically validated PEEP-to-ECMO-flow dose response;
- detailed cannula collapse/chatter physics beyond the existing reduced-order model;
- Phase 10b FdO2/systemic mixing-extraction work;
- Harlequin/preductal-postductal physiology;
- Phase 11 work.
