# ═══════════════════════════════════════════════════════════════
# RailMind AI — Predictive Maintenance Engine (LSTM)
# AI Component #6: Time-series prediction model
# Predicts WHEN an asset will fail based on health trend data
#
# Implementation:
#   1. Generates synthetic health degradation curves per asset type
#   2. Trains a real PyTorch LSTM on sliding-window sequences
#   3. Uses the trained LSTM to predict next-step health
#   4. Extrapolates to estimate Remaining Useful Life (RUL)
#   5. Falls back to exponential decay model if PyTorch unavailable
# ═══════════════════════════════════════════════════════════════

import numpy as np
import os
import joblib
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from config import get_settings
from models.asset import RailwayAsset
from models.maintenance_task import MaintenanceTask

settings = get_settings()

# ─── LSTM Architecture (defined at module level for pickling) ───
_LSTM_INPUT_SIZE = 5    # features per timestep
_LSTM_HIDDEN_SIZE = 32
_LSTM_NUM_LAYERS = 2
_LSTM_SEQ_LEN = 12      # 12 months lookback window

try:
    import torch
    import torch.nn as nn

    class LSTMPredictor(nn.Module):
        """
        LSTM model for asset health prediction.

        Input:  (batch, seq_len=12, features=5)
                features = [health_score, age_years, decay_rate, noise, maintenance_flag]
        Output: (batch, 1) — predicted next-month health score
        """
        def __init__(self, input_size=_LSTM_INPUT_SIZE, hidden_size=_LSTM_HIDDEN_SIZE,
                     num_layers=_LSTM_NUM_LAYERS):
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, num_layers,
                                batch_first=True, dropout=0.1)
            self.fc = nn.Sequential(
                nn.Linear(hidden_size, 16),
                nn.ReLU(),
                nn.Linear(16, 1),
            )

        def forward(self, x):
            out, _ = self.lstm(x)
            out = self.fc(out[:, -1, :])  # Use last timestep
            return out

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


