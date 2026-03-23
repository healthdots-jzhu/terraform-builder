"""Validation helpers for wizard input."""

from __future__ import annotations

import re

_CIDR_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$")
_PROJECT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$")

AWS_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "eu-west-1", "eu-west-2", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
]


def validate_cidr(value: str) -> bool:
    if not _CIDR_RE.match(value):
        return False
    ip, prefix = value.split("/")
    octets = ip.split(".")
    if any(int(o) > 255 for o in octets):
        return False
    if not 0 <= int(prefix) <= 32:
        return False
    return True


def validate_project_name(value: str) -> bool:
    return bool(_PROJECT_NAME_RE.match(value))


def validate_port(value: str) -> bool:
    try:
        p = int(value)
        return 1 <= p <= 65535
    except ValueError:
        return False
