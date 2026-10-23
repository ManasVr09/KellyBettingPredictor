# Dashboard performance

The existing simulator, strategy names, probability ladder, result schema, and all report calculations are preserved. The current seeded simulation is retained in session state. Bounded eight-entry report/chart caches and a sixteen-entry probability-ladder cache reuse static presentation work; keys include simulation parameters, axis settings where applicable, and implementation signatures. Caveat text remains in the existing expander and is evaluated only when opened.

No local model refactor was included. Tests check exact report arrays against the existing engine, repeat-run table equality, and seed-change invalidation. Streamlit 1.60+ is required for state-tracked expanders.
