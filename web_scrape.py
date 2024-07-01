import requests
import json
from kafka import KafkaProducer


def fetch_race_data(season, round):
    
    url = f"https://ergast.com/api/f1/{season}/{round}/results.json"  # Ergast F1 API
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
def send_to_kafka(topic, data):
    
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.send(topic, data)
    producer.flush()

def main():
    
    seasons = [2024]  
    rounds = range(1, 22)
    for season in seasons:
        for round in rounds:
            data = fetch_race_data(season, round)
            if data:
                send_to_kafka('f1_race_data', data)
                print(f"Sent data for season {season}, round {round} to Kafka.")

if __name__ == "__main__":
    main()