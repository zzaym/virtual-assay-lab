# Virtual Assay Lab — public replay

Read-only static archive of real Codex-designed virtual assays. No agent execution, backend API, credentials or model calls. All 35 historical run records (33 completed, two infrastructure failures), four provider trajectories, protocols, analysis files, scores and validation reports are included.

Serve `dist/` using a static HTTP server. No build dependencies are required. `node scripts/test-replay.mjs` verifies every archived state and Python/JavaScript reconstruction parity. `scripts/export.py` refreshes public observations from the local lab and rejects known credentials before publication.

Select a run, drag the timeline, play/pause, jump to a milestone, and inspect Laboratory / Analysis / Trajectory / Results / Data & validation. Legacy provider logs have no reliable lab-event wall-clock alignment; full trajectories are explicitly labeled and opt-in. Scores and hidden surfaces appear at submission. The underlying static files are public archive data, not a security boundary.

Data: Bashi et al., Cancer Discovery 2024, DOI 10.1158/2159-8290.CD-23-0388; author Figshare project 163378, CC BY 4.0. Public response surfaces are calibrated model predictions, not new wet-lab validation. Source hashes and complete selection reports are included. Plotly.js is bundled locally under its MIT license.

Deploy `dist/` as the root of a GitHub Pages publishing branch. All asset paths are relative, so project subpaths are supported.
