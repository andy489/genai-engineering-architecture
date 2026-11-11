"""Section 15: validate runtime configuration and print a safe, explicit projection.

This one-shot demo never calls a model or starts a server. It does not implement
TLS, a secrets manager, network segmentation or a hostile-code sandbox.
"""
import argparse
import errno
import json
import os
from pathlib import Path
import sys


def effective_config():
    # Validate fields without echoing invalid values or dumping the environment.
    choices = {"APP_ENV": {"demo", "staging", "production"},
               "MODEL_NAME": {"demo-model", "demo-model-small"},
               "LOG_LEVEL": {"INFO", "WARNING", "ERROR"}}
    config = {}
    for name, allowed in choices.items():
        value = os.environ.get(name, "")
        if value not in allowed:
            raise ValueError(f"{name} is missing or invalid")
        config[name] = value
    try:
        tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", ""))
    except ValueError:
        raise ValueError("MAX_OUTPUT_TOKENS must be an integer") from None
    if not 1 <= tokens <= 4096:
        raise ValueError("MAX_OUTPUT_TOKENS must be between 1 and 4096")
    if not os.environ.get("PROVIDER_API_KEY", "").strip():
        raise ValueError("PROVIDER_API_KEY is required")
    # This is an output allowlist, not a general-purpose redactor.
    config.update(MAX_OUTPUT_TOKENS=tokens, PROVIDER_API_KEY="[REDACTED]")
    return config


def check_read_only():
    # /tmp is normally writable in this base image. EROFS verifies --read-only,
    # rather than merely showing that the non-root user cannot write to /app.
    probe = Path("/tmp/c15-write-probe")
    try:
        with probe.open("x") as stream:
            stream.write("demo")
    except OSError as error:
        if error.errno == errno.EROFS:
            print("PASS: root filesystem write rejected as read-only.")
            return
        raise RuntimeError("Unexpected filesystem error; hardening not verified") from None
    else:
        probe.unlink()
        raise RuntimeError("Filesystem is writable; use --read-only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-read-only", action="store_true")
    args = parser.parse_args()
    try:
        config = effective_config()
        print("=== EFFECTIVE CONFIG (SAFE PROJECTION) ===")
        print(json.dumps(config, indent=2))
        print(json.dumps({"uid": os.getuid() if hasattr(os, "getuid") else None,
                          "env_file_in_image": Path("/app/.env.local").exists()}))
        if args.check_read_only:
            check_read_only()
    except (ValueError, RuntimeError) as error:
        print(f"STARTUP ERROR: {error}", file=sys.stderr)
        return 2
    print("READY: configuration accepted; no provider call was made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
