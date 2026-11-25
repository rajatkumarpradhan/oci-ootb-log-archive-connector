"""CLI: gate a log-archive environment export. Exit 0 clean, 2 findings, 3 error."""
import sys

from . import model, rules

USAGE = "usage: python -m lac_check run-all ENV_JSON"


def run_all(path, out=None):
    out = out or sys.stdout
    env = model.load(path)
    findings = rules.run_all(env)
    name = env["connector"].get("name", env["connector"].get("id", "connector"))
    print("Log archive gate - connector %r, target bucket %r"
          % (name, env["bucket"].get("name")), file=out)
    for finding in findings:
        print(finding.line(), file=out)
    bad = sum(1 for f in findings if f.severity in ("CRITICAL", "HIGH"))
    if findings:
        print("RESULT: gate failed - %d CRITICAL/HIGH / %d total finding(s) "
              "(exit code 2)" % (bad, len(findings)), file=out)
        return 2
    print("RESULT: log archive gate clean (exit code 0)", file=out)
    return 0


def main(argv):
    if len(argv) == 2 and argv[0] == "run-all":
        try:
            return run_all(argv[1])
        except model.LoadError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 3
    print(USAGE, file=sys.stderr)
    return 3
