import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, coalesce

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

STAGING_BUCKET = "s3://hospitalops-staging-ss26mghn"

# --- Read all 5 raw tables from the Data Catalog ---
patients_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_raw", table_name="patients").toDF()
encounters_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_raw", table_name="encounters").toDF()
diagnoses_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_raw", table_name="diagnoses").toDF()
claims_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_raw", table_name="claims").toDF()
providers_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_raw", table_name="providers").toDF()

print(f"RAW - Patients: {patients_df.count()}, Encounters: {encounters_df.count()}, "
      f"Diagnoses: {diagnoses_df.count()}, Claims: {claims_df.count()}, Providers: {providers_df.count()}")

# --- Clean patients: fix zip_code type ---
patients_clean_df = patients_df.withColumn("zip_code", col("zip_code").cast("string"))

# --- Clean encounters: normalize dates, dedupe ---
encounters_clean_df = encounters_df.withColumn(
    "admission_date_clean",
    coalesce(
        to_date(col("admission_date"), "yyyy-MM-dd"),
        to_date(col("admission_date"), "MM/dd/yyyy")
    )
).drop("admission_date").withColumnRenamed("admission_date_clean", "admission_date")

encounters_dedup_df = encounters_clean_df.dropDuplicates(["encounter_id"])

# --- diagnoses, claims, providers: no known issues, pass through as-is ---
diagnoses_clean_df = diagnoses_df
claims_clean_df = claims_df
providers_clean_df = providers_df

print(f"CLEAN - Encounters after dedup: {encounters_dedup_df.count()}")

# --- Write all 5 cleaned tables to staging as Parquet ---
patients_clean_df.write.mode("overwrite").parquet(f"{STAGING_BUCKET}/patients/")
encounters_dedup_df.write.mode("overwrite").parquet(f"{STAGING_BUCKET}/encounters/")
diagnoses_clean_df.write.mode("overwrite").parquet(f"{STAGING_BUCKET}/diagnoses/")
claims_clean_df.write.mode("overwrite").parquet(f"{STAGING_BUCKET}/claims/")
providers_clean_df.write.mode("overwrite").parquet(f"{STAGING_BUCKET}/providers/")

print("Staging write complete - all 5 tables.")

job.commit()