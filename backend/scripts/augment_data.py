"""
Augments the original review dataset with a small set of hand-written
English reviews covering common sentiment vocabulary (worst, awful,
poor, disappointing, mediocre, etc.) that never appears anywhere in
the original dataset. Without this, the model has literally no signal
for these words and defaults toward the majority class (Positive) when
it sees them.

Run once, before training: it writes data/nike_shoe_review_augmented.xlsx
which train_cnn.py reads instead of the raw file.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "data" / "nike_shoe_review.xlsx"
OUT_PATH = ROOT / "data" / "nike_shoe_review_augmented.xlsx"

NEGATIVE_TEMPLATES = [
    "This product is disappointing.",
    "Honestly disappointing quality for the price.",
    "Worst shoes I have ever bought.",
    "These are the worst running shoes I've owned.",
    "Awful comfort, my feet hurt after ten minutes.",
    "Poor quality materials, fell apart almost immediately.",
    "Poor stitching and an awful fit overall.",
    "Terrible experience, would not recommend to anyone.",
    "I hate how uncomfortable these shoes are.",
    "Mediocre at best, definitely not worth the money.",
    "Really disappointing purchase, not what I expected.",
    "The sole is awful and started falling apart fast.",
    "Not happy with this purchase at all.",
    "Such a poor fit, way too tight and uncomfortable.",
    "This is by far the worst pair of shoes I own.",
    "Cheap, poor quality, and disappointing durability.",
    "I regret buying these, awful experience overall.",
    "Disappointing cushioning, my knees hurt after every run.",
    "Worst purchase decision I've made this year.",
    "Terrible support, poor comfort, not recommended.",
]

POSITIVE_TEMPLATES = [
    "These shoes are amazing, best purchase I've made.",
    "Fantastic comfort and great quality overall.",
    "I love these shoes, they're excellent.",
    "Superb quality and very comfortable to wear.",
    "Best running shoes I have ever owned.",
    "Wonderful fit, incredible comfort, highly recommend.",
    "Really happy with this purchase, excellent value.",
    "Outstanding quality, worth every penny.",
    "Amazing cushioning and fantastic durability.",
    "Great shoes, love the design and comfort.",
]

NEUTRAL_TEMPLATES = [
    "It's okay, nothing special about it.",
    "Average shoes, does the job but nothing more.",
    "Mediocre quality, about what I expected for the price.",
    "So-so comfort, neither great nor bad.",
    "Decent enough, but I probably wouldn't buy again.",
    "It's fine, just an average pair of shoes.",
    "Not bad, not great, just okay overall.",
    "Reasonable quality for an average price.",
]

# Short, plain reviews (2-5 words) -- the original dataset skews toward
# long-form reviews, so the model has very little signal for how to
# classify brief ones. These fill that gap directly.
SHORT_NEGATIVE = [
    "Bad shoes.",
    "Terrible shoes.",
    "Awful quality.",
    "Really bad purchase.",
    "Do not buy these.",
    "Poor quality shoes.",
    "Worst shoes ever.",
    "Very disappointing.",
    "Not worth it.",
    "Hate these shoes.",
]

SHORT_POSITIVE = [
    "Great shoes.",
    "Love these shoes.",
    "Excellent quality.",
    "Really great purchase.",
    "Best shoes ever.",
    "Highly recommend these.",
    "Amazing shoes.",
    "Very comfortable shoes.",
    "Worth every penny.",
    "Fantastic purchase.",
]

SHORT_NEUTRAL = [
    "Okay shoes.",
    "Average quality.",
    "It's fine.",
    "Decent shoes.",
    "Nothing special.",
    "So-so quality.",
    "Just okay.",
    "Average purchase.",
]


def main():
    df = pd.read_excel(SRC_PATH)

    augmented_rows = (
        [{"Review": t, "Sentiment": "Negative"} for t in NEGATIVE_TEMPLATES]
        + [{"Review": t, "Sentiment": "Positive"} for t in POSITIVE_TEMPLATES]
        + [{"Review": t, "Sentiment": "Neutral"} for t in NEUTRAL_TEMPLATES]
        + [{"Review": t, "Sentiment": "Negative"} for t in SHORT_NEGATIVE]
        + [{"Review": t, "Sentiment": "Positive"} for t in SHORT_POSITIVE]
        + [{"Review": t, "Sentiment": "Neutral"} for t in SHORT_NEUTRAL]
    )
    aug_df = pd.DataFrame(augmented_rows)

    combined = pd.concat([df, aug_df], ignore_index=True)
    combined.to_excel(OUT_PATH, index=False)
    print(f"Original rows: {len(df)}, augmented rows added: {len(aug_df)}")
    print(f"Combined dataset written to {OUT_PATH}")


if __name__ == "__main__":
    main()
