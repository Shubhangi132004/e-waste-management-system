"""Run reproducible stratified cross-validation for the demo text classifier.

Run from the project root with: python -m ai.evaluate_category_model
The output evaluates only the bundled synthetic examples, not real-world performance.
"""
from __future__ import annotations

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report, confusion_matrix

from ai.category_classifier import DATASET_PATH, CategoryClassifier


def main() -> None:
    classifier = CategoryClassifier()
    rows = classifier._rows
    texts = [row["text"] for row in rows]
    labels = [row["category"] for row in rows]
    pipeline = classifier._pipeline
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    predictions = cross_val_predict(pipeline, texts, labels, cv=cv)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Synthetic examples: {len(rows)}")
    print("\nCross-validation classification report (synthetic data only):")
    print(classification_report(labels, predictions, zero_division=0))
    categories = classifier._categories
    print("Confusion matrix; rows=true category, columns=predicted category:")
    print("Categories:", " | ".join(categories))
    print(confusion_matrix(labels, predictions, labels=categories))
    print("\nDo not interpret these metrics as real-world accuracy. Validate with consented, representative, labelled reports.")


if __name__ == "__main__":
    main()
