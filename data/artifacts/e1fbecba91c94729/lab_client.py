"""Public capability-scoped SDK. Contains no assay model or server filesystem imports."""
import json
import os
import time
from pathlib import Path

import httpx


class LabClient:
    def __init__(self, url=None, run_id=None, token=None):
        self.url=(url or os.environ["ASSAY_URL"]).rstrip("/")
        self.run_id=run_id or os.environ["ASSAY_RUN_ID"]
        self.http=httpx.Client(timeout=60,headers={"X-Run-Token":token or os.environ["ASSAY_RUN_TOKEN"]})

    def observe(self):
        response=self.http.get(f"{self.url}/runs/{self.run_id}");response.raise_for_status()
        return response.json()

    def step(self, operation, **arguments):
        response=self.http.post(f"{self.url}/runs/{self.run_id}/jobs",json={"type":operation,**arguments})
        response.raise_for_status();job=response.json()
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            response=self.http.get(f"{self.url}/runs/{self.run_id}/jobs/{job['job_id']}");response.raise_for_status()
            status=response.json()
            if status["status"]=="completed":return status["result"]
            if status["status"] in ("failed","interrupted"):raise RuntimeError(f"Laboratory job {job['job_id']}: {status['error']}")
            time.sleep(.05)
        raise TimeoutError(f"Job {job['job_id']} is still running. Inspect its status before retrying any physical operation.")

    def echo(self, path, rationale, dry_run=False):
        return self.step("echo",picklist=Path(path).read_text(),rationale=rationale,dry_run=dry_run)

    def save_observation(self,path="observation.json"):
        Path(path).write_text(json.dumps(self.observe(),indent=2))


if __name__=="__main__":
    print(json.dumps(LabClient().observe(),indent=2))
