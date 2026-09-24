from faker import Faker
import random
import csv
from datetime import timedelta, date

fake = Faker()
Faker.seed(42)
random.seed(42)

INSURANCE_PROVIDERS = ["Aetna", "UnitedHealth", "Cigna", "Blue Cross", "Medicare", "Medicaid"]
CLAIM_STATUSES = ["Paid", "Denied", "Pending", "Partially Paid"]

def load_encounters(encounters_csv_path):
    encounters = []
    with open(encounters_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            encounters.append(row)
    return encounters

def generate_claim(claim_id, encounter):
    billed_amount = round(random.uniform(500, 45000), 2)
    status = random.choice(CLAIM_STATUSES)

    if status == "Denied":
        allowed_amount = 0
        paid_amount = 0
    elif status == "Pending":
        allowed_amount = ""   # not yet determined
        paid_amount = ""
    else:
        allowed_amount = round(billed_amount * random.uniform(0.5, 0.9), 2)
        paid_amount = round(allowed_amount * random.uniform(0.8, 1.0), 2) if status == "Paid" else round(allowed_amount * random.uniform(0.2, 0.7), 2)

    return {
        "claim_id": claim_id,
        "encounter_id": encounter["encounter_id"],
        "patient_id": encounter["patient_id"],
        "billed_amount": billed_amount,
        "allowed_amount": allowed_amount,
        "paid_amount": paid_amount,
        "claim_status": status,
        "insurance_provider": random.choice(INSURANCE_PROVIDERS),
    }

def generate_all_claims(encounters):
    claims = []
    claim_id = 1
    for encounter in encounters:
        # ~5% of encounters: no claim filed yet
        if random.random() < 0.05:
            continue
        claims.append(generate_claim(claim_id, encounter))
        claim_id += 1
    return claims

def write_claims_to_csv(filepath, claims):
    fieldnames = claims[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(claims)
    print(f"Generated {len(claims)} claim rows -> {filepath}")

if __name__ == "__main__":
    encounters = load_encounters("data_generator/output/encounters.csv")
    print(f"Loaded {len(encounters)} encounters")
    all_claims = generate_all_claims(encounters)
    write_claims_to_csv("data_generator/output/claims.csv", all_claims)