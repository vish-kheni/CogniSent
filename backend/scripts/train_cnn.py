"""
Train a Keras Conv1D (CNN) sentiment classifier on the Nike shoe
review dataset and save the artifacts used by the API.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, f1_score, classification_report

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras import layers

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so we can import the app package below
from app.services.custom_layers import PaddingMask  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "nike_shoe_review_augmented.xlsx"
OUT_DIR = ROOT / "models" / "cnn"
OUT_DIR.mkdir(parents=True, exist_ok=True)

VOCAB_SIZE = 20000
MAX_LEN = 100
EMBED_DIM = 128


def build_model(num_classes: int) -> keras.Model:
    """
    Functional-API model that explicitly zeroes out padding positions
    before the conv layer. Sequential Conv1D + GlobalMaxPooling1D does
    NOT know which timesteps are real padding tokens (index 0) --
    Conv1D doesn't propagate Keras's built-in masking, so on short
    reviews (mostly padding out of MAX_LEN=100), the padding token's
    learned embedding can dominate GlobalMaxPooling and drown out the
    real signal. Explicitly multiplying by a 0/1 mask before AND after
    the conv layer guarantees padding contributes exactly 0 activation,
    so ReLU + GlobalMaxPooling naturally ignores it regardless of
    review length.
    """
    inputs = layers.Input(shape=(MAX_LEN,))

    mask = PaddingMask()(inputs)
    mask_expanded = layers.Reshape((MAX_LEN, 1))(mask)

    embedded = layers.Embedding(input_dim=VOCAB_SIZE, output_dim=EMBED_DIM)(inputs)
    embedded = layers.Multiply()([embedded, mask_expanded])
    embedded = layers.SpatialDropout1D(0.2)(embedded)

    conv = layers.Conv1D(128, 5, padding="same", activation="relu")(embedded)
    conv = layers.Multiply()([conv, mask_expanded])  # re-zero padding after conv

    pooled = layers.GlobalMaxPooling1D()(conv)

    dense = layers.Dense(64, activation="relu")(pooled)
    dense = layers.Dropout(0.4)(dense)
    outputs = layers.Dense(num_classes, activation="softmax")(dense)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    df = pd.read_excel(DATA_PATH)
    df = df.dropna(subset=["Review", "Sentiment"])

    X = df["Review"].astype(str).tolist()
    y = df["Sentiment"].astype(str)

    label_encoder = LabelEncoder()
    y_enc = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
    tokenizer.fit_on_texts(X_train)

    X_train_seq = pad_sequences(
        tokenizer.texts_to_sequences(X_train), maxlen=MAX_LEN, padding="post", truncating="post"
    )
    X_test_seq = pad_sequences(
        tokenizer.texts_to_sequences(X_test), maxlen=MAX_LEN, padding="post", truncating="post"
    )

    model = build_model(num_classes=len(label_encoder.classes_))
    model.summary()

    # The dataset is imbalanced (~68% Positive), which otherwise biases the
    # model toward predicting Positive on generic/short/out-of-distribution
    # text. Weight the loss inversely to class frequency to correct for it.
    class_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train,
    )
    class_weight = {i: w for i, w in enumerate(class_weights_arr)}
    print(f"Class weights: {class_weight}")

    early_stop = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=2, restore_best_weights=True
    )

    history = model.fit(
        X_train_seq, y_train,
        validation_split=0.1,
        epochs=8,
        batch_size=64,
        class_weight=class_weight,
        callbacks=[early_stop],
        verbose=2,
    )

    probs = model.predict(X_test_seq)
    preds = np.argmax(probs, axis=1)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average="weighted")
    report = classification_report(
        y_test, preds, target_names=label_encoder.classes_, output_dict=True
    )
    print(f"Accuracy: {acc:.4f}")
    print(f"Weighted F1: {f1:.4f}")
    print(classification_report(y_test, preds, target_names=label_encoder.classes_))

    model.save(OUT_DIR / "cnn_sentiment_model.h5")
    with open(OUT_DIR / "tokenizer.pkl", "wb") as f:
        pickle.dump(tokenizer, f)
    with open(OUT_DIR / "label_encoder.pkl", "wb") as f:
        pickle.dump(label_encoder, f)

    metadata = {
        "model_name": "cnn",
        "version": "v1",
        "type": "keras.Conv1D",
        "vocab_size": VOCAB_SIZE,
        "max_len": MAX_LEN,
        "embedding_dim": EMBED_DIM,
        "classes": label_encoder.classes_.tolist(),
        "accuracy": acc,
        "weighted_f1": f1,
        "classification_report": report,
        "epochs_run": len(history.history["loss"]),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }
    with open(OUT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
