#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Charlie Linville
#
# This file header was last modified 21 Nov 2026.
"""Train the error predictor on learner answer sequences."""

from collections.abc import Iterable

import torch
from torch import nn


def train_lstm(
    model: nn.Module,
    batches: Iterable[tuple[torch.Tensor, ...]],
    epochs: int = 10,
    learning_rate: float = 0.001,
) -> list[float]:
    """Return the average weighted loss after each epoch using reusable batches."""
    if epochs > 1 and iter(batches) is batches:
        raise ValueError("batches")
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    device = next(model.parameters()).device
    losses = []

    for _ in range(epochs):
        model.train()
        total_loss = 0.0
        total_weight = 0.0
        for batch in batches:
            features, history_ids, lengths, concepts, subjects, labels, weights = batch
            features = features.to(device)
            history_ids = history_ids.to(device)
            concepts = concepts.to(device)
            subjects = subjects.to(device)
            labels = labels.to(device).float()
            weights = weights.to(device)
            optimizer.zero_grad()
            logits = model(features, history_ids, lengths, concepts, subjects)
            row_loss = nn.functional.binary_cross_entropy_with_logits(
                logits, labels, reduction="none"
            )
            loss = (row_loss * weights).sum() / weights.sum()
            loss.backward()
            optimizer.step()
            total_loss += (row_loss * weights).sum().item()
            total_weight += weights.sum().item()
        if total_weight == 0:
            raise ValueError("batches")
        losses.append(total_loss / total_weight)

    return losses
