from src.interfaces.web.bridge import OrchestratorBridge

bridge = OrchestratorBridge(grpc_host="localhost", grpc_port=50051)
bridge.connect()

devices = bridge.get_devices()
sensors = [d for d in devices if d.get('device_type') == 'sensor']
print(f"Total sensors: {len(sensors)}")

for s in sensors:
    reading = bridge.get_latest_reading(s['id'])
    print(f"Reading for {s['id']}: {reading}")
