import grpc
from src.interfaces.rpc.client import GrpcClient

client = GrpcClient(host="localhost", port=50051)
try:
    client.connect()
    devices = client.list_devices()
    print("Devices sample:")
    for i, d in enumerate(devices[:3]):
        print(f"{i}: {d}")
        
    sensors = [d for d in devices if d.get('device_type') == 'sensor']
    print(f"Sensors (device_type=sensor): {len(sensors)}")
    
    for s in sensors:
        reading = client.get_latest_reading(s['id'])
        print(f"Reading for {s['id']}: {reading}")
finally:
    client.disconnect()
