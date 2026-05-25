import os
import json
import time
import sys
from datetime import datetime
from datasets import load_dataset
from tqdm import tqdm
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── Import from our project ───────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.bias_classifier import classify_bias

# ── Label mapping ─────────────────────────────────────────
id2label = {0: "LEFT", 1: "CENTER", 2: "RIGHT"}
label2id = {"LEFT": 0, "CENTER": 1, "RIGHT": 2}

# ── Output paths ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(BASE_DIR, "dashboard")
CONFUSION_MATRIX_PATH = os.path.join(DASHBOARD_DIR, "confusion_matrix.png")
METRICS_JSON_PATH = os.path.join(DASHBOARD_DIR, "metrics.json")


def load_test_data():
    print("Loading dataset: Faith1712/Allsides_political_bias_proper")
    dataset = load_dataset("Faith1712/Allsides_political_bias_proper")

    # Use last 20% as test set
    full_data = dataset["train"]
    split = full_data.train_test_split(test_size=0.2, seed=42)
    test_data = split["test"]

    print(f"Test samples loaded: {len(test_data)}")

    from collections import Counter
    label_counts = Counter(test_data["label"])
    print("Label distribution in test set:")
    for label_id, count in sorted(label_counts.items()):
        print(f"  {id2label[label_id]}: {count} samples")

    return test_data


def run_inference(test_data):
    print("\nRunning inference on test set...")
    print("This takes 15-30 minutes on CPU. Please wait.\n")

    true_labels = []
    pred_labels = []
    errors = 0

    for i, sample in enumerate(tqdm(test_data, desc="Evaluating")):
        try:
            text = sample["text"]
            true_label_id = sample["label"]

            if not text or len(text.strip()) < 10:
                errors += 1
                continue

            result = classify_bias(text)

            if result["error"]:
                errors += 1
                continue

            pred_label_id = label2id[result["label"]]
            true_labels.append(true_label_id)
            pred_labels.append(pred_label_id)

            if (i + 1) % 100 == 0:
                current_acc = accuracy_score(true_labels, pred_labels) * 100
                tqdm.write(f"  Processed {i+1} articles — Running accuracy: {current_acc:.1f}%")

        except Exception as e:
            errors += 1
            continue

    print(f"\nInference complete")
    print(f"Successfully processed: {len(true_labels)} articles")
    print(f"Skipped due to errors: {errors} articles")

    return true_labels, pred_labels


def calculate_metrics(true_labels, pred_labels):
    accuracy = accuracy_score(true_labels, pred_labels)
    weighted_f1 = f1_score(true_labels, pred_labels, average="weighted", zero_division=0)
    macro_f1 = f1_score(true_labels, pred_labels, average="macro", zero_division=0)

    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels, pred_labels,
        labels=[0, 1, 2],
        zero_division=0
    )

    cm = confusion_matrix(true_labels, pred_labels, labels=[0, 1, 2])

    return {
        "accuracy": accuracy,
        "weighted_f1": weighted_f1,
        "macro_f1": macro_f1,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "support": support,
        "confusion_matrix": cm
    }


def print_results(metrics):
    accuracy = metrics["accuracy"] * 100
    weighted_f1 = metrics["weighted_f1"]
    precision = metrics["precision"]
    recall = metrics["recall"]
    f1 = metrics["f1"]

    print("\n" + "="*55)
    print("         MODEL EVALUATION RESULTS")
    print("="*55)
    print(f"  Overall Accuracy  : {accuracy:.2f}%")
    print(f"  Weighted F1 Score : {weighted_f1:.4f}")
    print(f"  Macro F1 Score    : {metrics['macro_f1']:.4f}")
    print("-"*55)
    print(f"  {'Class':<12} {'Precision':<12} {'Recall':<12} {'F1':<10}")
    for i, label_name in id2label.items():
        print(f"  {label_name:<12} {precision[i]:<12.4f} {recall[i]:<12.4f} {f1[i]:<10.4f}")
    print("="*55)
    print("\nNOTE DOWN THESE NUMBERS — USE ON YOUR RESUME")
    print(f"\nResume line: Fine-tuned DistilBERT achieving {accuracy:.1f}%")
    print(f"accuracy and {weighted_f1:.2f} weighted F1 on AllSides political bias dataset")


