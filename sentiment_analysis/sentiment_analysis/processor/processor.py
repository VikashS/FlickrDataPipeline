from loguru import logger
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col, from_json, sum
from pyspark.sql.types import StructType, StringType, TimestampType, StructField, ArrayType, DataType
from pyspark.sql import functions as f

from sentiment_analysis.processor.config import *

def start_streaming():
    spark = SparkSession.builder.appName("flickr").master("local[*]")\
        .config("spark.streaming.stopGracefullyOnShutdown","true")\
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3").getOrCreate()

    # Define schema for Kafka data
    schema = StructType([
        StructField("area", StringType(), True),
        StructField("tags", ArrayType(StringType()), True),
        StructField("timestamp", TimestampType(), True)
    ])

    # Read from Kafka
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse JSON data
    parsed_df = df.selectExpr("CAST(value AS STRING)") \
               .select(from_json(col("value"), schema).alias("data")) \
               .select("data.*")

    # Explode tags and group by area
    tag_counts = parsed_df \
        .withColumn("tag", explode(col("tags"))) \
        .groupBy("area", "tag") \
        .count().orderBy(f.col("count").desc())

    # Write output to console
    query = tag_counts \
        .writeStream \
        .outputMode("complete") \
        .option("checkpointLocation", CHECKPOINT_DIR) \
        .format("console") \
        .start()

    query.awaitTermination()


if __name__=="__main__":
    logger.info(f'start streaming')
    start_streaming()
    logger.info(f'End streaming')
