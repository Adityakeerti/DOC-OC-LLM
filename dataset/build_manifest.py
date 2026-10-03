import os
import json
from pathlib import Path
from PIL import Image

DATA_DIR = Path(__file__).parent
GT_DIR = DATA_DIR / "ground_truth"
GT_DIR.mkdir(exist_ok=True)

# 1. Write verified ground truth JSON files
ground_truths = {
    "10_1.json": {
        "board": "Council for the Indian School Certificate Examinations, New Delhi",
        "examination": "Indian Certificate of Secondary Education (Class - X) - Year 2021",
        "student_info": {
            "name": "DEVANG SHARMA",
            "roll_no": "TT 40195250",
            "enrollment_no": "7396962",
            "father_name": "MAHENDRA KUMAR SHARMA",
            "mother_name": "CHHAVI SHARMA",
            "school_name": "ST. JOSEPH'S ACADEMY, DEHRA DUN",
            "dob": "23.10.2005"
        },
        "subjects": [
            {"name": "English", "theory": None, "practical": None, "total": 89.0, "max_marks": 100.0, "grade": None},
            {"name": "Hindi", "theory": None, "practical": None, "total": 99.0, "max_marks": 100.0, "grade": None},
            {"name": "History, Civics & Geography", "theory": None, "practical": None, "total": 89.0, "max_marks": 100.0, "grade": None},
            {"name": "Mathematics", "theory": None, "practical": None, "total": 79.0, "max_marks": 100.0, "grade": None},
            {"name": "Science", "theory": None, "practical": None, "total": 81.0, "max_marks": 100.0, "grade": None},
            {"name": "Computer Applications", "theory": None, "practical": None, "total": 86.0, "max_marks": 100.0, "grade": None},
            {"name": "SUPW and Community Service", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A"}
        ],
        "result": {
            "total_obtained": None,
            "maximum_marks": None,
            "percentage": "89%",
            "status": "PASS"
        }
    },
    "10_2.json": {
        "board": "Board of School Education Uttarakhand",
        "examination": "High School Examination - 2021",
        "student_info": {
            "name": "KUNWAR KAPIL SINGH KARKI",
            "roll_no": "21085505",
            "father_name": "JAGJIT SINGH",
            "mother_name": "BHARATI DEVI",
            "school_name": "K.M.S.B. HIMALAYA I.C. CHOUKORI, PITHORAGARH",
            "dob": "04-05-2004"
        },
        "subjects": [
            {"name": "HINDI", "theory": 79.0, "practical": None, "total": 79.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "ENGLISH", "theory": 83.0, "practical": None, "total": 83.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "MATHEMATICS", "theory": 71.0, "practical": 20.0, "total": 91.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SCIENCE", "theory": 60.0, "practical": 20.0, "total": 80.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SOCIAL SCIENCE", "theory": 72.0, "practical": 20.0, "total": 92.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SANSKRIT", "theory": 82.0, "practical": None, "total": 82.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 425.0,
            "maximum_marks": 500.0,
            "percentage": "85.0%",
            "status": "PASS"
        }
    },
    "10_3.json": {
        "board": "Central Board of Secondary Education",
        "examination": "Secondary School Examination, 2021",
        "student_info": {
            "name": "VANSH JAISWAL",
            "roll_no": "25114139",
            "father_name": "RAJU JAISWAL",
            "mother_name": "MANJU JAISWAL",
            "school_name": "SAPIENCE SCHOOL VIKAS NAGAR DEHRADUN UK",
            "dob": "21-10-2004"
        },
        "subjects": [
            {"name": "English Lng & Lit.", "theory": 80.0, "practical": 20.0, "total": 100.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "Hindi Course-A", "theory": 70.0, "practical": 20.0, "total": 90.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "Mathematics Standard", "theory": 77.0, "practical": 20.0, "total": 97.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "Science", "theory": 75.0, "practical": 20.0, "total": 95.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "Social Science", "theory": 72.0, "practical": 20.0, "total": 92.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "Information Technology", "theory": 50.0, "practical": 50.0, "total": 100.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 574.0,
            "maximum_marks": 600.0,
            "percentage": "95.67%",
            "status": "PASS"
        }
    },
    "10_4.json": {
        "board": "Board of School Education Uttarakhand",
        "examination": "High School Examination - 2021",
        "student_info": {
            "name": "ROHIT PATHAK",
            "roll_no": "21085521",
            "father_name": "NAVEEN CHANDRA PATHAK",
            "mother_name": "GEETA PATHAK",
            "school_name": "K.M.S.B. HIMALAYA I.C. CHOUKORI, PITHORAGARH",
            "dob": "01-11-2005"
        },
        "subjects": [
            {"name": "HINDI", "theory": 77.0, "practical": None, "total": 77.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "ENGLISH", "theory": 89.0, "practical": None, "total": 89.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "MATHEMATICS", "theory": 77.0, "practical": 20.0, "total": 97.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SCIENCE", "theory": 72.0, "practical": 20.0, "total": 92.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SOCIAL SCIENCE", "theory": 75.0, "practical": 20.0, "total": 95.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "SANSKRIT", "theory": 80.0, "practical": None, "total": 80.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 450.0,
            "maximum_marks": 500.0,
            "percentage": "90.0%",
            "status": "PASS"
        }
    },
    "12_1.json": {
        "board": "Council for the Indian School Certificate Examinations, New Delhi",
        "examination": "Indian School Certificate Examination (Class - XII) - Year 2023",
        "student_info": {
            "name": "DEVANG SHARMA",
            "roll_no": "BG 90094366",
            "enrollment_no": "7396962",
            "father_name": "MAHENDRA KUMAR SHARMA",
            "mother_name": "CHHAVI SHARMA",
            "school_name": "ST. JOSEPH'S ACADEMY, DEHRA DUN"
        },
        "subjects": [
            {"name": "ENGLISH", "theory": None, "practical": None, "total": 86.0, "max_marks": 100.0, "grade": "EIGHT SIX"},
            {"name": "PSYCHOLOGY", "theory": None, "practical": None, "total": 78.0, "max_marks": 100.0, "grade": "SEVEN EIGHT"},
            {"name": "MATHEMATICS", "theory": None, "practical": None, "total": 64.0, "max_marks": 100.0, "grade": "SIX FOUR"},
            {"name": "PHYSICS", "theory": None, "practical": None, "total": 87.0, "max_marks": 100.0, "grade": "EIGHT SEVEN"},
            {"name": "CHEMISTRY", "theory": None, "practical": None, "total": 68.0, "max_marks": 100.0, "grade": "SIX EIGHT"},
            {"name": "SUPW AND COMMUNITY SERVICE", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A"}
        ],
        "result": {
            "total_obtained": 383.0,
            "maximum_marks": 500.0,
            "percentage": "76.6%",
            "status": "PASS"
        }
    },
    "12_2.json": {
        "board": "Board of School Education Uttarakhand",
        "examination": "Intermediate Examination - 2023",
        "student_info": {
            "name": "KUNWAR KAPIL SINGH KARKI",
            "roll_no": "23374463",
            "father_name": "JAGJIT SINGH",
            "mother_name": "BHARTI KARKI",
            "school_name": "K.M.S.B. HIMALAYA INTER COLLEGE CHAUKORI, PITHORAGARH"
        },
        "subjects": [
            {"name": "HINDI", "theory": 54.0, "practical": 20.0, "total": 74.0, "max_marks": 100.0, "grade": "B1"},
            {"name": "MATHEMATICS", "theory": 53.0, "practical": 20.0, "total": 73.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "PHYSICS", "theory": 26.0, "practical": 30.0, "total": 56.0, "max_marks": 100.0, "grade": "B2"},
            {"name": "CHEMISTRY", "theory": 44.0, "practical": 30.0, "total": 74.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "ENGLISH", "theory": 60.0, "practical": 19.0, "total": 79.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 356.0,
            "maximum_marks": 500.0,
            "percentage": "71.2%",
            "status": "PASS"
        }
    },
    "12_3.json": {
        "board": "Central Board of Secondary Education",
        "examination": "Senior School Certificate Examination, 2023",
        "student_info": {
            "name": "VANSH JAISWAL",
            "roll_no": "25618434",
            "father_name": "RAJU JAISWAL",
            "mother_name": "MANJU JAISWAL",
            "school_name": "SAPIENCE SCHOOL VIKAS NAGAR DEHRADUN UK"
        },
        "subjects": [
            {"name": "English Core", "theory": 62.0, "practical": 20.0, "total": 82.0, "max_marks": 100.0, "grade": "B1"},
            {"name": "Mathematics", "theory": 34.0, "practical": 20.0, "total": 54.0, "max_marks": 100.0, "grade": "C2"},
            {"name": "Physics", "theory": 40.0, "practical": 28.0, "total": 68.0, "max_marks": 100.0, "grade": "B2"},
            {"name": "Chemistry", "theory": 40.0, "practical": 30.0, "total": 70.0, "max_marks": 100.0, "grade": "B2"},
            {"name": "Painting", "theory": 26.0, "practical": 70.0, "total": 96.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "Computer Science", "theory": 60.0, "practical": 30.0, "total": 90.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "Work Experience", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "Health & Physical Education", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "General Studies", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 460.0,
            "maximum_marks": 500.0,
            "percentage": "92.0%",
            "status": "PASS"
        }
    },
    "12_4.json": {
        "board": "Board of School Education Uttarakhand",
        "examination": "Intermediate Examination - 2023",
        "student_info": {
            "name": "ROHIT PATHAK",
            "roll_no": "23374475",
            "father_name": "NAVEEN CHANDRA PATHAK",
            "mother_name": "GEETA PATHAK",
            "school_name": "K.M.S.B. HIMALAYA INTER COLLEGE CHAUKORI, PITHORAGARH"
        },
        "subjects": [
            {"name": "HINDI", "theory": 70.0, "practical": 20.0, "total": 90.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "MATHEMATICS", "theory": 54.0, "practical": 20.0, "total": 74.0, "max_marks": 100.0, "grade": "A2"},
            {"name": "PHYSICS", "theory": 40.0, "practical": 30.0, "total": 70.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "CHEMISTRY", "theory": 59.0, "practical": 30.0, "total": 89.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "ENGLISH", "theory": 77.0, "practical": 19.0, "total": 96.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 419.0,
            "maximum_marks": 500.0,
            "percentage": "83.8%",
            "status": "PASS"
        }
    },
    "cbse_sample_ajay.json": {
        "board": "Central Board of Secondary Education, Delhi",
        "examination": "Secondary School Examination (Session : 2011-2013)",
        "student_info": {
            "name": "AJAY",
            "roll_no": "2158156",
            "father_name": "JAWAHAR LAL",
            "mother_name": "ASHA RANI",
            "school_name": "04015-K V NO. 1 CHANDIMANDIR CANTT HARYANA",
            "dob": "28/10/1997"
        },
        "subjects": [
            {"name": "ENGLISH COMM.", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "HINDI COURSE-A", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "MATHEMATICS", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "SCIENCE", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"},
            {"name": "SOCIAL SCIENCE", "theory": None, "practical": None, "total": None, "max_marks": None, "grade": "A1"}
        ],
        "result": {
            "total_obtained": None,
            "maximum_marks": None,
            "percentage": "CGPA 10.0",
            "status": "PASS"
        }
    },
    "state_sample_ms7.json": {
        "board": "Central Board of Secondary Education",
        "examination": "All India Senior School Certificate Examination, 2008",
        "student_info": {
            "name": "ABHINAV BISWAS",
            "roll_no": "5652695",
            "father_name": "KARUNAMOY BISWAS",
            "mother_name": "APARNA BISWAS",
            "school_name": "08468 ARMY SCHOOL BARRACKPORE CANTT 24 PARGANAS WB"
        },
        "subjects": [
            {"name": "ENGLISH CORE", "theory": 87.0, "practical": None, "total": 87.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "MATHEMATICS", "theory": 95.0, "practical": None, "total": 95.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "PHYSICS", "theory": 58.0, "practical": 30.0, "total": 88.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "CHEMISTRY", "theory": 66.0, "practical": 29.0, "total": 95.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "COMPUTER SCIENCE", "theory": 62.0, "practical": 30.0, "total": 92.0, "max_marks": 100.0, "grade": "A1"},
            {"name": "PHYSICAL EDUCATION", "theory": 65.0, "practical": 23.0, "total": 88.0, "max_marks": 100.0, "grade": "A1"}
        ],
        "result": {
            "total_obtained": 545.0,
            "maximum_marks": 600.0,
            "percentage": "90.83%",
            "status": "PASS"
        }
    }
}

for fname, data in ground_truths.items():
    (GT_DIR / fname).write_text(json.dumps(data, indent=2, ensure_ascii=False))
print(f"✅ Generated {len(ground_truths)} gold-standard ground truth annotations in ground_truth/")

# 2. Build full dataset manifest
images = sorted([p for p in DATA_DIR.iterdir() if p.suffix.lower() in ['.jpg', '.jpeg', '.png']])
manifest = []

# Balanced train / val / test split
test_stems = {"10_1", "10_2", "10_3", "12_1", "12_3", "12_4"}
val_stems = {"10_4", "12_2", "cbse_sample_ajay", "state_sample_ms7", "haryana_10th", "up_board_10th"}

for p in images:
    with Image.open(p) as img:
        w, h = img.size
        fmt = img.format
    
    stem = p.stem
    gt_file = GT_DIR / f"{stem}.json"
    has_gt = gt_file.exists()

    # Determine Board
    if "cbse" in stem.lower() or stem in ["10_3", "12_3"]:
        board = "CBSE"
    elif "icse" in stem.lower() or stem in ["10_1", "12_1"]:
        board = "CISCE (ICSE/ISC)"
    elif "haryana" in stem.lower():
        board = "BSEH (Haryana)"
    elif "up_board" in stem.lower():
        board = "UPMSP (Uttar Pradesh)"
    elif stem in ["10_2", "10_4", "12_2", "12_4"]:
        board = "UBSE (Uttarakhand)"
    else:
        board = "General / Multi-board"

    # Split assignment
    if stem in test_stems:
        split = "test"
    elif stem in val_stems:
        split = "validation"
    else:
        split = "train"

    manifest.append({
        "filename": p.name,
        "board": board,
        "width": w,
        "height": h,
        "format": fmt,
        "size_kb": round(p.stat().st_size / 1024, 1),
        "split": split,
        "has_ground_truth": has_gt
    })

manifest_file = DATA_DIR / "manifest.json"
manifest_file.write_text(json.dumps({
    "dataset_name": "DOC-OC Marksheet Benchmark & Training Dataset",
    "version": "6.0",
    "total_images": len(manifest),
    "split_counts": {
        "train": sum(1 for m in manifest if m["split"] == "train"),
        "validation": sum(1 for m in manifest if m["split"] == "validation"),
        "test": sum(1 for m in manifest if m["split"] == "test")
    },
    "records": manifest
}, indent=2, ensure_ascii=False))

print(f"✅ Generated dataset manifest: {manifest_file} with {len(manifest)} image entries.")