def save_confusion_matrix(cm):
    os.makedirs(DASHBOARD_DIR, exist_ok=True)

    labels = ["LEFT", "CENTER", "RIGHT"]
    cm_percent = cm.astype(float)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_percent = cm_percent / row_sums * 100

    fig, ax = plt.subplots(figsize=(8, 6))

    sns.heatmap(
        cm_percent,
        annot=False,
        fmt="",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        linewidths=0.5
    )

    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(
                j + 0.5, i + 0.5,
                f"{cm[i][j]}\n({cm_percent[i][j]:.1f}%)",
                ha="center", va="center",
                fontsize=11, fontweight="bold",
                color="white" if cm_percent[i][j] > 50 else "black"
            )

    ax.set_title("DistilBERT Bias Classification — Confusion Matrix", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)

    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Confusion matrix saved to {CONFUSION_MATRIX_PATH}")


def save_metrics_json(metrics, total_samples):
    os.makedirs(DASHBOARD_DIR, exist_ok=True)

    precision = metrics["precision"]
    recall = metrics["recall"]
    f1 = metrics["f1"]
    support = metrics["support"]
    cm = metrics["confusion_matrix"]

    metrics_dict = {
        "overall_accuracy": round(metrics["accuracy"], 4),
        "weighted_f1": round(metrics["weighted_f1"], 4),
        "macro_f1": round(metrics["macro_f1"], 4),
        "per_class": {
            "LEFT": {
                "precision": round(float(precision[0]), 4),
                "recall": round(float(recall[0]), 4),
                "f1": round(float(f1[0]), 4),
                "support": int(support[0])
            },
            "CENTER": {
                "precision": round(float(precision[1]), 4),
                "recall": round(float(recall[1]), 4),
                "f1": round(float(f1[1]), 4),
                "support": int(support[1])
            },
            "RIGHT": {
                "precision": round(float(precision[2]), 4),
                "recall": round(float(recall[2]), 4),
                "f1": round(float(f1[2]), 4),
                "support": int(support[2])
            }
        },
        "confusion_matrix": cm.tolist(),
        "total_test_samples": total_samples,
        "model_name": "DistilBERT fine-tuned on AllSides",
        "dataset": "Faith1712/Allsides_political_bias_proper",
        "evaluation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(METRICS_JSON_PATH, "w") as f:
        json.dump(metrics_dict, f, indent=2)

    print(f"Metrics saved to {METRICS_JSON_PATH}")
    return metrics_dict


if __name__ == "__main__":
    start_time = time.time()

    try:
        print("="*55)
        print("  STARTING MODEL EVALUATION")
        print("="*55)

        # Step 1 — Load test data
        test_data = load_test_data()

        # Step 2 — Run inference
        true_labels, pred_labels = run_inference(test_data)

        if len(true_labels) == 0:
            print("ERROR: No articles processed successfully")
            sys.exit(1)

        # Step 3 — Calculate metrics
        metrics = calculate_metrics(true_labels, pred_labels)

        # Step 4 — Print results
        print_results(metrics)

        # Step 5 — Save confusion matrix
        save_confusion_matrix(metrics["confusion_matrix"])

        # Step 6 — Save metrics JSON
        save_metrics_json(metrics, len(true_labels))

        # Step 7 — Total time
        elapsed = time.time() - start_time
        print(f"\nTotal evaluation time: {elapsed/60:.1f} minutes")
        print("\nEVALUATION COMPLETE")

    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        elapsed = time.time() - start_time
        print(f"Time elapsed before interrupt: {elapsed/60:.1f} minutes")
        sys.exit(0)