"""
prepare_dataset.py — Prepare multimodal conversation JSONL dataset for VLM fine-tuning.

Converts marksheet images and gold/audited labels into standard LLaVA/ShareGPT
conversational JSONL format for LoRA/QLoRA supervised fine-tuning (SFT).
"""

import json
from pathlib import Path
from pipeline import prepare, extract, validate

DATASET_DIR = Path("dataset")
MANIFEST_PATH = DATASET_DIR / "manifest.json"
GROUND_TRUTH_DIR = DATASET_DIR / "ground_truth"
OUTPUT_DIR = Path("training/data")


def load_ground_truth(filename: str) -> dict | None:
    """Find and return audited ground truth JSON if available."""
    stem = Path(filename).stem
    candidates = [
        GROUND_TRUTH_DIR / f"{stem}.json",
        GROUND_TRUTH_DIR / f"{filename}.json"
    ]
    for c in candidates:
        if c.exists():
            with open(c, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def build_conversation_entry(entry_id: str, image_rel_path: str, target_json: dict) -> dict:
    """Format single sample into multimodal conversation structure."""
    json_str = json.dumps(target_json, ensure_ascii=False, indent=2)
    return {
        "id": entry_id,
        "image": image_rel_path,
        "conversations": [
            {
                "from": "human",
                "value": "<image>\nExtract all data from this marksheet image into strict JSON according to the schema and layout rules."
            },
            {
                "from": "gpt",
                "value": json_str
            }
        ]
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    train_entries = []
    val_entries = []
    test_entries = []

    print(f"Loaded manifest with {len(manifest['records'])} records.")

    for rec in manifest["records"]:
        fname = rec["filename"]
        split = rec.get("split", "train")
        img_path = DATASET_DIR / fname

        if not img_path.exists():
            print(f"⚠️ Image not found: {img_path}, skipping.")
            continue

        gt = load_ground_truth(fname)

        if gt is not None:
            target_data = gt
            source = "GOLD_GROUND_TRUTH"
        else:
            print(f"Processing pseudo-label for {fname} via Phase 1 engine...")
            try:
                img = prepare(str(img_path))
                raw = extract(img)
                marksheet, _ = validate(raw)
                target_data = marksheet.model_dump()
                source = "VLM_PSEUDO_LABEL"
            except Exception as e:
                print(f"❌ Failed to extract {fname}: {e}, skipping.")
                continue

        entry = build_conversation_entry(
            entry_id=Path(fname).stem,
            image_rel_path=str(img_path),
            target_json=target_data
        )

        if split == "test":
            test_entries.append(entry)
        elif split == "validation":
            val_entries.append(entry)
        else:
            train_entries.append(entry)

        print(f"  [{source}] {fname} -> {split} split")

    # Write splits
    for name, entries in [("train.jsonl", train_entries), ("val.jsonl", val_entries), ("test.jsonl", test_entries)]:
        out_path = OUTPUT_DIR / name
        with open(out_path, "w", encoding="utf-8") as f:
            for item in entries:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"✅ Saved {len(entries)} samples to {out_path}")

    print("\nDataset preparation complete!")


if __name__ == "__main__":
    main()
