"""
Master training script: trains the CNN sentiment model, then writes
models/registry.json which the FastAPI app reads at startup.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "models" / "registry.json"


def run(script_name: str):
    print(f"\n{'=' * 60}\nRunning {script_name}\n{'=' * 60}")
    subprocess.run([sys.executable, str(ROOT / "scripts" / script_name)], check=True)


def build_registry():
    cnn_meta = json.load(open(ROOT / "models" / "cnn" / "metadata.json"))

    registry = {
        "model": "cnn",
        "display_name": "CNN (Conv1D + Embeddings)",
        "path": "models/cnn",
        "accuracy": cnn_meta["accuracy"],
        "weighted_f1": cnn_meta["weighted_f1"],
        "classes": cnn_meta["classes"],
        "status": "ready",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"\nRegistry written to {REGISTRY_PATH}")


if __name__ == "__main__":
    run("train_cnn.py")
    build_registry()
    print("\nModel trained successfully.")
