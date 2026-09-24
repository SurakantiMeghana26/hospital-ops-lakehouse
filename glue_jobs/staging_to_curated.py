import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.window import Window
from pyspark.sql.functions import col, lag, datediff, when, avg, sum as spark_sum, round as spark_round

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
claims_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_staging", table_name="claims").toDF()
diagnoses_df = glueContext.create_dynamic_frame.from_catalog(
    database="hospitalops_staging", table_name="diagnoses").toDF()

print(f"STAGING - Encounters: {encounters_df.count()}, Claims: {claims_df.count()}, Diagnoses: {diagnoses_df.count()}")

# Only keep primary diagnosis per encounter (avoids duplicating costs/LOS across multiple diagnosis rows)
primary_diagnoses_df = diagnoses_df.filter(col("is_primary") == "true")

# Cast discharge_date to real date type (used by both readmission and LOS logic below)
encounters_with_discharge = encounters_df.withColumn(
    "discharge_date", col("discharge_date").cast("date")
)

# =========================================
# MART 1: readmission_risk
# =========================================

patient_window = Window.partitionBy("patient_id").orderBy("admission_date")

encounters_with_prev = encounters_with_discharge.withColumn(
    "prev_discharge_date", lag("discharge_date").over(patient_window)
)

encounters_with_gap = encounters_with_prev.withColumn(
    "days_since_prev_discharge", datediff(col("admission_date"), col("prev_discharge_date"))
)

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
print(f"CURATED - readmission_risk: {readmission_risk_df.count()} total, {readmission_count} flagged as 30-day readmissions")

readmission_risk_df.write.mode("overwrite").parquet(f"{CURATED_BUCKET}/readmission_risk/")

# =========================================
# MART 2: claims_cost_summary
# =========================================

claims_with_diagnosis_df = claims_df.join(
    primary_diagnoses_df.select("encounter_id", "icd10_code", "description"),
    on="encounter_id",
    how="left"
)

claims_cost_summary_df = claims_with_diagnosis_df.groupBy(
    "icd10_code", "description", "insurance_provider"
).agg(
    spark_round(spark_sum("billed_amount"), 2).alias("total_billed"),
    spark_round(spark_sum("allowed_amount"), 2).alias("total_allowed"),
    spark_round(spark_sum("paid_amount"), 2).alias("total_paid")
)

print(f"CURATED - claims_cost_summary rows: {claims_cost_summary_df.count()}")

claims_cost_summary_df.write.mode("overwrite").parquet(f"{CURATED_BUCKET}/claims_cost_summary/")

# =========================================
# MART 3: los_by_diagnosis
# =========================================

encounters_with_los_df = encounters_with_discharge.withColumn(
    "length_of_stay_days", datediff(col("discharge_date"), col("admission_date"))
)

encounters_with_los_and_dx_df = encounters_with_los_df.join(
    primary_diagnoses_df.select("encounter_id", "icd10_code", "description"),
    on="encounter_id",
    how="left"
)

los_by_diagnosis_df = encounters_with_los_and_dx_df.filter(
    col("length_of_stay_days").isNotNull()
).groupBy(
    "icd10_code", "description", "admission_type"
).agg(
    spark_round(avg("length_of_stay_days"), 1).alias("avg_length_of_stay_days")
)

print(f"CURATED - los_by_diagnosis rows: {los_by_diagnosis_df.count()}")

los_by_diagnosis_df.write.mode("overwrite").parquet(f"{CURATED_BUCKET}/los_by_diagnosis/")

print("Curated write complete - all 3 marts.")

job.commit()