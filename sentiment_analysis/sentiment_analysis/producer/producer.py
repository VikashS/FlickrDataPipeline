import requests
import json
from kafka import KafkaProducer
import time
from sentiment_analysis.producer.config import *
from loguru import logger


# Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_photos(lat, lon, radius):
    params = {
        'method': 'flickr.photos.search',
        'api_key': FLICKR_API_KEY,
        'lat': lat,
        'lon': lon,
        'radius': radius,
        'tags': TAG,
        'per_page': 10,  # Fetch 10 photos per request
        'format': 'json',
        'nojsoncallback': 1,
        'extras': 'tags'
    }
    response = requests.get(FLICKR_URL, params=params)
    return response.json().get('photos', {}).get('photo', [])

def start_producer_main():
    while True:
        for area in GEO_AREAS:
            photos = fetch_photos(area['lat'], area['lon'], area['radius'])
            for photo in photos:
                message = {
                    'area': area['name'],
                    'tags': photo.get('tags', '').split(),
                    'timestamp': time.time()
                }
                producer.send(TOPIC, value=message)
                logger.info(f"Sent photo data for {area['name']}: {message}")
        time.sleep(600) # sleep
        print("ended")


if __name__ == "__main__":
    logger.info(f'Consuming from Flickr started')
    start_producer_main()
    logger.info(f'Consuming from Flickr Ended')