from faker import Faker
import random
import csv

fake = Faker()
Faker.seed(42)
random.seed(42)

# Simplified realistic ICD-10 codes with descriptions
ICD10_CODES = [
    ("I50.9", "Heart failure, unspecified"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("J18.9", "Pneumonia, unspecified organism"),
    ("N39.0", "Urinary tract infection"),
    ("I21.9", "Acute myocardial infarction, unspecified"),
    ("J44.9", "COPD, unspecified"),
    ("K21.9", "GERD without esophagitis"),
    ("M17.9", "Osteoarthritis of knee, unspecified"),
    ("F32.9", "Major depressive disorder, single episode"),
    ("O80", "Encounter for full-term uncomplicated delivery"),
]

def load_encounter_ids(encounters_csv_path):
    encounter_ids = []
    with open(encounters_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            encounter_ids.append(row["encounter_id"])
    return encounter_ids

def generate_diagnoses_for_encounter(diagnosis_id_start, encounter_id):
    num_diagnoses = random.randint(1, 3)
    chosen = random.sample(ICD10_CODES, num_diagnoses)
    diagnoses = []
    for idx, (code, description) in enumerate(chosen):
        diagnoses.append({
            "diagnosis_id": diagnosis_id_start + idx,
            "encounter_id": encounter_id,
            "icd10_code": code,
            "description": description,
            "is_primary": "true" if idx == 0 else "false",
        })
    return diagnoses

def generate_all_diagnoses(encounter_ids):
    all_diagnoses = []
    diagnosis_id = 1
    for encounter_id in encounter_ids:
        # ~4% of encounters: missing diagnosis entirely (not yet coded by billing dept)
        if random.random() < 0.04:
            continue
        batch = generate_diagnoses_for_encounter(diagnosis_id, encounter_id)
        all_diagnoses.extend(batch)
        diagnosis_id += len(batch)
    return all_diagnoses

def write_diagnoses_to_csv(filepath, diagnoses):
    fieldnames = diagnoses[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(diagnoses)
    print(f"Generated {len(diagnoses)} diagnosis rows -> {filepath}")

if __name__ == "__main__":
    encounter_ids = load_encounter_ids("data_generator/output/encounters.csv")
    print(f"Loaded {len(encounter_ids)} encounter IDs")
    all_diagnoses = generate_all_diagnoses(encounter_ids)
    write_diagnoses_to_csv("data_generator/output/diagnoses.csv", all_diagnoses)