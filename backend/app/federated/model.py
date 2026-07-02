"""The model every client trains locally and the server averages -
deliberately tiny (logistic regression over 5 features) since the point of
this simulation is demonstrating the federated + differential-privacy
mechanics, not squeezing accuracy out of a large network.
"""

from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn

from app.federated.data import NUM_FEATURES


class ThreatClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(NUM_FEATURES, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def get_weights(model: nn.Module) -> list:
    return [val.cpu().numpy() for val in model.state_dict().values()]


def set_weights(model: nn.Module, weights: list) -> None:
    params = zip(model.state_dict().keys(), weights, strict=True)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params})
    model.load_state_dict(state_dict, strict=True)
