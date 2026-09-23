import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def main():
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_db = os.getenv("POSTGRES_DB", "postgres")
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "root")
    jdbc_url = f"jdbc:postgresql://{postgres_host}:5432/{postgres_db}"

    spark = SparkSession.builder \
        .appName("EcommerceRFMAnalysis") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print("Чтение заказов из PostgreSQL...")
    try:
        orders_df = spark.read \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", "orders") \
            .option("user", postgres_user) \
            .option("password", postgres_password) \
            .option("driver", "org.postgresql.Driver") \
            .load()
    except Exception as e:
        print(f"Ошибка при чтении из PostgreSQL: {e}")
        spark.stop()
        return

    orders_df = orders_df.withColumn("created_at", F.to_timestamp(F.col("created_at")))

    max_timestamp = orders_df.select(F.max("created_at")).collect()[0][0]

    print("Расчет RFM метрик...")
    rfm_raw = orders_df.groupBy("user_id").agg(
        F.datediff(F.lit(max_timestamp), F.max("created_at")).alias("recency_days"),
        F.count("id").alias("frequency"),
        F.sum("total_amount").alias("monetary")
    )

    r_window = Window.orderBy(F.col("recency_days").desc())
    f_window = Window.orderBy(F.col("frequency").asc())
    m_window = Window.orderBy(F.col("monetary").asc())

    rfm_scores = rfm_raw \
        .withColumn("r_score", F.ntile(5).over(r_window)) \
        .withColumn("f_score", F.ntile(5).over(f_window)) \
        .withColumn("m_score", F.ntile(5).over(m_window))

    rfm_segmented = rfm_scores.withColumn(
        "segment",
        F.when((F.col("r_score") >= 4) & (F.col("f_score") >= 4), "Champions")
         .when((F.col("r_score") >= 3) & (F.col("f_score") >= 3), "Loyal Customers")
         .when((F.col("r_score") >= 3) & (F.col("f_score") < 3), "Promising / Recent")
         .when((F.col("r_score") < 3) & (F.col("f_score") >= 3), "At Risk")
         .otherwise("Lost / Hibernating")
    ).withColumn("calculated_at", F.current_timestamp())

    print("Запись результатов в PostgreSQL (таблица user_rfm_segments)...")
    rfm_segmented.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "user_rfm_segments") \
        .option("user", postgres_user) \
        .option("password", postgres_password) \
        .option("driver", "org.postgresql.Driver") \
        .mode("overwrite") \
        .save()

    print("RFM-анализ успешно завершен!")
    spark.stop()

if __name__ == "__main__":
    main()
