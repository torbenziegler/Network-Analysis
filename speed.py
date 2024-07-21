"""
This script measures the network performance of the network and writes the data to InfluxDB.
"""

import time
import os
import speedtest
import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("INFLUXDB_TOKEN")
ORGANISATION = os.getenv("INFLUX_ORGANISATION")
URL = os.getenv("INFLUX_URL")
BUCKET = os.getenv("INFLUX_BUCKET")

MEASURE_INTERVAL = 10 # Seconds. Collect data every hour: 3600. Currently 10 seconds

def measure_speed():
    """
    Measure the download and upload speed of the network.
    Returns the download speed in bits per second, upload speed in bits per second and ping in milliseconds.
    """
    st = speedtest.Speedtest(secure=True)
    st.download()
    st.upload()
    results = st.results.dict()
    return results['download'], results['upload'], results['ping']

def main():
    """
    Measure the network performance and write the data to InfluxDB.
    """
    write_client = influxdb_client.InfluxDBClient(url=URL, token=TOKEN, org=ORGANISATION)
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    while True:
        try:
            print("Measuring network performance...")
            download_speed, upload_speed, ping = measure_speed()
            point = Point("network_performance").tag("host", "raspberrypi").field("download_speed", download_speed / 1_000_000).field("upload_speed", upload_speed / 1_000_000).field("ping", ping)
            print(f"Download: {download_speed / 1_000_000:.2f} Mbps")
            print(f"Upload: {upload_speed / 1_000_000:.2f} Mbps")
            write_api.write(bucket=BUCKET, org=ORGANISATION, record=point)
            print("Data written to InfluxDB")
            time.sleep(MEASURE_INTERVAL) 
        except Exception as e:
                print(f"Failed to write data to InfluxDB: {e}")

if __name__ == '__main__':
    main()
