"""Synthetic per-client CFTI datasets for the federated learning simulation.

Real deployment would train on each user's own device over their own scam
reports - data that structurally cannot leave the device (that's the whole
point of federation). Nobody outside a real deployment has that data, so
this generates it with a known ground-truth rule instead, which is what
lets `run_simulation.py` report whether the federated model actually
learned something, not just that it ran.
"""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import TensorDataset

FEATURES = [
    "report_count_7d",  # normalized count of reports for this entity in the last week
    "name_has_digit_suffix",  # 1 if the entity name ends in digits (QuickCash24-style)
    "name_length",  # normalized character length
    "report_hour",  # normalized hour of day the report came in (late night skews suspicious)
    "distinct_reporters",  # normalized count of unique users who reported it
]
NUM_FEATURES = len(FEATURES)


def _ground_truth_rule(x: np.ndarray, rng: np.random.Generator, label_noise: float = 0.08) -> np.ndarray:
    """A scam entity tends to rack up reports fast, from a digit-suffixed
    name, from multiple distinct reporters, often late at night - not any
    single feature, which is what makes this a genuine (if small) learning
    problem rather than a lookup table."""
    score = (
        1.6 * x[:, 0]
        + 1.2 * x[:, 1]
        + 0.9 * x[:, 3]
        + 1.4 * x[:, 4]
        - 0.5 * x[:, 2]
    )
    prob = 1 / (1 + np.exp(-(score - 1.5)))
    labels = (rng.random(len(x)) < prob).astype(np.float32)
    flip = rng.random(len(x)) < label_noise
    labels[flip] = 1 - labels[flip]
    return labels


def make_client_dataset(client_id: int, num_samples: int = 200, seed: int | None = None) -> TensorDataset:
    rng = np.random.default_rng(seed if seed is not None else client_id)
    x = rng.random((num_samples, NUM_FEATURES)).astype(np.float32)
    x[:, 1] = (rng.random(num_samples) < 0.35).astype(np.float32)  # name_has_digit_suffix is binary
    y = _ground_truth_rule(x, rng)
    return TensorDataset(torch.from_numpy(x), torch.from_numpy(y).unsqueeze(1))
