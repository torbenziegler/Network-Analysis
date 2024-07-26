"""
This script measures the network performance of the network and writes the data to InfluxDB.
"""

import time
import os
import socket
import speedtest
import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import psutil
from ping3 import ping

load_dotenv()

TOKEN = os.getenv("INFLUXDB_TOKEN")
ORGANISATION = os.getenv("INFLUX_ORGANISATION")
URL = os.getenv("INFLUX_URL")
BUCKET = os.getenv("INFLUX_BUCKET")
HOST_NAME = os.getenv("HOST_NAME")
MEASURE_INTERVAL = 5 # 3600 # Seconds. Collect data every hour

def measure_speed():
    """
    Measure the download and upload speed of the network.
    Returns the download speed in bits per second, upload speed in bits per second and ping in milliseconds.
    """
    st = speedtest.Speedtest(secure=True)
    st.download()
    st.upload()
    results = st.results.dict()
    download_speed = results['download']
    upload_speed = results['upload']
    speedtest_ping = results['ping']
    print(f"Download: {download_speed / 1_000_000:.2f} Mbps")
    print(f"Upload: {upload_speed / 1_000_000:.2f} Mbps")
    print(f"Ping: {speedtest_ping} ms")
    return download_speed, upload_speed, speedtest_ping

# Function to get the active network interface
def get_active_interface():
    for interface, addrs in psutil.net_if_addrs().items():
        if interface != 'lo':
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4
                    return interface
    return None

# Function to measure network interface stats
def measure_network_interface(interface):
    try:
        net_io = psutil.net_io_counters(pernic=True)[interface]
        print(f"Bytes sent: {net_io.bytes_sent}")
        print(f"Bytes received: {net_io.bytes_recv}")
        print(f"Errors in: {net_io.errin}")
        print(f"Errors out: {net_io.errout}")
        print(f"Packets dropped in: {net_io.dropin}")
        print(f"Packets dropped out: {net_io.dropout}")
        return net_io.bytes_sent, net_io.bytes_recv, net_io.errin, net_io.errout, net_io.dropin, net_io.dropout
    except KeyError:
        print(f"Interface {interface} not found.")
        return None, None, None, None, None, None

# Function to measure packet loss and jitter
def measure_ping(host='8.8.8.8'):
    results = []
    for _ in range(10):  # Ping multiple times to calculate jitter
        delay = ping(host, unit='ms')
        if delay is not None:
            results.append(delay)
        time.sleep(1)

    packet_loss = (10 - len(results)) / 10.0 * 100
    jitter = max(results) - min(results) if results else None
    avg_ping = sum(results) / len(results) if results else None

    print(f"Packet loss: {packet_loss:.2f}%")
    print(f"Jitter: {jitter:.2f} ms")
    print(f"Avg. Ping: {avg_ping} ms")

    return avg_ping, packet_loss, jitter

def write_data_to_influxdb(write_api, point):
    """
    Write the data to InfluxDB.
    """
    write_api.write(bucket=BUCKET, org=ORGANISATION, record=point)
    print("Data written to InfluxDB")

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
            # Measure ping, packet loss, and jitter
            print("Measuring ping, packet loss, and jitter...")
            avg_ping, packet_loss, jitter = measure_ping()

            active_interface = get_active_interface()
            if active_interface:
                print(f"Using interface: {active_interface}")
                # Measure network interface stats
                bytes_sent, bytes_recv, errin, errout, dropin, dropout = measure_network_interface(active_interface)
                
            else:
                print("No active network interface found.")
                bytes_sent, bytes_recv, errin, errout, dropin, dropout = None, None, None, None, None, None

            # Write data to InfluxDB
            point = Point("network_performance").tag("host", HOST_NAME).field("download_speed", download_speed / 1_000_000).field("upload_speed", upload_speed / 1_000_000).field("ping", ping).field("avg_ping", avg_ping).field("packet_loss", packet_loss).field("jitter", jitter).field("bytes_sent", bytes_sent).field("bytes_recv", bytes_recv).field("errin", errin).field("errout", errout).field("dropin", dropin).field("dropout", dropout)            
            write_data_to_influxdb(write_api, point)
            # Wait for the next measurement
            print(f"Waiting for {MEASURE_INTERVAL} seconds...")
            time.sleep(MEASURE_INTERVAL)
        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(MEASURE_INTERVAL)

if __name__ == '__main__':
    main()
