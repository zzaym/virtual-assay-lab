# Data and model acceptance

## Provenance and scope

Bashi et al., *Cancer Discovery* 2024, [Large-scale Pan-cancer Cell Line Screening Identifies Actionable and Effective Drug Combinations](https://doi.org/10.1158/2159-8290.CD-23-0388). Source: [author Figshare project](https://figshare.com/projects/163378), CC BY 4.0. `data/source/manifest.json` pins the v2 well-level and observed single-agent exports by Figshare article, file ID, MD5 and SHA256. Model targets are observed combination `inhibition` and single-agent `y`; author `yhat`, Bliss/HSA scores and fitted rankings are excluded.

The extraction contains 550,350 combination wells, 161,631 single-agent wells and 1,022 physical plates from the seven reported repeat-screen cell lines. Physical keys are project + plate barcode + well position. Conflicting duplicate measurements fail ingestion; no duplicate physical wells were removed. Missing doses or measurements fail ingestion. Experimental projects remain separate; the released demo uses GDSC_007 only. Repeated plates are not relabeled as new biological batches.

Raw intensity and published inhibition obey an affine normalization with clipping at 0 and 1. On uncensored wells we reconstruct control means from `intensity = vehicle - (vehicle - blank) × inhibition`. Both means are **derived**, not exported raw control replicates. All 1,022 reconstructed plate scales pass the physical/range and inverse-normalization residual gate. Censored observations are excluded from this reconstruction, retained as published for model fitting and reported in the machine-readable audit. Controls in the simulator therefore have inferred means; their separate real noise distributions cannot be recovered from this export.

The real study uses pre-seeded 1,536-well plates with 7.5 uL media, 72 h drug treatment at 37 C / 5% CO2 and approximately 0.2% DMSO, followed by 2.5 uL CellTiter-Glo 2.0 and 10 min incubation. The original 24 h pre-dosing incubation is considered complete when a virtual plate is allocated. The original large control layout is reduced for the 96-well task budget. The virtual blank represents a media-only/no-cell well, not a killed-cell positive control.

## Model and evaluation

Whole physical plates are split 70/15/15 with deterministic, outcome-independent hash ordering, stratified by cell line and project. Nine positive internal dose coordinates (level indices 1/3/5 × 1/3/5) are removed from every combination curve fit. Single-agent curves use separate observed monotherapy measurements. Identical drugs share their monotherapy curves across pairs in the same cell/context.

Each of 16 worlds fits a Hill single-agent response, Bliss independence baseline and a gated Matérn-2.5 GP residual in log concentration space. The gate makes both zero-dose axes exactly equal to the corresponding single drug. Whole-plate bootstrap resampling is shared across pairs. One ensemble member is fixed for an entire run; reading a new well does not redraw the underlying biology.

Measurement variability is estimated from calibration residuals and its scale calibrated on validation observations. These residuals contain unexplained variation **and model discrepancy**; they are not pure isolated instrument noise. A virtual plate selects one calibration-plate background/vehicle scale; Gaussian normalized residual variation is mapped back to RLU and truncated at zero. Control noise uses this residual model because individual raw control wells are unavailable. This is an explicit modeling assumption, not independently validated control-well physics. No extra pipetting noise, contamination, edge effect, temperature response or arbitrary background model is added.

133 eligible scenes were attempted under the declared first-context/demo scope; 106 pass the release gates. Every attempted case, optimizer warning and failure reason is in `model-validation.json`. Released counts: A375 17, C32 15, HT-29 12, MHH-ES-1 16, PC-14 14, SW620 14, U-2-OS 18. Released internal-dose test MAE is **0.0539164** and test 90% prediction-interval coverage **0.904787**. Per-scene interpolation MAE is at most 0.10 and test coverage is 80–98%; cross-plate metrics are reported per scene.

**Selection caveat:** model and noise parameters never fit test data, but locked test thresholds decide scene release. Thus released-scene metrics are acceptance metrics after selection, not an unbiased generalization claim. The complete attempted-scene distribution and rejection reasons must accompany them. Plate-level tags do not establish independent biological batches. The model cannot infer arbitrary new drugs, cells, exposure times, media, temperatures or out-of-range doses.

## Instrument and task realism

Echo CSV is a real picklist format with nL volumes. The executor models a 2.5 nL transfer increment and a 384-LDV-DMSO source working floor of 3 uL. Stock ladders are pre-prepared to yield in-range exposures with small transfers. Target concentrations are never trusted: actual transferred compound amounts divided by actual exposure volume drive the response model. CTG dilution is applied after exposure and does not retroactively change exposure dose.

PyLabRobot 0.2.2 LiquidHandler.dispense and PlateReader.read_luminescence are real frontend calls. The backends belong to this project and connect to the stateful simulator. The preloaded detection dispenser/tip geometry is illustrative. No robot motion, optical kinetics, robotic collision model or solubility physics is claimed. A CSV is structurally compatible with Echo import; it has not been validated on a physical Echo instrument.

The simulator score uses the fixed hidden expected response. Observed HSA and a within-plate nonparametric 95% bootstrap interval come from confirmation wells. Simple regret uses a 41×41 log-dose reference grid per pair, not a claimed exact continuous optimum. Novel doses remain model predictions rather than measured wet-lab validation. Budget consumption and score are separate; efficient evidence collection is reported without rewarding discarded/invalid actions.

Sources: [original study](https://doi.org/10.1158/2159-8290.CD-23-0388), [Echo Cherry Pick](https://www.beckman.com/liquid-handlers/software/echo/cherry-pick), [Echo 550 series](https://www.beckman.com/liquid-handlers/echo-acoustic/echo-550-series), [PyLabRobot PlateReader interface](https://docs.pylabrobot.org/0.2.0/api/_autosummary/pylabrobot.plate_reading.plate_reader.PlateReader.html).
