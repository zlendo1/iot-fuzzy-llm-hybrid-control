FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt

COPY scripts/simulate_devices.py .

ENV MQTT_HOST=mosquitto
ENV MQTT_PORT=1883
ENV PYTHONUNBUFFERED=1

# Use shell form to allow environment variable expansion
CMD python simulate_devices.py --host "$MQTT_HOST" --port "$MQTT_PORT"