class PredictiveEngine:
    """
    LSTM-based predictive maintenance engine.

    WHAT IT DOES:
    - Takes asset health data (current health, age, type, section)
    - Uses a trained LSTM to predict future health trajectory
    - Estimates Remaining Useful Life (RUL)
    - Triggers proactive maintenance tasks for high-risk assets

    HOW IT WORKS:
    - Trains a real PyTorch LSTM on synthetic health degradation curves
    - Each asset type (TRACK/SIGNAL/OHE/BRIDGE) has different decay characteristics
    - Ghat sections degrade ~30% faster than plain sections
    - The LSTM learns the degradation patterns from time-series data
    - Falls back to exponential decay model if PyTorch is unavailable

    TRAINING APPROACH:
    Synthetic data is generated using domain-expert decay models for each
    asset type. The LSTM is trained to predict next-month health from a
    12-month sliding window. This is valid because Indian Railways assets
    follow predictable degradation curves.
    """

    def __init__(self):
        self.lstm_model = None
        self.scaler = None  # min/max scaling params
        self.decay_models = {}
        self._initialize_decay_models()
        self._load_or_train_lstm()

    def _initialize_decay_models(self):
        """
        Initialize exponential decay models for each asset type.
        These encode domain knowledge about asset degradation rates.
        Used both for generating LSTM training data and as fallback.

        Health(t) = H0 * exp(-lambda * t) + noise
        where lambda = degradation rate, t = years
        """
        self.decay_models = {
            "TRACK": {
                "lambda": 0.04,       # ~4% per year
                "ghat_factor": 1.3,   # 30% faster in ghat sections
                "noise_std": 3.0,     # Health score noise
                "critical_threshold": 50,
                "failure_threshold": 20,
                "mean_life_years": 25,
            },
            "SIGNAL": {
                "lambda": 0.05,       # ~5% per year (electronics degrade faster)
                "ghat_factor": 1.1,   # Slight increase in ghat
                "noise_std": 4.0,
                "critical_threshold": 55,
                "failure_threshold": 25,
                "mean_life_years": 20,
            },
            "OHE": {
                "lambda": 0.045,      # ~4.5% per year
                "ghat_factor": 1.4,   # Significant degradation in ghat
                "noise_std": 3.5,
                "critical_threshold": 50,
                "failure_threshold": 20,
                "mean_life_years": 22,
            },
            "BRIDGE": {
                "lambda": 0.02,       # ~2% per year (durable)
                "ghat_factor": 1.2,
                "noise_std": 2.0,
                "critical_threshold": 60,
                "failure_threshold": 30,
                "mean_life_years": 50,
            },
        }

    def _load_or_train_lstm(self):
        """Load existing LSTM model or train a new one."""
        if not _TORCH_AVAILABLE:
            print("[PredictiveEngine] PyTorch not available, using exponential decay fallback")
            return

        model_path = settings.PREDICTIVE_MODEL_PATH
        if os.path.exists(model_path):
            try:
                self.lstm_model = LSTMPredictor()
                state = torch.load(model_path, weights_only=True, map_location="cpu")
                self.lstm_model.load_state_dict(state)
                self.lstm_model.eval()
                print("[PredictiveEngine] LSTM model loaded successfully")
                return
            except Exception as e:
                print(f"[PredictiveEngine] Error loading LSTM model: {e}")
                self.lstm_model = None

        # Train a new LSTM
        print("[PredictiveEngine] Training new LSTM model...")
        self._train_lstm()

    def _generate_training_sequences(self, n_assets=500, seq_len=_LSTM_SEQ_LEN):
        """
        Generate synthetic health degradation time-series for LSTM training.

        For each simulated asset:
          - Pick a random asset type and initial health
          - Simulate monthly health readings with exponential decay + noise
          - Create sliding windows of length seq_len
          - Target = health at timestep seq_len+1

        Features per timestep: [health, age_years, decay_rate, noise_level, maint_flag]
        """
        np.random.seed(42)
        X_sequences = []
        y_targets = []

        asset_types = list(self.decay_models.keys())

        for _ in range(n_assets):
            asset_type = np.random.choice(asset_types)
            config = self.decay_models[asset_type]
            is_ghat = np.random.random() < 0.3  # 30% ghat sections

            decay_rate = config["lambda"]
            if is_ghat:
                decay_rate *= config["ghat_factor"]

            # Random starting conditions
            initial_health = np.random.uniform(60, 100)
            initial_age = np.random.uniform(0, 15)  # years

            # Maintenance events (randomly boost health)
            maint_months = set(np.random.choice(range(36), size=np.random.randint(0, 4), replace=False))

            # Generate 36 months of health readings (need seq_len+1 for targets)
            n_months = max(36, seq_len + 12)
            health_series = []
            age_series = []
            decay_series = []
            noise_series = []
            maint_series = []

            current_health = initial_health
            for month in range(n_months):
                age = initial_age + month / 12.0
                noise = np.random.normal(0, config["noise_std"] * 0.3)
                maint_flag = 1.0 if month in maint_months else 0.0

                # Apply maintenance boost
                if maint_flag:
                    current_health = min(100, current_health + np.random.uniform(5, 15))

                # Record
                health_series.append(max(0, min(100, current_health + noise)))
                age_series.append(age)
                decay_series.append(decay_rate)
                noise_series.append(abs(noise))
                maint_series.append(maint_flag)

                # Decay for next step
                current_health *= np.exp(-decay_rate / 12.0)

            # Create sliding windows
            for start in range(len(health_series) - seq_len):
                seq = np.column_stack([
                    health_series[start:start + seq_len],
                    age_series[start:start + seq_len],
                    [decay_rate] * seq_len,
                    noise_series[start:start + seq_len],
                    maint_series[start:start + seq_len],
                ])
                target = health_series[start + seq_len]
                X_sequences.append(seq)
                y_targets.append(target)

        X = np.array(X_sequences, dtype=np.float32)
        y = np.array(y_targets, dtype=np.float32)

        return X, y

    def _train_lstm(self):
        """Train the LSTM model on synthetic degradation data."""
        if not _TORCH_AVAILABLE:
            return

        X, y = self._generate_training_sequences(n_assets=500)

        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).unsqueeze(1)

        # Train/val split
        n_train = int(0.8 * len(X_tensor))
        X_train, X_val = X_tensor[:n_train], X_tensor[n_train:]
        y_train, y_val = y_tensor[:n_train], y_tensor[n_train:]

        # Create model
        model = LSTMPredictor()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        # Training loop
        batch_size = 64
        n_epochs = 30
        best_val_loss = float("inf")
        best_state = None

        model.train()
        for epoch in range(n_epochs):
            # Shuffle training data
            perm = torch.randperm(n_train)
            X_train_shuffled = X_train[perm]
            y_train_shuffled = y_train[perm]

            epoch_loss = 0.0
            n_batches = 0
            for i in range(0, n_train, batch_size):
                batch_X = X_train_shuffled[i:i + batch_size]
                batch_y = y_train_shuffled[i:i + batch_size]

                optimizer.zero_grad()
                pred = model(batch_X)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                n_batches += 1

            # Validation
            model.eval()
            with torch.no_grad():
                val_pred = model(X_val)
                val_loss = criterion(val_pred, y_val).item()
            model.train()

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in model.state_dict().items()}

            if (epoch + 1) % 10 == 0:
                print(f"  [LSTM] Epoch {epoch+1}/{n_epochs} — "
                      f"train_loss: {epoch_loss/n_batches:.4f}, val_loss: {val_loss:.4f}")

        # Load best model
        if best_state:
            model.load_state_dict(best_state)

        model.eval()
        self.lstm_model = model

        # Save model
        os.makedirs(os.path.dirname(settings.PREDICTIVE_MODEL_PATH), exist_ok=True)
        torch.save(model.state_dict(), settings.PREDICTIVE_MODEL_PATH)
        print(f"[PredictiveEngine] LSTM model trained and saved "
              f"(val_loss: {best_val_loss:.4f})")

    def _parse_date(self, value) -> Optional[date]:
        """Safely parse a date value (handles SQLite string storage)."""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])  # Handle "2024-01-15" or datetime strings
            except (ValueError, IndexError):
                return None
        return None

    def _predict_with_lstm(self, current_health: float, decay_rate: float,
                            age_years: float, is_ghat: bool) -> list[float]:
        """
        Use the trained LSTM to predict future health trajectory.

        Builds a synthetic history from the current state, then
        autoregressively predicts the next 12 months.

        Returns: list of 12 predicted monthly health values
        """
        if not _TORCH_AVAILABLE or self.lstm_model is None:
            return []

        # Build a synthetic history of _LSTM_SEQ_LEN months leading up to now
        # using the decay model to simulate plausible past health
        config_key = "TRACK"  # default
        for asset_type, config in self.decay_models.items():
            if abs(config["lambda"] * (config["ghat_factor"] if is_ghat else 1.0) - decay_rate) < 0.005:
                config_key = asset_type
                break

        config = self.decay_models[config_key]

        # Reconstruct plausible history (working backwards from current_health)
        history_health = []
        for month_back in range(_LSTM_SEQ_LEN - 1, -1, -1):
            # Health was higher in the past
            past_health = current_health * np.exp(decay_rate * month_back / 12.0)
            past_health = min(100, past_health) + np.random.normal(0, 0.5)
            history_health.append(max(0, min(100, past_health)))

        # Build feature sequence [health, age, decay, noise, maint_flag]
        sequence = []
        for i, h in enumerate(history_health):
            past_age = age_years - (_LSTM_SEQ_LEN - 1 - i) / 12.0
            sequence.append([h, max(0, past_age), decay_rate, 0.5, 0.0])

        # Autoregressive prediction for 12 months
        predictions = []
        seq = np.array(sequence, dtype=np.float32)

        self.lstm_model.eval()
        with torch.no_grad():
            for month in range(12):
                input_tensor = torch.FloatTensor(seq[-_LSTM_SEQ_LEN:]).unsqueeze(0)
                pred = self.lstm_model(input_tensor).item()
                pred = max(0, min(100, pred))
                predictions.append(round(pred, 2))

                # Append prediction to sequence for next step
                new_age = age_years + (month + 1) / 12.0
                new_step = [pred, new_age, decay_rate, 0.5, 0.0]
                seq = np.vstack([seq, new_step])

        return predictions

    def predict_remaining_life(self, asset: RailwayAsset, is_ghat: bool = False) -> dict:
        """
        Predict remaining useful life (RUL) for an asset.

        Uses the trained LSTM when available; falls back to exponential decay.

        Returns:
        {
            "current_health": float,
            "predicted_failure_date": date,
            "remaining_life_days": int,
            "health_trajectory": list[dict],  # next 12 months predicted health
            "risk_level": str,  # LOW/MEDIUM/HIGH/CRITICAL
            "maintenance_recommended_date": date,
            "confidence": float,
        }
        """
        today = date.today()
        current_health = float(asset.health_score) if asset.health_score else 100.0

        # Get decay model for this asset type
        decay_config = self.decay_models.get(asset.asset_type, self.decay_models["TRACK"])
        decay_rate = decay_config["lambda"]

        if is_ghat:
            decay_rate *= decay_config["ghat_factor"]

        # Calculate asset age (safely parse date from SQLite)
        install_dt = self._parse_date(asset.install_date)
        age_days = (today - install_dt).days if install_dt else 365 * 5
        age_years = age_days / 365.25

        # Maintenance effect: recent maintenance slows degradation
        maintenance_boost = 1.0
        last_maint_dt = self._parse_date(asset.last_maintained)
        if last_maint_dt:
            days_since_maint = (today - last_maint_dt).days
            if days_since_maint < 90:
                maintenance_boost = 0.7  # 30% slower degradation
            elif days_since_maint < 180:
                maintenance_boost = 0.85

        effective_decay = decay_rate * maintenance_boost

        # ─── Predict future health trajectory ───
        use_lstm = (self.lstm_model is not None)
        lstm_predictions = []

        if use_lstm:
            lstm_predictions = self._predict_with_lstm(
                current_health, effective_decay, age_years, is_ghat
            )

        # Build trajectory (LSTM or fallback)
        trajectory = []
        failure_date = None
        maintenance_date = None

        for month in range(1, 13):
            days = month * 30
            future_date = today + timedelta(days=days)

            if use_lstm and month <= len(lstm_predictions):
                predicted_health = lstm_predictions[month - 1]
            else:
                # Exponential decay fallback
                predicted_health = current_health * np.exp(-effective_decay * (month / 12))
                noise = np.random.normal(0, decay_config["noise_std"] * 0.3)
                predicted_health = max(0, min(100, predicted_health + noise))

            trajectory.append({
                "date": future_date.isoformat(),
                "predicted_health": round(predicted_health, 2),
                "month": month,
            })

            # Check thresholds
            if predicted_health <= decay_config["failure_threshold"] and failure_date is None:
                failure_date = future_date

            if predicted_health <= decay_config["critical_threshold"] and maintenance_date is None:
                maintenance_date = future_date

        # If no failure within 12 months, extrapolate
        if failure_date is None:
            threshold = decay_config["failure_threshold"]
            if current_health > threshold and effective_decay > 0:
                months_to_failure = -np.log(threshold / current_health) / effective_decay * 12
                failure_date = today + timedelta(days=int(months_to_failure * 30))
            else:
                failure_date = today + timedelta(days=365 * 5)  # Default 5 years

        if maintenance_date is None:
            maintenance_date = failure_date - timedelta(days=90)  # 3 months before failure

        # Calculate remaining life
        remaining_days = (failure_date - today).days

        # Risk level
        if current_health < decay_config["failure_threshold"]:
            risk_level = "CRITICAL"
        elif current_health < decay_config["critical_threshold"]:
            risk_level = "HIGH"
        elif current_health < 75:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Confidence based on data quality and model availability
        confidence = 0.65  # Base confidence for synthetic model
        if use_lstm:
            confidence += 0.15  # LSTM adds confidence
        if install_dt:
            confidence += 0.1
        if last_maint_dt:
            confidence += 0.1

        return {
            "asset_code": asset.asset_code,
            "asset_type": asset.asset_type,
            "current_health": current_health,
            "predicted_failure_date": failure_date.isoformat(),
            "remaining_life_days": remaining_days,
            "health_trajectory": trajectory,
            "risk_level": risk_level,
            "maintenance_recommended_date": maintenance_date.isoformat(),
            "confidence": round(min(confidence, 0.95), 2),
            "decay_rate": round(effective_decay, 4),
            "model_used": "LSTM" if use_lstm else "EXPONENTIAL_DECAY",
        }

    def predict_all_assets(
        self,
        db: Session,
        section_id: int,
        update_tasks: bool = True,
    ) -> list[dict]:
        """
        Run predictions for ALL assets in a section.
        Optionally creates proactive maintenance tasks for high-risk assets.
        """
        from models.corridor import RailwaySection

        section = db.query(RailwaySection).filter_by(id=section_id).first()
        if not section:
            return []

        assets = db.query(RailwayAsset).filter_by(section_id=section_id).all()
        is_ghat = section.is_ghat_section

        predictions = []
        high_risk_count = 0

        for asset in assets:
            prediction = self.predict_remaining_life(asset, is_ghat=is_ghat)
            predictions.append(prediction)

            # Update task predicted_failure dates
            if update_tasks and prediction["risk_level"] in ("CRITICAL", "HIGH"):
                high_risk_count += 1
                linked_tasks = db.query(MaintenanceTask).filter_by(
                    asset_id=asset.id, status="PENDING"
                ).all()
                for task in linked_tasks:
                    task.predicted_failure = date.fromisoformat(prediction["predicted_failure_date"])

        if update_tasks:
            db.commit()

        # Sort by risk (critical first)
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        predictions.sort(key=lambda p: risk_order.get(p["risk_level"], 4))

        print(f"[PredictiveEngine] Analyzed {len(predictions)} assets, {high_risk_count} high-risk")
        return predictions

    def get_section_risk_summary(self, db: Session, section_id: int) -> dict:
        """Get risk summary for dashboard display."""
        predictions = self.predict_all_assets(db, section_id, update_tasks=False)

        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for p in predictions:
            risk_counts[p["risk_level"]] = risk_counts.get(p["risk_level"], 0) + 1

        avg_health = np.mean([p["current_health"] for p in predictions]) if predictions else 0

        return {
            "total_assets": len(predictions),
            "risk_distribution": risk_counts,
            "avg_health": round(avg_health, 2),
            "assets_needing_attention": risk_counts["CRITICAL"] + risk_counts["HIGH"],
            "top_5_at_risk": predictions[:5],
        }
