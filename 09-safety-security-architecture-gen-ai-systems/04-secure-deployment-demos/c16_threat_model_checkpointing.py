"""Section 16: durable GenAI workflow. Standard library, single worker per run.

The runner persists real results and progress. Local adapters replace external
services; replace them with authenticated, timeout-bounded clients.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time

# === DURABLE GENAI WORKFLOW ===
VERSION = 3
STAGES = ("validate_request", "retrieve_context", "generate_response",
          "validate_output", "release_response")
MAX_ATTEMPTS = 3


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, value):
    """Persist a complete file before publishing its name. Same filesystem only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_state(folder, run_id, request):
    path = folder / "checkpoint.json"
    expected = {"version": VERSION, "run_id": run_id,
                "request_sha256": digest(json.dumps(request, sort_keys=True).encode())}
    state = {**expected, "last_completed": 0, "generation_attempts": 0, "artifacts": {}}
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(state, dict) or set(state) != {*expected, "last_completed", "generation_attempts", "artifacts"}
            or any(type(state[k]) is not type(v) or state[k] != v for k, v in expected.items())
            or type(state["last_completed"]) is not int or not 0 <= state["last_completed"] <= 5
            or type(state["generation_attempts"]) is not int or not 0 <= state["generation_attempts"] <= MAX_ATTEMPTS
            or not isinstance(state["artifacts"], dict)
            or set(state["artifacts"]) != set(STAGES[:state["last_completed"]])):
        raise ValueError("Checkpoint does not match this request or workflow")
    outputs = {}
    for stage, ref in state["artifacts"].items():
        if not isinstance(ref, dict) or set(ref) != {"file", "sha256"} or ref["file"] != stage + ".json":
            raise ValueError("Invalid artifact reference")
        data = (folder / ref["file"]).read_bytes()
        if digest(data) != ref["sha256"]:
            raise ValueError("Checkpoint artifact integrity check failed")
        outputs[stage] = json.loads(data)
    return state, outputs


def run_workflow(root, run_id, request, services):
    """Services supply current authorization, retrieval, generation, checks, delivery."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
        raise ValueError("Invalid run ID")
    services.authorize(request)  # Current identity, including on resume; never from generated text.
    folder = root / run_id
    state, outputs = load_state(folder, run_id, request)
    checkpoint = folder / "checkpoint.json"
    print(f"CHECKPOINT: last_completed={state['last_completed']}", flush=True)
    if state["last_completed"] == 5:
        print("ALREADY COMPLETE: no stages executed.")
        return
    for number, stage in enumerate(STAGES, 1):
        if number <= state["last_completed"]:
            print(f"SKIP {number}: {stage}")
            continue
        services.authorize(request)
        print(f"START {number}: {stage}", flush=True)
        if number == 1:
            if not isinstance(request.get("prompt"), str) or not 1 <= len(request["prompt"]) <= 2000:
                raise ValueError("Invalid request")
            result = {"accepted": True}
        elif number == 2:
            result = services.retrieve(request)
        elif number == 3:
            # Persist attempts BEFORE calling: restarting does not reset the retry budget.
            while state["generation_attempts"] < MAX_ATTEMPTS:
                state["generation_attempts"] += 1
                atomic_json(checkpoint, state)
                try:
                    result = services.generate(request, outputs["retrieve_context"])
                    break
                except TimeoutError:
                    print(f"TRANSIENT TIMEOUT: attempt={state['generation_attempts']}/{MAX_ATTEMPTS}", flush=True)
                    time.sleep(0.1 * 2 ** (state["generation_attempts"] - 1))
            else:
                raise RuntimeError("Generation retry budget exhausted; operator review required")
        elif number == 4:
            result = services.validate_output(outputs["generate_response"])
        else:
            # A previous approval is not sufficient: revalidate under current policy.
            services.validate_output(outputs["generate_response"])
            services.authorize(request)
            result = services.deliver(request, outputs["generate_response"], key=run_id + ":release")
        artifact = folder / (stage + ".json")
        atomic_json(artifact, result)
        state["artifacts"][stage] = {"file": artifact.name, "sha256": digest(artifact.read_bytes())}
        state["last_completed"] = number
        atomic_json(checkpoint, state)
        outputs[stage] = result
        print(f"SAVED: last_completed={number}", flush=True)
    print("COMPLETE: validated response delivered to local receiver.")

def main():
    from c16_local_adapters import LocalServices
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="demo")
    parser.add_argument("--state-dir", type=Path, default=Path(__file__).resolve().parent / "c16_runs")
    parser.add_argument("--fault", choices=("crash", "timeout", "always-timeout", "unsafe-output", "crash-after-delivery"))
    parser.add_argument("--revoke-access", action="store_true")
    args = parser.parse_args()
    request = {"subject": "demo-user", "tenant": "tenant-a", "prompt": "Summarize the refund policy."}
    try:
        services = LocalServices(args.state_dir, args.fault, args.revoke_access)
        run_workflow(args.state_dir, args.run_id, request, services)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"STOPPED: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
