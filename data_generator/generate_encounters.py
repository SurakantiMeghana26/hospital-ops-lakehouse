from faker import Faker
import random
import csv
from datetime import timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

ADMISSION_TYPES = ["Emergency", "Elective", "Urgent", "Newborn"]
DISCHARGE_DISPOSITIONS = ["Home", "Skilled Nursing Facility", "Rehab", "Transferred", "Expired"]

def load_patient_ids(patients_csv_path):
    patient_ids = []
    with open(patients_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            patient_ids.append(row["patient_id"])
    return patient_ids
if __name__ == "__main__":
    ids = load_patient_ids("data_generator/output/patients.csv")
    print(f"Loaded {len(ids)} patient IDs")
    print(ids[:5])
def generate_encounter(encounter_id, patient_id):
    admission_date = fake.date_between(start_date="-2y", end_date="today")
    length_of_stay = random.randint(0, 14)
    discharge_date = admission_date + timedelta(days=length_of_stay)

    # ~3% of encounters: no discharge date yet (still admitted)
    still_admitted = random.random() < 0.03

    # ~10% of encounters: date stored in a different format (simulates a system change mid-year)
    use_alt_format = random.random() < 0.10
    if use_alt_format:
        admission_date_str = admission_date.strftime("%m/%d/%Y")
    else:
        admission_date_str = admission_date.isoformat()

    return {
        "encounter_id": encounter_id,
        "patient_id": patient_id,
        "admission_date": admission_date_str,
        "discharge_date": "" if still_admitted else discharge_date.isoformat(),
        "admission_type": random.choice(ADMISSION_TYPES),
        "discharge_disposition": "" if still_admitted else random.choice(DISCHARGE_DISPOSITIONS),
        "attending_provider_id": f"PROV{random.randint(1, 40):03d}",
    }
def generate_all_encounters(patient_ids):
    encounters = []
    encounter_id = 1

    for patient_id in patient_ids:
        # Most patients have 1-3 encounters; a smaller group has more (chronic/readmission cases)
        if random.random() < 0.15:
            num_encounters = random.randint(4, 8)   # frequent/chronic patients
        else:
            num_encounters = random.randint(0, 3)   # typical patients (some have zero)

        for _ in range(num_encounters):
            encounters.append(generate_encounter(encounter_id, patient_id))
            encounter_id += 1

    # Inject duplicates: ~2% of encounters get accidentally repeated,
    # simulating the source system re-sending the same record
    num_duplicates = int(len(encounters) * 0.02)
    duplicates = random.sample(encounters, num_duplicates)
    encounters.extend(duplicates)

    random.shuffle(encounters)
    return encounters


def write_encounters_to_csv(filepath, encounters):
    fieldnames = encounters[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(encounters)
    print(f"Generated {len(encounters)} encounter rows (including duplicates) -> {filepath}")


if __name__ == "__main__":
    patient_ids = load_patient_ids("data_generator/output/patients.csv")
    print(f"Loaded {len(patient_ids)} patient IDs")

    all_encounters = generate_all_encounters(patient_ids)
    write_encounters_to_csv("data_generator/output/encounters.csv", all_encounters)
