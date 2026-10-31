# Offline e-waste category suggestion model

## What the feature does

EcoSmart includes an optional text classifier that suggests one of the seven e-waste categories from a short device/problem description. It runs inside the Flask application using scikit-learn; it does not call a paid AI API or send suggestion text to an external model provider. The suggestion is optional. The user must choose and confirm the final category before submitting a report.

The pipeline uses `TfidfVectorizer` with word-boundary character n-grams of length 3–5, followed by a balanced `LogisticRegression` classifier. The character features can recognize some spelling and word-form variation; they do not understand meaning like a large language model. TF-IDF turns text into weighted numerical features; the classifier learns label patterns from the example corpus. [scikit-learn documents TF-IDF and character n-grams](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction). scikit-learn is distributed under the BSD 3-Clause license; its license terms are included in its upstream repository. [scikit-learn license](https://github.com/scikit-learn/scikit-learn/blob/main/COPYING).

## Training data and limitations

`data/category_training_samples.csv` contains 84 short, manually authored synthetic examples (12 per category). It is an openly inspectable teaching seed, not an official or representative dataset. Similar phrases in training and real reports can make an offline demonstration appear more accurate than it really is. The returned `model_score` is a ranking score, not a calibrated probability, guarantee, recycling decision, or safety assessment.

Do not describe this seed model as production-accurate. Do not use its suggestion to make decisions about hazards, legal compliance, value, or collection eligibility. A real deployment would need a consented and representative labelled dataset, documented annotation rules, class-balance checks, a held-out evaluation set, per-category precision/recall analysis, monitoring for language and device drift, and human review. Never train on personal report text without an appropriate privacy basis and user safeguards.

With the code and sample corpus shipped here, the reproducible five-fold run measured **0.67 accuracy and 0.66 weighted F1** on synthetic examples. The `Other Electronic Waste` class had only 0.33 F1, and `Computer Accessories` 0.45 F1 in that run. These scores describe the limited synthetic corpus only and should be presented as a baseline/limitation, not a real-world accuracy claim.

## Reproduce evaluation

Install project dependencies, activate the virtual environment, and run from the repository root:

```powershell
python -m ai.evaluate_category_model
```

The script uses stratified five-fold cross-validation and prints a classification report and confusion matrix. The printed metrics describe only the bundled synthetic examples. They are not an estimate of performance on reports from Pune or other real users.

## Endpoints

- `GET /api/ai/model` returns the model version, library version, supported labels, training-example count, and limitations.
- `POST /api/ai/suggest-category` accepts JSON `{"text": "..."}` and returns a suggested label with the top three model scores. It requires the same CSRF header as other state-changing requests.

## Environmental context

This academic prototype is not affiliated with a municipality or the Central Pollution Control Board (CPCB), and it does not dispatch collectors. For current Indian rules and guidance, consult the [CPCB E-Waste Management Rules page](https://cpcb.nic.in/rules-6/) and [CPCB e-waste FAQ](https://eprewaste.cpcb.gov.in/assets/PDF/faqewaste.pdf). These links are informational; EcoSmart does not integrate with the CPCB portal or verify recycler authorisation.
