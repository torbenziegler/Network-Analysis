import time
import speedtest
from influxdb import InfluxDBClient


def measure_speed():
    st = speedtest.Speedtest()
    st.download()
    st.upload()
    results = st.results.dict()
    return results['download'], results['upload'], results['ping']

def main():
    client = InfluxDBClient(host='localhost', port=8086)
    client.switch_database('network_monitor')

    while True:
        print("Measuring network performance...")
        download_speed, upload_speed, ping = measure_speed()
        data = [
            {
                "measurement": "network_performance",
                "fields": {
                    "download_speed": download_speed / 1_000_000,  # Convert to Mbps
                    "upload_speed": upload_speed / 1_000_000,      # Convert to Mbps
                    "ping": ping
                }
            }
        ]
        print(f"Download: {download_speed / 1_000_000:.2f} Mbps")
        print(f"Upload: {upload_speed / 1_000_000:.2f} Mbps")
        client.write_points(data)
        time.sleep(3600)  # Collect data every hour

if __name__ == '__main__':
    main()
