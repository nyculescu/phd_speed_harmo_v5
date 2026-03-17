"""QRDQN policy wrapper that supports risk-sensitive CVaR action selection."""
from typing import Optional

import torch as th
from sb3_contrib.qrdqn.policies import QRDQNPolicy


class CvarQRDQNPolicy(QRDQNPolicy):
    """
    Compute Q-values using CVaR over the lowest quantiles instead of mean.

    Configurable via:
      risk_mode: "cvar" or None
      risk_alpha: fraction of quantile mass to average (e.g., 0.05)
    """

    def __init__(
        self,
        *args,
        risk_mode: Optional[str] = None,
        risk_alpha: float = 0.05,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.risk_mode = (risk_mode or "").lower() if risk_mode else None
        self.risk_alpha = float(max(min(risk_alpha, 1.0), 1e-6))

    def _get_q_values(self, quantiles: th.Tensor) -> th.Tensor:
        """
        quantiles: [batch, actions, n_quantiles]
        returns: [batch, actions] Q-values
        """
        if self.risk_mode != "cvar":
            return quantiles.mean(dim=2)

        n_q = quantiles.shape[2]
        k = max(1, int(self.risk_alpha * n_q))
        return quantiles[:, :, :k].mean(dim=2)
