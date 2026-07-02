"""FedAvg over the clients' DP-trained updates - the server never sees raw
threat reports, only averaged, already-noised model weights.
"""

from __future__ import annotations

from flwr.common import Context, ndarrays_to_parameters
from flwr.server import ServerApp, ServerAppComponents, ServerConfig
from flwr.server.strategy import FedAvg

from app.federated.model import ThreatClassifier, get_weights

NUM_ROUNDS = 5


def _weighted_accuracy(metrics: list[tuple[int, dict]]) -> dict:
    total = sum(n for n, _ in metrics)
    accuracy = sum(n * m.get("accuracy", 0.0) for n, m in metrics) / total
    return {"accuracy": accuracy}


def _mean_epsilon(metrics: list[tuple[int, dict]]) -> dict:
    values = [m["epsilon_spent"] for _, m in metrics if "epsilon_spent" in m]
    return {"mean_epsilon_spent": sum(values) / len(values)} if values else {}


def server_fn(context: Context) -> ServerAppComponents:
    initial_parameters = ndarrays_to_parameters(get_weights(ThreatClassifier()))
    strategy = FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_available_clients=2,
        initial_parameters=initial_parameters,
        evaluate_metrics_aggregation_fn=_weighted_accuracy,
        fit_metrics_aggregation_fn=_mean_epsilon,
    )
    return ServerAppComponents(strategy=strategy, config=ServerConfig(num_rounds=NUM_ROUNDS))


app = ServerApp(server_fn=server_fn)
