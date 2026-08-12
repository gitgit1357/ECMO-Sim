# Phase 9b.0 — Typed Scenario→Mechanism Activation Feasibility Audit
Date: 2026-08-11
Status: AUDIT COMPLETE
Conclusion: **EXISTING PRIMITIVES SUFFICE — no new generalized activation surface is needed.**

## 1. Existing path

The current architecture already implements the intended contract:

`ScenarioDefinition / ScenarioStepDefinition`
→ immutable `ActionDefinition(mechanism_id, parameters)`
→ `ScenarioEngine._fire_step()`
→ `ActionExecutor.execute()`
→ immutable `MechanismInvocation`
→ `MechanismRegistry.invoke()`
→ registered typed mechanism handler
→ authoritative owner method/control port
→ `MechanismResult`
→ canonical structured requested/applied/unavailable events.

`ScenarioEngine` explicitly documents that it owns orchestration only and that simulator mutation crosses the `MechanismRegistry` boundary.

## 2. Real callers already demonstrate the contract

The ready hypovolemia scenario/fault path is a real scenario-origin caller:
- fault catalog builds `ActionDefinition(..., "patient.record_blood_loss", ...)`;
- scenario step releases the fault;
- `ActionExecutor` invokes the registry;
- the registered handler calls `UnifiedNeonatalPatient.record_blood_loss()`;
- the volume ledger remains the authoritative owner;
- scenario action requested/applied events are emitted.

Learner-originated volume actions use the same registry boundary with a different source, demonstrating that the mechanism path is source-agnostic while ownership remains centralized.

## 3. Direct-patch audit

A source sweep of `src/neoscenarios` found no scenario path that directly assigns patient/circuit physiology internals. Scenario-engine assignments are confined to its own orchestration runtime state.

Existing registered mechanisms mutate authoritative systems through named owner methods or control setters, not arbitrary reflective field names.

## 4. Gap assessment

The proposed Phase-9b generalized new command surface is **not needed**.

Future mechanisms such as bubble events, vasoactive mechanism classes, or lactate deterioration should follow the existing pattern by adding:
- a named mechanism ID;
- a `MechanismDescriptor`;
- a typed registration/handler for that mechanism family;
- an authoritative owner method/port;
- scenario `ActionDefinition`s that reference that mechanism ID.

There should be **no generic dispatcher accepting arbitrary internal variable names**.

## 5. Naming / event convention

Because no new generalized surface is being built, the existing event/source convention remains authoritative:
- scenario-engine-originated scenario mutations use `source="scenario-engine"`;
- learner actions use `source="learner"`;
- educator/manual release may identify educator at the step-release layer, while actual scenario-owned mechanism application remains routed through the same executor/registry path.

The illustrative `source="scenario"` wording in the roadmap's hypothetical 9b.1 does not apply because 9b.1 is not needed; changing the established source identity would add churn without architectural benefit.

## 6. Stop/rescope criteria evaluation

The audit explicitly allowed success by finding that an existing primitive should be reused instead of building a new generalized contract.

That is the result here.

Conclusion: **STOP NEW-SURFACE IMPLEMENTATION / EXISTING PRIMITIVES SUFFICE.**

This is a successful Phase-9b outcome, not a failure. No 9b.1 generalized implementation should be authorized.

Future phase-specific mechanism registrations remain normal implementation work inside those future phases and do not reopen Phase 9b unless an actual capability gap is demonstrated.

## 7. Existing evidence

Existing tests already exercise the contract, including scenario primitives, Tier-A vertical-slice/orchestration behavior, and ready-scenario catalog behavior. During this audit, a broad combined rerun reached completion output but exceeded the outer execution window during process cleanup; it is therefore recorded as INCOMPLETE rather than converted into a new pass claim. No new test behavior was introduced by this audit.
