# producer/producer.py
import time
import json
import requests
from kafka import KafkaProducer

# Use a free sample API (no key required)
API_URL = "https://api.sampleapis.com/futurama/characters"
TOPIC = "live_news"
KAFKA_BOOTSTRAP = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    linger_ms=10
)

def fetch_api_data():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("API fetch error:", e)
        return []

def convert_item_to_text(item):
    # customize fields per API shape
    name = item.get("name", "")
    species = item.get("species", "")
    occupation = item.get("occupation", "")
    text = f"Name: {name}. Species: {species}. Occupation: {occupation}."
    return text

print(" Producer started. Fetching API and producing to Kafka...")

while True:
    items = fetch_api_data()
    if not items:
        print("No data fetched. Sleeping for 30s.")
        time.sleep(30)
        continue

    for item in items:
        text = convert_item_to_text(item)
        message = {"text": text}
        try:
            producer.send(TOPIC, value=message)
            print("Produced:", text)
        except Exception as e:
            print("Produce error:", e)

    producer.flush()
    print(" Waiting 30 seconds before next fetch...\n")
    time.sleep(30)
