"""Offline text classifier for suggesting an e-waste report category.

The bundled examples are synthetic demonstrations, not a representative field dataset.
Predictions are suggestions for the user to confirm, never automatic decisions.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MODEL_VERSION = "ewaste-tfidf-logreg-v1"
DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "category_training_samples.csv"


def _load_training_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open("r", encoding="utf-8", newline="") as dataset_file:
        rows = [row for row in csv.DictReader(dataset_file) if row.get("text") and row.get("category")]
    if len(rows) < 14 or len({row["category"] for row in rows}) < 2:
        raise RuntimeError("The category model training data is missing or too small.")
    return rows


class CategoryClassifier:
    """Small CPU-only classifier, trained in memory from bundled example text."""

    def __init__(self) -> None:
        self._rows = _load_training_rows()
        self._categories = sorted({row["category"] for row in self._rows})
        self._pipeline = Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        sublinear_tf=True,
                        max_features=12000,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        C=4.0,
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        self._pipeline.fit([row["text"] for row in self._rows], [row["category"] for row in self._rows])

    def metadata(self) -> dict[str, Any]:
        return {
            "model": MODEL_VERSION,
            "library": "scikit-learn",
            "library_version": sklearn.__version__,
            "training_examples": len(self._rows),
            "categories": self._categories,
            "training_data_note": "Bundled synthetic demonstration examples; validate with representative labelled data before real-world use.",
            "inference": "local; submitted text is not sent to an external AI service",
        }

    def predict(self, text: str, limit: int = 3) -> dict[str, Any]:
        clean_text = " ".join(text.split())
        if not clean_text:
            raise ValueError("Enter a short description of the electronic item or issue first.")
        probabilities = self._pipeline.predict_proba([clean_text])[0]
        classifier = self._pipeline.named_steps["classifier"]
        ranked = sorted(
            zip(classifier.classes_, probabilities),
            key=lambda item: float(item[1]),
            reverse=True,
        )[:limit]
        best_category, best_score = ranked[0]
        return {
            "suggested_category": str(best_category),
            "model_score": round(float(best_score), 4),
            "alternatives": [
                {"category": str(category), "model_score": round(float(score), 4)}
                for category, score in ranked
            ],
            "model": MODEL_VERSION,
            "notice": "A model score is not a guarantee. Check the suggestion and choose the correct category yourself.",
        }


@lru_cache(maxsize=1)
def get_classifier() -> CategoryClassifier:
    """Train once per process and reuse the in-memory pipeline."""
    return CategoryClassifier()
