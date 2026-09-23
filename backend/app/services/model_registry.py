"""
Loads and caches the trained CNN sentiment model described by
models/registry.json, and exposes a predict() interface.

Every prediction first runs through the rule-based pipeline in
prediction_pipeline.py (translate -> clean -> emoji/idiom/negated-
adjective/hedge/contrast/VADER overrides). If a rule fires
confidently, its label is returned directly. Otherwise the CNN makes
the call, using the same cleaned text the pipeline already produced.
"""
import json
import pickle
import threading

from app.core.config import settings
from app.services.prediction_pipeline import fallback_sentiment, resolve_sentiment

_lock = threading.Lock()


class CNNModel:
    def __init__(self, model, tokenizer, label_encoder, metadata: dict):
        self.model = model
        self.tokenizer = tokenizer
        self.label_encoder = label_encoder
        self.metadata = metadata

    def predict(self, text: str) -> dict:
        import numpy as np

        rule_label, cleaned = resolve_sentiment(text)

        if rule_label is not None:
            return {
                "label": rule_label,
                "confidence": 1.0,
                "probabilities": {
                    cls: (1.0 if cls == rule_label else 0.0)
                    for cls in self.label_encoder.classes_
                },
            }

        from tensorflow.keras.preprocessing.sequence import pad_sequences

        max_len = self.metadata.get("max_len", 100)
        seq = self.tokenizer.texts_to_sequences([cleaned])
        padded = pad_sequences(seq, maxlen=max_len, padding="post", truncating="post")
        probs = self.model.predict(padded, verbose=0)[0]
        pred_idx = int(np.argmax(probs))
        label = self.label_encoder.inverse_transform([pred_idx])[0]

        return {
            "label": label,
            "confidence": float(probs[pred_idx]),
            "probabilities": {
                cls: float(p) for cls, p in zip(self.label_encoder.classes_, probs)
            },
        }


class RuleBasedModel:
    """Low-memory inference used by the Render free instance."""

    def predict(self, text: str) -> dict:
        rule_label, cleaned = resolve_sentiment(text)
        if rule_label is not None:
            label = rule_label
            confidence = 1.0
            probabilities = {
                name: (1.0 if name == label else 0.0)
                for name in ("Negative", "Neutral", "Positive")
            }
        else:
            label, confidence, probabilities = fallback_sentiment(cleaned)

        return {
            "label": label,
            "confidence": confidence,
            "probabilities": probabilities,
        }


class ModelRegistry:
    """Lazily loads the CNN model on first use and caches it in memory."""

    def __init__(self):
        self._model: CNNModel | None = None
        self._registry: dict | None = None

    def _load_registry(self) -> dict:
        if self._registry is None:
            with open(settings.REGISTRY_PATH) as f:
                self._registry = json.load(f)
        return self._registry

    def info(self) -> dict:
        info = dict(self._load_registry())
        if not settings.USE_CNN:
            info.update(
                model="vader",
                display_name="VADER (low-memory mode)",
                status="ready",
            )
        return info

    def get(self) -> CNNModel:
        with _lock:
            if self._model is not None:
                return self._model

            registry = self._load_registry()
            if not settings.USE_CNN:
                self._model = RuleBasedModel()
                return self._model

            model_dir = (settings.MODELS_DIR / ".." / registry["path"]).resolve()
            metadata = json.load(open(model_dir / "metadata.json"))

            from tensorflow import keras

            # Importing this registers the PaddingMask custom layer with
            # Keras's serialization registry so load_model can reconstruct
            # it safely (see custom_layers.py for why this is needed).
            from app.services.custom_layers import PaddingMask  # noqa: F401

            keras_model = keras.models.load_model(model_dir / "cnn_sentiment_model.h5")
            with open(model_dir / "tokenizer.pkl", "rb") as f:
                tokenizer = pickle.load(f)
            with open(model_dir / "label_encoder.pkl", "rb") as f:
                label_encoder = pickle.load(f)

            self._model = CNNModel(keras_model, tokenizer, label_encoder, metadata)
            return self._model


registry = ModelRegistry()
