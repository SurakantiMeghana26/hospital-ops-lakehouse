import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.window import Window
from pyspark.sql.functions import col, lag, datediff, when

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

CURATED_BUCKET = "s3://hospitalops-curated-ss26mghn"

# --- Read staging tables ---
encounters_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_staging", table_name="encounters").toDF()

print(f"STAGING - Encounters: {encounters_df.count()}")

# --- Only encounters with a real discharge_date can be used to measure readmission ---
# (still-admitted patients have no discharge_date - exclude those from the "previous" side of the comparison)
encounters_with_discharge = encounters_df.withColumn(
    "discharge_date", col("discharge_date").cast("date")
)

# --- Window: for each patient, order their encounters by admission_date ---
patient_window = Window.partitionBy("patient_id").orderBy("admission_date")

# --- Get each patient's PREVIOUS discharge_date, on the same row as the current encounter ---
encounters_with_prev = encounters_with_discharge.withColumn(
    "prev_discharge_date", lag("discharge_date").over(patient_window)
)

# --- Compute days between previous discharge and this admission ---
encounters_with_gap = encounters_with_prev.withColumn(
    "days_since_prev_discharge", datediff(col("admission_date"), col("prev_discharge_date"))
)

# --- Flag as readmission if gap exists and is <= 30 days ---
readmission_risk_df = encounters_with_gap.withColumn(
    "is_30_day_readmission",
    when(
        (col("days_since_prev_discharge").isNotNull()) & (col("days_since_prev_discharge") <= 30),
        True
    ).otherwise(False)
).select(
    "encounter_id", "patient_id", "admission_date", "discharge_date",
    "prev_discharge_date", "days_since_prev_discharge", "is_30_day_readmission"
)

readmission_count = readmission_risk_df.filter(col("is_30_day_readmission") == True).count()
print(f"CURATED - Total encounters: {readmission_risk_df.count()}, Flagged as 30-day readmissions: {readmission_count}")

# --- Write to curated ---
readmission_risk_df.write.mode("overwrite").parquet(f"{CURATED_BUCKET}/readmission_risk/")

print("Curated write complete - readmission_risk.")

job.commit()