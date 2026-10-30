# Virtual Assay Lab — Streamlit replay

Original Streamlit UI, configured as a read-only archive. Includes all 35 run records (33 completed and two infrastructure attempts), four agent trajectories, protocols, code, results and validation reports. No API server, Docker, credentials, model weights or agent execution is required.

## Deploy on Streamlit Community Cloud

| Field | Value |
|---|---|
| Repository | `zzaym/virtual-assay-lab` |
| Branch | `main` |
| Main file path | `streamlit_app.py` |
| Python version in Advanced settings | `3.11` |
| Secrets | Leave empty |
| App URL | An available name, for example `virtual-assay-lab-zzaym` |

Click Deploy. Dependencies are pinned in requirements.txt; the committed data/ directory is the only data source. Deployment never contacts the original local laboratory.

## Run locally

```sh
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -s tests -v
```

Experiment / Analysis / Trajectory / Protocol & replay / Results retain the original layout. Replay supports timeline dragging, play/pause, steps and milestone jumps; Final snapshot shows the final state. There is no Start Agent or Stop Agent control. Agent files and reports are downloadable under Protocol & replay.

Legacy logs have no reliable lab-event wall-clock timestamps. Laboratory state replays exactly; complete provider trajectories are explicitly labeled and opt-in. Scores and hidden surfaces appear at submission. The data files are public archive records, so this viewing convention is not an access-control boundary.

scripts/export.py is an optional maintainer-only tool to refresh the public data using the original lab development environment. It is never imported or run by the deployed app. It rejects known credentials before publication.

GitHub Pages has been unpublished and its publishing source disabled. This repository is now the Streamlit source.

Data: Bashi et al., Cancer Discovery 2024, DOI 10.1158/2159-8290.CD-23-0388; author Figshare project 163378, CC BY 4.0. Response surfaces are calibrated model predictions, not new wet-lab validation. Pinned source hashes and all attempted-scene validation reports are included.
