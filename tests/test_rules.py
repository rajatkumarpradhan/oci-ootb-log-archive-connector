import os
import unittest

from lac_check import model, rules

EX = os.path.join(os.path.dirname(__file__), "..", "examples")


class TestMessy(unittest.TestCase):
    def setUp(self):
        env = model.load(os.path.join(EX, "env_messy.json"))
        self.findings = rules.run_all(env)

    def test_disabled_connector_is_critical(self):
        f = [x for x in self.findings if x.rule == "LAC003"]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "CRITICAL")

    def test_no_lifecycle_rule_is_high(self):
        self.assertTrue(any(f.rule == "LAC001" and f.severity == "HIGH"
                            for f in self.findings))

    def test_oversized_rollover_flagged(self):
        self.assertTrue(any(f.rule == "LAC004" for f in self.findings))

    def test_missing_sch_alarm_flagged(self):
        self.assertTrue(any(f.rule == "LAC005" for f in self.findings))

    def test_retention_ok_not_flagged(self):
        self.assertFalse(any(f.rule == "LAC002" for f in self.findings))

    def test_sorted_critical_first(self):
        ranks = [rules.RANK[f.severity] for f in self.findings]
        self.assertEqual(ranks, sorted(ranks))

    def test_total_count(self):
        self.assertEqual(len(self.findings), 4)


class TestRetentionRule(unittest.TestCase):
    def _env_with(self, retention_days, batch_ms):
        return {
            "connector": {"name": "c", "state": "ENABLED",
                          "source": {"kind": "logging", "log_group_id": "lg"},
                          "target": {"kind": "objectstorage", "bucket": "b",
                                     "batch_rollover_ms": batch_ms}},
            "bucket": {"name": "b",
                       "lifecycle_rules": [{"action": "delete", "days": 365}]},
            "log_group": {"id": "lg", "retention_days": retention_days},
            "alarms": [{"metric_namespace": "oci_sch", "enabled": True}],
        }

    def test_fires_when_retention_shorter_than_batch(self):
        findings = rules.run_all(self._env_with(0, 3600000))
        self.assertTrue(any(f.rule == "LAC002" for f in findings))

    def test_quiet_when_retention_covers_batch(self):
        findings = rules.run_all(self._env_with(30, 3600000))
        self.assertEqual(findings, [])


class TestClean(unittest.TestCase):
    def test_clean_env_has_no_findings(self):
        env = model.load(os.path.join(EX, "env_clean.json"))
        self.assertEqual(rules.run_all(env), [])


if __name__ == "__main__":
    unittest.main()
