"""Runs the federated CFTI simulation locally - N simulated clients, each
training on their own synthetic threat-report data with Opacus DP-SGD,
coordinated by a Flower FedAvg server that only ever sees noised model
weights, never raw data. This is Phase 3's "genuine federated learning"
item (docs/ROADMAP.md) - real Flower + real Opacus, run against synthetic
data because nobody outside a real multi-device deployment has actual
per-user CFTI report histories to federate over.

Run with: python -m app.federated.run_simulation
"""

from __future__ import annotations

from flwr.simulation import run_simulation

from app.federated.client_app import app as client_app
from app.federated.server_app import app as server_app

NUM_CLIENTS = 5


if __name__ == "__main__":
    run_simulation(
        server_app=server_app,
        client_app=client_app,
        num_supernodes=NUM_CLIENTS,
        backend_config={"client_resources": {"num_cpus": 1, "num_gpus": 0}},
    )
