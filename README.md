# ears
lets machines hear phonetically rather than speech-to-text

## Architecture and research (draft)

The current research implementation lives on the draft feature branch, not yet in the default branch.

- [Architecture](docs/ARCHITECTURE.md) — auditory pipeline and non-negotiable evidence boundaries.
- [Nine-upstream intake](docs/HARMONIC_ARCHITECTURE_INTAKE.md) — component-by-component reusable ideas, exclusions, and licensing constraints.
- [Research and decisions](docs/RESEARCH_AND_DECISIONS.md) — documented design choices, uncertainties, and evidence classes.
- [Implementation backlog](docs/NEXT_IMPLEMENTATION.md) — actionable research, validation and integration tasks.

Minimal NumPy acoustic analysis: `ears/acoustics.py`; synthetic test source: `tests/test_acoustics.py`. Tests have not yet been executed or externally qualified.
