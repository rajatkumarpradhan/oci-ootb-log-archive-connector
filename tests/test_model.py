import os
import tempfile
import unittest

from lac_check import model

EX = os.path.join(os.path.dirname(__file__), "..", "examples")


class TestLoad(unittest.TestCase):
    def _write(self, text):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def test_load_ok(self):
        env = model.load(os.path.join(EX, "env_messy.json"))
        self.assertEqual(env["connector"]["name"], "audit-logs-to-archive")

    def test_rejects_bad_json(self):
        bad = self._write("{oops")
        with self.assertRaises(model.LoadError):
            model.load(bad)

    def test_rejects_missing_file(self):
        with self.assertRaises(model.LoadError):
            model.load("/no/such/file.json")

    def test_rejects_missing_section(self):
        bad = self._write('{"connector": {}, "bucket": {}, "log_group": {}}')
        with self.assertRaises(model.LoadError):
            model.load(bad)

    def test_rejects_wrong_source_kind(self):
        bad = self._write(
            '{"connector": {"state": "ENABLED",'
            ' "source": {"kind": "streaming"},'
            ' "target": {"kind": "objectstorage"}},'
            ' "bucket": {}, "log_group": {}, "alarms": []}')
        with self.assertRaises(model.LoadError):
            model.load(bad)

    def test_rejects_wrong_target_kind(self):
        bad = self._write(
            '{"connector": {"state": "ENABLED",'
            ' "source": {"kind": "logging"},'
            ' "target": {"kind": "functions"}},'
            ' "bucket": {}, "log_group": {}, "alarms": []}')
        with self.assertRaises(model.LoadError):
            model.load(bad)


if __name__ == "__main__":
    unittest.main()
