**# Neonatal ECMO Sim Platform — Fix Map v4**

Supersedes \`FIX\_MAP\_v3.md\`. This round converges the roadmap — the remaining changes are implementation-level
refinements to Phase 0b and two additions (structured event schema, scenario determinism), not architectural
changes. Sections not listed below as changed are **\*\*unchanged from v3\*\*** and not repeated in full here except
where needed for context; see v3 for their complete text.

**\*\*Changes in this revision:\*\***
\- 0b: adopted deep-snapshot + main-thread-commit explicitly (not "pick one"), and simplified it using something
  already in the code — \`\_solve()\`'s existing \`cache\_key\` tuple is already the correct snapshot, so the worker
  needs zero access to the live \`UnifiedNeonatalPatient\` object.
\- 0b: corrected the coalescing model — Python threads can't be cancelled mid-solve, so the real design is one
  running (uncancelable, discard-on-completion-if-stale) task plus one pending (overwritten) revision, not a
  queue of obsolete work.
\- 0b: added an open implementation question found by reading \`neocoupling/core.py\`, not raised by either
  critique — the native solve isn't pure C/Fortran, it wraps a Python-level iterate loop around the scipy calls,
  so a plain \`threading.Thread\` may not release the GIL enough to keep Tk responsive. Needs an empirical check,
  possibly \`ProcessPoolExecutor\` instead.
\- 0c/Phase 0 exit: the <500ms–1s long-term native-solve target is no longer a Phase 0 gate — it's tracked as
  performance debt, revisited opportunistically, so P0 doesn't become a perpetual optimization project.
\- Simulation-time semantics: added a structured internal debug log distinguishing \`event\_time\` from
  \`solver\_completion\_time\` (learner-facing log doesn't need both).
\- 1d: event records are now a structured schema, not log strings.
\- 1e: added scenario determinism as a hard rule for \`neoscenarios/\` — seeded RNG owned by the scenario engine,
  no uncontrolled randomness in physiology or GUI code. (Checked: no unseeded randomness exists in the codebase
  today, so this is a clean forward rule, not a retrofit.)
\- 2c: noted result-availability/turnaround delay (sample drawn vs. result posted) as an explicit future
  refinement, not required now.
\- Verdict: the roadmap is mature enough to stop iterating. Moving to Phase 0b implementation next.

**---**

**## Guiding principles — unchanged from v3, keep in project docs verbatim**

Clinical plausibility outranks mathematical fidelity. Scenario actions call mechanisms, not monitor numbers. The
console must never silently present a stale result as current — except labs, which are deliberately frozen at
draw time. (Full text in v3.)

**---**

**## Ongoing discipline: Behavior Contracts (Clinical + System) — unchanged from v3**

Two permanent, parallel suites, not a phase. Clinical Behavior Contracts get preconditions/expected-response/
allowed-exceptions structure; exit bar is "every supported scenario passes, every unsupported one is marked
\`mechanism not implemented\`" — never force a pass by faking a mechanism. System Behavior Contracts cover runtime
correctness (RPM-only stays cheap, blood-loss never blocks Tk, rapid changes only let the newest revision win).
Full text in v3.

**---**

**## Phase 0 — Close the real-time gap completely**

**### 0a. Native physiology caching — DONE, closed. Unchanged from v3.**

**### 0b. Fix the invalidation-event freeze — OPEN, this is the real remaining P0 work**

**\*\*Chosen design: deep/isolated solve snapshot + main-thread commit (v3's "option 2"), not a mutation queue.\*\***
Rationale, and it's a good one: learner/scenario actions should land in the authoritative live state immediately
regardless of whether a physiology solve is in flight — UI responsiveness shouldn't depend on a worker
serialization queue.

**\*\*Concrete simplification, found by re-reading \`neopatient/core.py\`'s actual cache implementation:\*\*** the
"snapshot" this design needs already exists. \`\_solve()\`'s \`cache\_key\` tuple (\`weight\_kg\`, \`lung\_run\_s\`,
\`circulation\_run\_s\`, \`peep\_cmh2o\`, \`airway\_opening\_pressure\_cmh2o\`, \`fio2\`) plus
\`self.state.blood\_volume\_delta\_ml\` are the *\*entire\** input surface of \`run\_coupled\_neonate()\` — and
\`UnifiedPatientConfig\`/\`AirwayPort\` are already frozen (immutable) dataclasses. So the worker doesn't need a
deep copy of the live \`UnifiedNeonatalPatient\` object at all — it needs six primitives, all of which are already
being read out and hashed today. Concretely:
\- Main thread, on any cache-invalidating event: build the same \`cache\_key\` tuple + \`blood\_volume\_delta\_ml\` float
  it already builds today, tag it with an incrementing revision counter, hand those primitives (not the object)
  to the worker.
\- Worker calls \`run\_coupled\_neonate(...)\` with only those primitive arguments — it never touches
  \`self.state\`, \`self.\_physiology\_cache\*\`, or anything else on the live patient object. No shared mutable state
  enters the worker at all.
\- Main thread, on worker completion: if the returned revision is still the current one requested, commit the
  result into \`self.\_physiology\_cache\_key\` / \`self.\_physiology\_cache\_blood\_volume\_delta\_ml\` /
  \`self.\_physiology\_cache\` — exactly the three fields \`\_solve()\` already writes on a cache miss today. If the
  revision is stale, discard the result and do nothing.

This means 0b is smaller than either critique round implied: it's "extract the existing cache-miss path into a
function callable off-thread with primitive inputs, plus a revision-checked commit," not a redesign of state
ownership.

**\*\*Corrected coalescing model — no queue, and nothing gets "dropped" mid-flight:\*\***
Python threads can't be safely cancelled once running, so revision N-1's solve, once started, runs to
completion regardless — it just gets its result discarded if something newer has arrived by the time it
finishes. The actual model needed is one *\*active\** slot (uncancelable, running) and one *\*pending\** slot
(overwritten by whatever's newest, never queued):
\`\`\`
active = revision 10 (running, cannot be interrupted)
pending = revision 11
  -> revision 12 arrives -> pending = revision 12 (11 is simply gone, never ran)
  -> revision 13 arrives -> pending = revision 13
revision 10 completes -> its result is discarded if pending exists and differs
                       -> immediately start solving pending (13); pending slot clears
\`\`\`
No queue of obsolete work ever accumulates. This is a small, standard "trailing-edge debounce" pattern — don't
build anything fancier than the two-slot version above.

**\*\*Open implementation question — verify empirically, don't assume threading is sufficient:\*\***
\`neocoupling/core.py\`'s \`run\_coupled\_neonate()\` isn't a single opaque C call — it wraps \`scipy.solve\_ivp\`
(LSODA) inside a Python-level loop ("iterate flow -> venous extraction -> gas -> PVR a few times"). NumPy/SciPy's
compiled routines typically release the GIL during their internal work, but the Python-level glue around them
(dataclass construction, the iteration loop itself, unit conversions) does not. Whether a plain
\`threading.Thread\` running this keeps the Tk event loop under the <50ms blocking target from 0c, or whether
enough of the cost is pure-Python that a \`ProcessPoolExecutor\` is actually needed instead, is an open question —
**\*\*benchmark both during implementation\*\*** rather than assuming threading is sufficient just because it's simpler.
If a process pool is needed: good news, the inputs (six primitives) and output (\`CoupledResult\`, a plain
dataclass) are both trivially picklable, so the switch costs little if threading turns out not to be enough.

**\*\*Simulation-time semantics — unchanged framing from v3, one addition:\*\***
The result of a solve is "given the new conditions, here is the patient's updated equilibrium state," never
"here are N seconds of physiologic evolution." Add a structured internal debug/event log (separate from the
learner-facing event log in 1d) that records both \`event\_time\` (when the learner/scenario action happened) and
\`solver\_completion\_time\` (when the resulting revision was committed) — e.g.
\`10:32:04.200 hemorrhage 20 mL\` / \`10:32:08.731 physiology revision 184 committed\`. Useful for debugging and
debrief later; the learner-facing log doesn't need the second timestamp.

**\*\*Full 0b acceptance criteria (revised):\*\***
\- [ ] Tk main thread never blocks on a native-physiology solve, measured directly
\- [ ] GUI callback/event-loop blocking stays <50ms even during a forced recompute — confirm this holds with a
      plain thread, or switch to a process pool if it doesn't (see open question above)
\- [ ] Routine (cache-hit) simulation/display tick stays <100–150ms
\- [ ] No physiologic event blocks the UI thread for >250ms
\- [ ] Native-solve latency ≤5s, confirmed on real target hardware — **\*\*not\*\*** gated on hitting the <500ms–1s
      long-term target (see Phase 0 exit criteria below)
\- [ ] Stale results are rejected: single active/pending slot design, no queue, correct discard-on-stale behavior
\- [ ] Cache commit (\`\_physiology\_cache\*\` mutation) happens only on the main thread, never inside the worker
\- [ ] Simulation-time semantics documented and matched by the code, including the internal
      \`event\_time\`/\`solver\_completion\_time\` log
\- [ ] System Behavior Contracts for RPM-only, blood-loss, and rapid-PEEP/FiO2 scenarios all pass

**### 0c. Performance contract — unchanged split (UI responsiveness / native solve latency / state freshness),**
one change: the native-solve long-term target (<500ms–1s) is explicitly **\*\*not\*\*** a Phase 0 exit gate — see below.

**### 0d, 0e — unchanged from v3.**

**\*\*Phase 0 exit criteria (revised):\*\*** 0a done. 0b's acceptance list above satisfied, including the ≤5s interim
solve-latency target on real hardware. 0c's UI-responsiveness and state-freshness metrics met. 0d passing. 0e
confirmed on target hardware. \*\*The <500ms–1s long-term native-solve target is logged as tracked performance
debt and does not block moving to Phase 1\*\* — this is the one deliberate scope cut in this revision, made so P0
doesn't become a perpetual optimization project. Revisit it opportunistically, or explicitly if Behavior
Contracts or real usage later show the ≤5s interim latency is actually hurting crisis-scenario training value.

**---**

**## Phase 1 — Architecture consolidation**

**### 1a, 1b, 1c — unchanged from v3 (JS-engine audit before design; port intent, retire runtime by default;**
capability matrix with the \`Learner-operable\` column).

**### 1d. Event-record contract — now a structured schema, not log strings**
Each event is a record, not a formatted string:
\`\`\`
timestamp, event\_type, source, target, action, old\_value, new\_value, revision, metadata
\`\`\`
The UI renders a human string from it (\`PEEP 5 -> 8\`) when needed; tests and future tooling (debrief, instructor
timeline, scoring, replay, scenario branching) inspect the structured fields directly instead of parsing log
text. Define this schema now, alongside \`neoscenarios/\` design, even though the Scenario Log tab still waits for
Phase 2e — every intervention/scenario action built from here forward emits to this stream in this shape from
day one.

**### 1e. \`neoscenarios/\` design — one new hard rule: scenario determinism**
Add before any scenario code is written: \*\*all scenario randomness must come through a seeded RNG owned by the
scenario engine; no uncontrolled random calls inside physiology or GUI code.\*\* This matters for regression
testing, instructor comparison ("run VA hemorrhage scenario, seed X, twice, get the same initial condition and
event progression unless learner actions differ"), research/evaluation use, and reproducing reported bugs.
Checked the current codebase for this — no unseeded randomness exists anywhere in \`src/\` today, so this is a
clean rule to establish going forward, not a cleanup task. Otherwise unchanged from v3 (\`engine.py\`, \`events.py\`,
\`triggers.py\`, \`actions.py\`, \`complications/\`, \`scenarios/\`, \`logging.py\`; actions call mechanisms, never assign
monitor values).

**\*\*Phase 1 exit criteria:\*\*** unchanged from v3, plus the determinism rule is written down and enforced (e.g., a
lint/test rule flagging any \`import random\` / \`numpy.random\` call outside the scenario engine's seeded RNG).

**---**

**## Phase 2 — Complete the learner loop (GUI tabs)**

Unchanged order and content from v3: Patient Monitor -> Interventions (with the formulary-sim scope guardrail)
-> Labs (ordered-test distinction, frozen sample timestamps) -> Ventilator (gated on the \`AirwayPort\` backend
extension) -> Scenario Log (renders the Phase 1d event stream, gated on the Phase 1 scenario-engine decision).

**\*\*One noted future refinement to 2c, not required now:\*\*** eventually distinguish sample-drawn time from
result-available time (\`sample drawn: 10:32\` / \`result posted: 10:35\`) to model realistic lab turnaround. Purely
additive on top of the existing frozen-timestamp design — doesn't need to be solved before 2c ships.

**---**

**## Phase 4 — Physiology fidelity gaps (behavior-first, gated by Behavior Contract results)**

Unchanged from v3. Model complexity earns its way in by fixing a demonstrated Clinical Behavior Contract
failure, never added because it seemed theoretically incomplete. Myocardial dysfunction already has a known
failure and earns investigation; the oxygenator proxy and cannula resistance may need nothing beyond disclosure
if their contracts pass; CKRT scope stays phased (real numbers now, full prescription surface later).

**---**

**## Phase 5 — Broader validation and commercial readiness**

Unchanged from v3. Lock the education/simulation-training positioning now; defer formal commercial/IP review
until there's a product worth reviewing; keep UX architecture (alarms, control placement, latency) as functional
priority, separate from and ahead of cosmetic polish.

**---**

**## How this actually runs — unchanged diagram from v3**

Behavior Contracts (Clinical + System) run continuously underneath Phase 0 -> Phase 1 -> Phase 2 -> Phase 4 ->
Phase 5. Never again let "N tests pass" stand in for "the product behaves correctly for a learner."

**## Next up**

**\*\*Phase 0b, exactly as specified above, and nothing more.\*\*** The design is now concrete enough to build directly:
reuse the existing \`cache\_key\` tuple as the snapshot, run the solve off-thread with only primitive inputs, keep
a single active/pending slot with no queue, commit only from the main thread on a revision match, and verify
empirically whether a plain thread is sufficient or a process pool is needed for the GIL question above. Once
0b's acceptance checklist passes together with the System Behavior Contracts and a real-target-hardware
benchmark, Phase 0 is closed — including accepting the ≤5s interim solve latency and logging the sub-second
target as tracked debt rather than continuing to optimize — and the next work moves to Phase 1's JS-engine
audit. This roadmap is treated as settled as of this version; further changes to it should come from things
learned while building Phase 0b, not from another critique pass on paper.