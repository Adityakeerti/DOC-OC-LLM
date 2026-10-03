# DOC-OC v6 Marksheet Dataset

A curated, multi-board dataset of Indian educational marksheets and certificates designed for Vision-Language Model (VLM) benchmarking, fine-tuning (LoRA), and structured document extraction.

---

## 📊 Dataset Overview

* **Total Images**: 37 authentic scanned marksheets
* **Image Formats**: JPEG & PNG
* **Resolutions**: From 522×702 up to 4096×2304 (high-res scans)
* **Metadata Manifest**: [`dataset/manifest.json`](manifest.json)
* **Verified Ground Truth**: [`dataset/ground_truth/`](ground_truth/) (Hand-audited JSON labels)

---

## 🏛️ Education Board Diversity

| Board | Short Code | Documents | Notes |
| :--- | :---: | :---: | :--- |
| **Central Board of Secondary Education** | **CBSE** | 12 | Class X & XII, modern tabular, CCE CGPA (2011-13), dot-matrix (2008), floral bordered |
| **Council for the Indian School Certificate Examinations** | **CISCE / ICSE** | 5 | Class X (ICSE) & Class XII (ISC), sub-paper composite hierarchy, green security background |
| **Uttarakhand Board of School Education** | **UBSE** | 10 | Class X (High School) & XII (Intermediate), bilingual Hindi/English, state watermark |
| **Board of School Education Haryana** | **BSEH** | 2 | Secondary (Class 10) & Senior Secondary (Class 12) |
| **Uttar Pradesh Madhyamik Shiksha Parishad** | **UPMSP** | 1 | Class X High School, pink colored background |
| **General / Multi-board** | **Mixed** | 7 | Diverse state and senior school formats |

---

## 🗂️ Split Breakdown for Fine-Tuning

The dataset is partitioned in `manifest.json` for reproducible evaluation:

| Split | Count | Purpose |
| :--- | :---: | :--- |
| **Train** | **25** (67.6%) | Training LoRA / QLoRA adapters for document layout comprehension |
| **Validation** | **6** (16.2%) | Hyperparameter tuning & prompt iteration (includes Haryana, UP, CCE CGPA, dot-matrix) |
| **Test (Held-Out)** | **6** (16.2%) | Final zero-shot benchmark reporting (includes CBSE, ICSE, and Uttarakhand boards) |

---

## 📄 Target Ground Truth JSON Schema

Ground truth annotations in [`ground_truth/`](ground_truth/) strictly follow the universal marksheet schema:

```json
{
  "board": "string (Official board title)",
  "examination": "string (e.g. High School Examination - 2021)",
  "student_info": {
    "name": "string (Candidate's certified name)",
    "roll_no": "string",
    "enrollment_no": "string or null",
    "father_name": "string or null",
    "mother_name": "string or null",
    "school_name": "string or null",
    "dob": "string or null"
  },
  "subjects": [
    {
      "name": "string (Subject title)",
      "theory": "number or null",
      "practical": "number or null",
      "total": "number",
      "max_marks": "number or null",
      "grade": "string or null"
    }
  ],
  "result": {
    "total_obtained": "number or null",
    "maximum_marks": "number or null",
    "percentage": "string or null",
    "status": "PASS / FAIL / COMPARTMENT"
  }
}
```

---

## 🛠️ Usage

To inspect or rebuild the manifest and ground-truth index:

```bash
python dataset/build_manifest.py
```
