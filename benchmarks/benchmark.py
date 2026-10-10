"""
benchmark.py — Test the VLM pipeline on all marksheet images.

Runs each image through: preprocess → extract → validate
Prints a live summary and saves detailed results to results/.

Usage:
    python benchmark.py                    # test all images in dataset/
    python benchmark.py some_folder/       # test images in a specific folder
"""

import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import prepare, extract, validate


def run(dataset_dir: str = "dataset"):
    """Process every image and save results."""
    dataset = Path(dataset_dir)
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # Find all images
    images = sorted(
        f for f in dataset.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".pdf")
    )

    if not images:
        print(f"No images found in {dataset_dir}/")
        return

    print(f"Found {len(images)} images in {dataset_dir}/")
    print("=" * 60)

    summary = []

    for i, path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] {path.name}")

        try:
            # Preprocess
            t0 = time.time()
            image = prepare(str(path))
            t_pre = time.time() - t0

            # Extract via VLM
            t0 = time.time()
            raw = extract(image)
            t_ext = time.time() - t0

            # Validate
            marksheet, warnings = validate(raw)

            # Save result
            out_file = results_dir / f"{path.stem}.json"
            out_file.write_text(json.dumps({
                "source": path.name,
                "data": marksheet.model_dump(),
                "warnings": warnings,
                "timing": {"preprocess": round(t_pre, 2), "extract": round(t_ext, 2)},
            }, indent=2, ensure_ascii=False))

            # Print summary
            board = marksheet.board or "?"
            name = marksheet.student_info.name or "?"
            n = len(marksheet.subjects)
            print(f"  ✅ {board} | {name} | {n} subjects | {t_ext:.1f}s")
            if warnings:
                for w in warnings:
                    print(f"  ⚠️  {w}")

            summary.append({"file": path.name, "status": "ok", "board": board,
                            "subjects": n, "time": round(t_ext, 2)})

        except Exception as e:
            print(f"  ❌ {e}")
            summary.append({"file": path.name, "status": "error", "error": str(e)})

    # Final summary
    ok = sum(1 for s in summary if s["status"] == "ok")
    print("\n" + "=" * 60)
    print(f"Done: {ok}/{len(summary)} succeeded")
    print(f"Results saved to {results_dir}/")

    # Save summary
    (results_dir / "_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "dataset"
    run(folder)
