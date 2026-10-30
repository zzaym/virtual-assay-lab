import unittest
from pathlib import Path
from unittest.mock import patch

from assay_replay import replay_observation
from archive_store import bundle,read_archive,read_json
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class ArchiveTests(unittest.TestCase):
    def test_every_downloadable_artifact_is_bundled(self):
        total=0
        for row in read_archive("/admin/runs"):
            for artifact in bundle(row["run_id"])["artifacts"]:
                path=(ROOT/artifact["url"]).resolve()
                self.assertTrue(path.is_relative_to((ROOT/"data/artifacts").resolve()))
                self.assertTrue(path.is_file(),f"Missing published artifact: {artifact['url']}")
                path.read_bytes()
                total+=1
        self.assertGreater(total,0)

    def test_all_archived_runs_reconstruct(self):
        runs=read_archive("/admin/runs")
        self.assertEqual(len(runs),35)
        self.assertEqual(len(read_archive("/admin/agents")),4)
        for row in runs:
            latest=bundle(row["run_id"])["observation"]
            final=replay_observation(latest,len(latest["events"])-1)
            self.assertEqual(final["plates"],latest["plates"])
            self.assertEqual(final["result"],latest["result"])
            self.assertEqual(final["wells_used"],latest["wells_used"])

    def test_read_only_and_path_boundaries(self):
        with self.assertRaises(ValueError):read_archive("/runs/0123456789abcdef/jobs")
        with self.assertRaises(ValueError):bundle("../../runtime/operator.key")
        with self.assertRaises(ValueError):read_json("../../runtime/operator.key")

    def test_ui_offline_timeline_and_results(self):
        with patch("socket.create_connection",side_effect=AssertionError("Deployed replay must work without network")):
            app=AppTest.from_file(str(ROOT/"streamlit_app.py"),default_timeout=30).run()
            self.assertEqual(len(app.exception),0)
            self.assertFalse(any(b.label in ("Start Agent","Stop Agent") for b in app.button))
            self.assertEqual(next(m.value for m in app.metric if m.label=="Simulator score"),"15.80")
            next(b for b in app.button if b.label=="First").click().run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(next(m.value for m in app.metric if m.label=="Experimental wells"),"0 / 288")
            self.assertEqual(next(m.value for m in app.metric if m.label=="Simulator score"),"Pending")
            next(s for s in app.slider if s.label=="Laboratory event timeline").set_value(240).run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(next(m.value for m in app.metric if m.label=="Experimental wells"),"96 / 288")
            next(b for b in app.button if b.label=="Last").click().run()
            self.assertEqual(len(app.exception),0)
            self.assertEqual(next(m.value for m in app.metric if m.label=="Simulator score"),"15.80")

if __name__=="__main__":unittest.main()
