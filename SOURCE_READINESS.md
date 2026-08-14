# Source readiness gate

A real record is ready for scoring only when validation can establish all of the
following. A parseable record that fails this checklist may be retained, but must
remain diagnostic and produce a readiness warning.

- source organization, stable URL, and access date are present;
- evaluator, harness owner, and run executor are identified when published;
- immutable model snapshot/API revision and evaluation date are identified;
- benchmark and harness versions are identified;
- metric definition, unit, direction, and workload class are known;
- a cohort key captures materially compatible evaluation settings;
- tools, scaffold, retry policy, effort, context, and pass@k are recorded when relevant;
- provenance tier is assigned and configuration verification is stated;
- an inspectable raw capture or artifact is retained and referenced;
- sample/task/trial counts and uncertainty are preserved when published;
- the record does not collide with a different snapshot or incompatible cohort.

`umi validate` reports schema/referential errors separately from readiness warnings.
No adapter may manufacture missing facts to silence a warning.
