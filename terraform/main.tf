# TEMPLATE ONLY - not validated with terraform plan/apply.
# The OOTB wiring this repo gates: OCI Logging (log group)
#   -> Service Connector Hub (built-in connector, no custom code)
#   -> Object Storage (archive bucket with lifecycle rule).

variable "compartment_ocid" { type = string }

resource "oci_logging_log_group" "audit" {
  compartment_id = var.compartment_ocid
  display_name   = "audit"
  retention_duration_days = 30
}

resource "oci_objectstorage_bucket" "log_archive" {
  compartment_id = var.compartment_ocid
  namespace      = "REPLACE_WITH_TENANCY_NAMESPACE"
  name           = "log-archive"
  storage_tier   = "Archive"
}

resource "oci_objectstorage_object_lifecycle_policy" "archive_retention" {
  bucket    = oci_objectstorage_bucket.log_archive.name
  namespace = "REPLACE_WITH_TENANCY_NAMESPACE"
  rules {
    action      = "DELETE"
    is_enabled  = true
    target      = "objects"
    time_amount = 365
    time_unit   = "DAYS"
  }
}

resource "oci_sch_service_connector" "audit_to_archive" {
  compartment_id = var.compartment_ocid
  display_name   = "audit-logs-to-archive"
  source {
    kind = "logging"
    log_sources {
      compartment_id = var.compartment_ocid
      log_group_id   = oci_logging_log_group.audit.id
    }
  }
  target {
    kind              = "objectStorage"
    bucket            = oci_objectstorage_bucket.log_archive.name
    batch_rollover_size_in_mbs = 100
    batch_rollover_time_in_ms  = 3600000
  }
}
