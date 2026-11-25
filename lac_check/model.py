"""Load and validate a synthetic log-archive environment export."""
import json
import os

REQUIRED_TOP = ("connector", "bucket", "log_group", "alarms")


class LoadError(Exception):
    pass


def load(path):
    if not os.path.exists(path):
        raise LoadError("missing file: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except json.JSONDecodeError as exc:
        raise LoadError("bad JSON in %s: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise LoadError("environment export must be a JSON object")
    for field in REQUIRED_TOP:
        if field not in doc:
            raise LoadError("environment export missing section %r" % field)
    connector = doc["connector"]
    for field in ("state", "source", "target"):
        if field not in connector:
            raise LoadError("connector missing field %r" % field)
    if connector["source"].get("kind") != "logging":
        raise LoadError("connector source kind must be 'logging'")
    if connector["target"].get("kind") != "objectstorage":
        raise LoadError("connector target kind must be 'objectstorage'")
    if not isinstance(doc["alarms"], list):
        raise LoadError("alarms must be a list")
    return doc
