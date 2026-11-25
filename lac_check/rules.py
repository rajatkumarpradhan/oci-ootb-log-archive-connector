"""Gate rules for a Logging -> Service Connector Hub -> Object Storage archive."""

RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


class Finding:
    def __init__(self, rule, severity, message):
        self.rule = rule
        self.severity = severity
        self.message = message

    def line(self):
        return "[%-8s] %s %s" % (self.severity, self.rule, self.message)


def check(env):
    findings = []
    connector = env["connector"]
    bucket = env["bucket"]
    log_group = env["log_group"]
    alarms = env["alarms"]

    if connector["state"] != "ENABLED":
        findings.append(Finding("LAC003", "CRITICAL",
            "service connector is %s while log group archiving is expected; "
            "logs are silently not being archived" % connector["state"]))

    rules_list = bucket.get("lifecycle_rules", [])
    if not rules_list:
        findings.append(Finding("LAC001", "HIGH",
            "archive bucket %r has no lifecycle rule; objects accumulate "
            "forever and storage cost grows unbounded" % bucket.get("name")))

    retention = log_group.get("retention_days", 30)
    batch_ms = connector["target"].get("batch_rollover_ms", 0)
    if retention * 24 * 3600 * 1000 < batch_ms:
        findings.append(Finding("LAC002", "HIGH",
            "log group retention (%d days) is shorter than the connector batch "
            "window; logs can expire before the connector ships them"
            % retention))

    rollover_mb = connector["target"].get("batch_rollover_mb", 0)
    if rollover_mb and rollover_mb > 100:
        findings.append(Finding("LAC004", "MEDIUM",
            "batch rollover %d MB exceeds the Service Connector Hub 100 MB "
            "object rollover limit; lower it to 100 MB or less" % rollover_mb))

    sch_alarms = [a for a in alarms
                  if a.get("metric_namespace") == "oci_sch" and a.get("enabled")]
    if not sch_alarms:
        findings.append(Finding("LAC005", "MEDIUM",
            "no enabled Monitoring alarm watches Service Connector Hub "
            "failures; a broken connector would page nobody"))

    return findings


def sort_key(f):
    return (RANK[f.severity], f.rule, f.message)


def run_all(env):
    findings = check(env)
    findings.sort(key=sort_key)
    return findings
