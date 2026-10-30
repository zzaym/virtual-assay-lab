# Virtual Assay Lab scientist task

You are operating a calibrated virtual cell viability assay. Actually execute multiple rounds and submit evidence; a proposal alone does not complete the task. Use English rationales and commentary. Do not ask the user questions.

Your goal is to find and independently confirm a drug combination that improves inhibition over BOTH matched-dose single drugs. You can also submit an evidence-supported no-hit conclusion. The simulator score is 100 * max(0, combination inhibition - max(single A inhibition,single B inhibition)), and requires expected combination inhibition >=0.5 and valid independent confirmation.

## Available tools

- `from lab_client import LabClient; lab=LabClient(); observation=lab.observe()` gives SOP, six pairs, source stocks, inventory and measurements. Environment variables provide your run capability. No initial results are given.
- `lab.step('create_plate',wells=[...],blank_wells=[...],rationale='...')` creates a new independent virtual plate P1/P2/P3. 1536 physical positions A1:AF48; at most 96 allocated wells per plate and 288 experimental wells total. Controls, blanks and repeats consume wells. Allocate only wells you will actually use.
- Generate and save a real Echo picklist CSV (see `example_picklist.csv`). Use exact headers, `stocks`, `384LDV_DMSO`, source well, destination plate P1 etc, destination well and Transfer Volume in **nL**, multiples of 2.5. `lab.echo(path,rationale,dry_run=True)` checks without consumption; `lab.echo(path,rationale)` executes it.
- Stock concentrations are uM; delivered amount = stock uM * transfer uL. Final exposure concentration = delivered amount / actual total uL. Initial medium is 7.5 uL. Every cell-containing well must receive exactly 15 nL DMSO total, including the DMSO solvent of all drug transfers. DMSO-only stock is P24. A convenient matched-dose design uses 7.5 nL per drug in combinations; singles receive 7.5 nL drug + 7.5 nL DMSO; vehicles receive 15 nL DMSO. Blank wells contain medium without cells and need no drug/solvent.
- `lab.step('incubate',plate_id='P1',hours=72,temperature_C=37,co2_percent=5,rationale='...')` validates executed doses. Only published dose ranges and one of the six pairs are supported. Unsupported experimental conditions fail rather than fabricate feedback.
- `from lab_instruments import detect_and_read; import asyncio; raw=asyncio.run(detect_and_read(lab,'P1'))` runs genuine PyLabRobot LiquidHandler.dispense and PlateReader.read_luminescence frontends connected to this simulator. This adds 2.5 uL CellTiter-Glo, waits 10 simulated minutes and measures raw RLU. Repeat reading returns the same endpoint measurement. Instrument helper is illustrative; the model does not simulate mechanical robot motion.
- Use `lab.observe()` to obtain all measured RLU and executed compositions. Normalize using your **own plate controls**, inhibition = 1 - (RLU - mean blank)/(mean vehicle - mean blank). Do not silently clip uncertainty or regard measured HSA as noise-free.
- Analyze locally with numpy, scipy, sklearn, matplotlib. Write analysis artifacts and rationale. There is no automatic experiment recommender. Decide how to split exploratory doses, monotherapies and replication. Read each round before planning the next. Announce decisions in concise English commentary.

## Confirmation and submission

At most 3 plates. Reserve at least 15 wells on a new plate **created after an earlier plate was measured**. Confirm your chosen combination, single A at exactly its combination dose, single B at exactly its combination dose, vehicle and blank. At least 3 distinct wells per group; preferably more if budget permits. Every group must be on that independent confirmation plate.

`lab.step('submit',pair_id='D123+D456',plate_id='P3',groups={'combination':[...],'single_a':[...],'single_b':[...],'vehicle':[...],'blank':[...]},conclusion='...')` returns the simulator score and observed uncertainty. Alternatively `lab.step('submit',no_hit=True,conclusion='...')` after collecting evidence. Score is not proof of a wet-lab discovery. Novel doses are predictions within a calibrated model; replicates do not establish biological reproducibility.

Do not access source datasets, model weights, other runs, operator routes, other tasks or internet datasets. The worker container has only this workspace, SDK and model-provider connectivity. Stay within that boundary. If an operation fails, inspect the error and current state before retrying; physical operations already committed are not rolled back. Do not print OAuth credentials. Finish with a concise English evidence report and actually submit to the service.
