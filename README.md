# oci-ootb-log-archive-connector

**Category: OOTB project - wires built-in (native) OCI services, with a
custom gate around them.** The pipeline itself is 100% native OCI:

1. **OCI Logging** - a log group (e.g. the audit log group) emits logs.
2. **OCI Service Connector Hub** - a built-in service connector moves those
   logs, no custom shipping code.
3. **OCI Object Storage** - an Archive-tier bucket holds them, with a native
   lifecycle rule for retention.
4. **OCI Monitoring + Notifications** - an alarm on the connector's error
   metrics pages someone when archiving breaks.

## What is custom code vs native configuration

- Native configuration: everything above. `terraform/main.tf` shows the
  wiring as a TEMPLATE ONLY - it has NOT been validated with
  `terraform plan`/`apply` and was never run against a tenancy.
- Custom code (`lac_check/`, Python stdlib only): a gate that reads an
  export describing the environment and fails CI when the archive path is
  misconfigured. This is the part that ran - locally and in GitHub Actions.

## Gate rules

| Rule | Severity | Fires when |
| --- | --- | --- |
| LAC003 | CRITICAL | the service connector is DISABLED (logs silently not archived) |
| LAC001 | HIGH | the archive bucket has no lifecycle rule (unbounded storage cost) |
| LAC002 | HIGH | log group retention is shorter than the connector batch window (data loss) |
| LAC004 | MEDIUM | batch rollover exceeds the Service Connector Hub 100 MB object limit |
| LAC005 | MEDIUM | no enabled Monitoring alarm watches connector failure metrics |

Exit codes: `0` clean, `2` findings, `3` usage/input error.

## What actually ran vs what did not

- Ran: the gate (`python -m lac_check ...`) on synthetic environment exports,
  20 unit tests, and CI on Python 3.10/3.11/3.12 with demo steps that must
  exit 2 (messy) and 0 (clean).
- Did NOT run: anything against a live OCI tenancy. The `examples/` JSON is
  synthetic data in the shape of Logging/Service Connector Hub/Object
  Storage listings. The Terraform file is a wiring sketch for a future
  live setup, not an applied configuration.

## Run it

```
python -m lac_check run-all examples/env_messy.json   # 4 findings, exit 2
python -m lac_check run-all examples/env_clean.json   # clean, exit 0
```

## Test it

```
python -m unittest discover -s tests -v
```
