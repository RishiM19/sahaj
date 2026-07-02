"""Each simulated client trains locally with Opacus DP-SGD before its model
update goes anywhere - individual reports never leave the device, and even
the model update carries calibrated noise. See docs/ROADMAP.md for the
epsilon = 0.1 privacy budget this targets (the exec-summary spec) and why
that's an aggressive setting whose utility cost only gets absorbed once
enough real clients are federating - not the handful simulated here.
"""

from __future__ import annotations

import warnings

import torch
from flwr.client import ClientApp, NumPyClient
from flwr.common import Context
from opacus import PrivacyEngine
from torch.utils.data import DataLoader, random_split

from app.federated.data import make_client_dataset
from app.federated.model import ThreatClassifier, get_weights, set_weights

TARGET_EPSILON = 0.1
TARGET_DELTA = 1e-5
LOCAL_EPOCHS = 1


class FlowerClient(NumPyClient):
    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        self.model = ThreatClassifier()

        dataset = make_client_dataset(client_id)
        n_val = max(1, len(dataset) // 5)
        n_train = len(dataset) - n_val
        train_set, val_set = random_split(dataset, [n_train, n_val])
        self.train_loader = DataLoader(train_set, batch_size=16, shuffle=True)
        self.val_loader = DataLoader(val_set, batch_size=32)

    def get_parameters(self, config):
        return get_weights(self.model)

    def fit(self, parameters, config):
        set_weights(self.model, parameters)
        optimizer = torch.optim.SGD(self.model.parameters(), lr=0.5)
        privacy_engine = PrivacyEngine()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # opacus warns about the deliberately tiny model/dataset here
            dp_model, dp_optimizer, dp_loader = privacy_engine.make_private_with_epsilon(
                module=self.model,
                optimizer=optimizer,
                data_loader=self.train_loader,
                target_epsilon=TARGET_EPSILON,
                target_delta=TARGET_DELTA,
                epochs=LOCAL_EPOCHS,
                max_grad_norm=1.0,
            )

        loss_fn = torch.nn.BCEWithLogitsLoss()
        dp_model.train()
        for _ in range(LOCAL_EPOCHS):
            for xb, yb in dp_loader:
                dp_optimizer.zero_grad()
                loss = loss_fn(dp_model(xb), yb)
                loss.backward()
                dp_optimizer.step()

        epsilon_spent = privacy_engine.get_epsilon(TARGET_DELTA)
        trained_module = getattr(dp_model, "_module", dp_model)
        return get_weights(trained_module), len(self.train_loader.dataset), {"epsilon_spent": epsilon_spent}

    def evaluate(self, parameters, config):
        set_weights(self.model, parameters)
        loss_fn = torch.nn.BCEWithLogitsLoss()
        self.model.eval()
        correct, total, loss_sum = 0, 0, 0.0
        with torch.no_grad():
            for xb, yb in self.val_loader:
                logits = self.model(xb)
                loss_sum += loss_fn(logits, yb).item() * len(xb)
                preds = (torch.sigmoid(logits) > 0.5).float()
                correct += (preds == yb).sum().item()
                total += len(xb)
        return loss_sum / total, total, {"accuracy": correct / total}


def client_fn(context: Context):
    client_id = context.node_config["partition-id"]
    return FlowerClient(client_id).to_client()


app = ClientApp(client_fn=client_fn)
