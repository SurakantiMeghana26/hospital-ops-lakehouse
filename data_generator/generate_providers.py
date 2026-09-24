from faker import Faker
import random
import csv

fake = Faker()
Faker.seed(42)
random.seed(42)

SPECIALTIES = ["Cardiology", "Internal Medicine", "Emergency Medicine", "Orthopedics",
               "Pediatrics", "Obstetrics", "Oncology", "Neurology", "General Surgery", "Psychiatry"]

DEPARTMENTS = ["ICU", "ER", "Med-Surg", "Cardiology Unit", "Oncology Unit", "Maternity", "Outpatient"]

NUM_PROVIDERS = 40  # matches PROV001-PROV040 used in encounters.py

def generate_provider(provider_id_num):
    return {
        "provider_id": f"PROV{provider_id_num:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "specialty": random.choice(SPECIALTIES),
        "department": random.choice(DEPARTMENTS),
        "npi_number": fake.numerify("##########"),  # 10-digit fake NPI (National Provider Identifier)
    }

def write_providers_to_csv(filepath, num_providers):
    providers = [generate_provider(i) for i in range(1, num_providers + 1)]
    fieldnames = providers[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(providers)
    print(f"Generated {len(providers)} providers -> {filepath}")

if __name__ == "__main__":
    write_providers_to_csv("data_generator/output/providers.csv", NUM_PROVIDERS)