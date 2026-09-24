from faker import Faker
import random
import csv

fake = Faker()
Faker.seed(42)
random.seed(42)

NUM_PATIENTS = 500

def generate_patient(patient_id):
    return {
        "patient_id": patient_id,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date_of_birth(minimum_age=0, maximum_age=95).isoformat(),
        "gender": random.choice(["M", "F"]),
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state_abbr(),
        "zip_code": fake.zipcode(),
        "insurance_provider": random.choice(["Aetna", "UnitedHealth", "Cigna", "Blue Cross", "Medicare", "Medicaid"]),
    }

def write_patients_to_csv(filepath, num_patients):
    patients = [generate_patient(i) for i in range(1, num_patients + 1)]

    fieldnames = patients[0].keys()

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patients)

    print(f"Generated {len(patients)} patients -> {filepath}")


if __name__ == "__main__":
    write_patients_to_csv("data_generator/output/patients.csv", NUM_PATIENTS)