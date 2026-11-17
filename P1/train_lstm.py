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
    """Return the average weighted loss after each epoch."""
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
            raise ValueError("training batches are empty")
        losses.append(total_loss / total_weight)

    return losses
