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
"""Estimate the next answer's error probability from earlier attempts."""

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence


class LSTMErrorModel(nn.Module):
    """Combine the answer sequence with the target concept and subject."""

    def __init__(
        self,
        concept_count: int,
        subject_count: int,
        hidden_size: int = 32,
        embedding_size: int = 8,
    ) -> None:
        """Create the sequence encoder and target embeddings."""
        super().__init__()
        self.history_concept_embedding = nn.Embedding(
            concept_count,
            embedding_size,
            padding_idx=0,
        )
        self.lstm = nn.LSTM(27 + embedding_size, hidden_size, batch_first=True)
        self.concept_embedding = nn.Embedding(
            concept_count,
            embedding_size,
            padding_idx=0,
        )
        self.subject_embedding = nn.Embedding(
            subject_count,
            embedding_size,
            padding_idx=0,
        )
        self.output = nn.Linear(hidden_size + 2 * embedding_size, 1)

    def forward(
        self,
        inputs: torch.Tensor,
        history_concept_ids: torch.Tensor,
        lengths: torch.Tensor,
        concept_ids: torch.Tensor,
        subject_ids: torch.Tensor,
    ) -> torch.Tensor:
        """Return one unnormalized error score per learner sequence."""
        historical = self.history_concept_embedding(history_concept_ids)
        count = (history_concept_ids != 0).sum(dim=2).clamp(min=1).unsqueeze(-1)
        historical = historical.sum(dim=2) / count
        packed = pack_padded_sequence(
            torch.cat((inputs, historical), dim=2),
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False,
        )
        _, (hidden, _) = self.lstm(packed)
        combined = torch.cat(
            (
                hidden[-1],
                self.concept_embedding(concept_ids),
                self.subject_embedding(subject_ids),
            ),
            dim=1,
        )
        return self.output(combined).squeeze(-1)

    @torch.no_grad()
    def predict_error_batch(
        self,
        inputs: torch.Tensor,
        history_concept_ids: torch.Tensor,
        lengths: torch.Tensor,
        concept_ids: torch.Tensor,
        subject_ids: torch.Tensor,
    ) -> torch.Tensor:
        """Convert the model's scores to error probabilities."""
        self.eval()
        return torch.sigmoid(
            self(inputs, history_concept_ids, lengths, concept_ids, subject_ids)
        )
