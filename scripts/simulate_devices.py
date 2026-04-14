"""IoT Smart Home Simulator.

Simulates all sensors defined in devices.json and reacts to commands
sent by the IoT Fuzzy-LLM system to actuators. Runs continuously,
publishing realistic sensor data via MQTT and subscribing to actuator
command topics to simulate device responses.

Usage:
    python scripts/simulate_devices.py --host localhost --port 21883
    python scripts/simulate_devices.py --interval 3
"""

import argparse
import json
import math
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion

    HAS_V2_API = True
except ImportError:
    try:
        import paho.mqtt.client as mqtt

        HAS_V2_API = False
    except ImportError:
        print("Error: paho-mqtt is required. Install with: pip install paho-mqtt")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# Actuator state models
# ─────────────────────────────────────────────────────────────


class ActuatorState:
    def __init__(self, device_id, on=False):
        self.device_id = device_id
        self.on = on

    def summary(self):
        return "ON" if self.on else "OFF"


class ThermostatState(ActuatorState):
    def __init__(self, device_id, on=False, target_temp=22.0, mode="auto"):
        super().__init__(device_id, on)
        self.target_temp = target_temp
        self.mode = mode

    def summary(self):
        return "%s target=%.1f°C mode=%s" % (
            "ON" if self.on else "OFF",
            self.target_temp,
            self.mode,
        )


class LightState(ActuatorState):
    def __init__(self, device_id, on=False, brightness=100):
        super().__init__(device_id, on)
        self.brightness = brightness

    def summary(self):
        return "%s brightness=%d%%" % ("ON" if self.on else "OFF", self.brightness)


class BlindsState(ActuatorState):
    def __init__(self, device_id, on=False, position=0):
        super().__init__(device_id, on)
        self.position = position

    def summary(self):
        state = "OPEN" if self.position > 50 else "CLOSED"
        return "%s position=%d%%" % (state, self.position)


# ─────────────────────────────────────────────────────────────
# Sensor simulation models
# ─────────────────────────────────────────────────────────────


class SensorSim:
    def __init__(
        self,
        sensor_id,
        topic,
        device_class,
        location,
        unit,
        value=0.0,
        min_val=-40.0,
        max_val=85.0,
    ):
        self.sensor_id = sensor_id
        self.topic = topic
        self.device_class = device_class
        self.location = location
        self.unit = unit
        self.value = value
        self.min_val = min_val
        self.max_val = max_val


class MotionSensorSim:
    def __init__(self, sensor_id, topic, location, value=False):
        self.sensor_id = sensor_id
        self.topic = topic
        self.location = location
        self.value = value
        self.cooldown = 0


# ─────────────────────────────────────────────────────────────
# Simulator
# ─────────────────────────────────────────────────────────────


class SmartHomeSimulator:
    """Continuously simulates sensors and responds to actuator commands."""

    def __init__(self, host, port, interval=5.0):
        self._host = host
        self._port = port
        self._interval = interval
        self._running = False
        self._tick = 0

        # MQTT client
        if HAS_V2_API:
            self._client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id="iot-simulator",
                protocol=mqtt.MQTTv5,
            )
        else:
            self._client = mqtt.Client(
                client_id="iot-simulator",
                protocol=mqtt.MQTTv311,
            )

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # ── Actuator states ──────────────────────────────────
        self._actuators = {
            "ac_living_room": ThermostatState("ac_living_room", target_temp=23.0),
            "heater_bedroom": ThermostatState("heater_bedroom", target_temp=21.0),
            "heater_office": ThermostatState("heater_office", target_temp=22.0),
            "light_living_room": LightState("light_living_room", brightness=80),
            "light_hallway": LightState("light_hallway"),
            "blinds_living_room": BlindsState("blinds_living_room", position=50),
            "blinds_bedroom": BlindsState("blinds_bedroom", position=0),
        }

        # command_topic -> actuator_id mapping
        self._command_topics = {
            "home/living_room/ac/set": "ac_living_room",
            "home/bedroom/heater/set": "heater_bedroom",
            "home/office/heater/set": "heater_office",
            "home/living_room/light/set": "light_living_room",
            "home/hallway/light/set": "light_hallway",
            "home/living_room/blinds/set": "blinds_living_room",
            "home/bedroom/blinds/set": "blinds_bedroom",
        }

        # ── Sensor states ────────────────────────────────────
        self._sensors = [
            SensorSim(
                "temp_living_room",
                "home/living_room/temperature",
                "temperature",
                "living_room",
                "°C",
                value=22.0,
            ),
            SensorSim(
                "humidity_living_room",
                "home/living_room/humidity",
                "humidity",
                "living_room",
                "%",
                value=55.0,
                min_val=0,
                max_val=100,
            ),
            SensorSim(
                "temp_bedroom",
                "home/bedroom/temperature",
                "temperature",
                "bedroom",
                "°C",
                value=20.0,
            ),
            SensorSim(
                "light_level_living_room",
                "home/living_room/light_level",
                "light_level",
                "living_room",
                "lux",
                value=300.0,
                min_val=0,
                max_val=100000,
            ),
            SensorSim(
                "temp_office",
                "home/office/temperature",
                "temperature",
                "office",
                "°C",
                value=21.0,
            ),
        ]

        self._motion_sensors = [
            MotionSensorSim("motion_hallway", "home/hallway/motion", "hallway"),
            MotionSensorSim(
                "motion_living_room", "home/living_room/motion", "living_room"
            ),
        ]

    # ── MQTT callbacks ───────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if hasattr(rc, "value"):
            rc_val = rc.value
        else:
            rc_val = int(rc)

        if rc_val == 0:
            self._log("INFO", "Connected to MQTT broker")
            for topic in self._command_topics:
                client.subscribe(topic, qos=1)
                self._log("INFO", "  Subscribed to %s" % topic)
        else:
            self._log("ERROR", "Connection failed with code %d" % rc_val)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        actuator_id = self._command_topics.get(topic)
        if not actuator_id:
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._log("WARN", "Invalid command payload on %s" % topic)
            return

        self._handle_command(actuator_id, payload)

    # ── Command handling ─────────────────────────────────────

    def _handle_command(self, actuator_id, payload):
        state = self._actuators.get(actuator_id)
        if not state:
            self._log("WARN", "Unknown actuator: %s" % actuator_id)
            return

        cmd_type = payload.get("command_type", "set")
        params = payload.get("parameters", {})

        self._log("CMD", "<< %s: type=%s params=%s" % (actuator_id, cmd_type, params))

        if cmd_type == "set":
            value = params.get("value")
            if isinstance(state, ThermostatState):
                if isinstance(value, (int, float)):
                    state.target_temp = float(value)
                    state.on = True
                mode = params.get("mode")
                if mode:
                    state.mode = str(mode)
            elif isinstance(state, LightState):
                if isinstance(value, (int, float)):
                    state.brightness = max(0, min(100, int(value)))
                    state.on = state.brightness > 0
                elif isinstance(value, bool):
                    state.on = value
            elif isinstance(state, BlindsState):
                if isinstance(value, (int, float)):
                    state.position = max(0, min(100, int(value)))
            else:
                if isinstance(value, bool):
                    state.on = value

        elif cmd_type == "toggle":
            state.on = not state.on

        elif cmd_type == "increase":
            if isinstance(state, ThermostatState):
                state.target_temp = min(30, state.target_temp + 1)
            elif isinstance(state, LightState):
                state.brightness = min(100, state.brightness + 10)
            elif isinstance(state, BlindsState):
                state.position = min(100, state.position + 10)

        elif cmd_type == "decrease":
            if isinstance(state, ThermostatState):
                state.target_temp = max(15, state.target_temp - 1)
            elif isinstance(state, LightState):
                state.brightness = max(0, state.brightness - 10)
            elif isinstance(state, BlindsState):
                state.position = max(0, state.position - 10)

        self._log("CMD", "  >> %s now: %s" % (actuator_id, state.summary()))

    # ── Sensor simulation ────────────────────────────────────

    def _update_sensors(self):
        t = self._tick * self._interval
        hour_of_day = (t / 3600) % 24

        for sensor in self._sensors:
            if sensor.device_class == "temperature":
                sensor.value = self._sim_temperature(sensor, t, hour_of_day)
            elif sensor.device_class == "humidity":
                sensor.value = self._sim_humidity(sensor, t, hour_of_day)
            elif sensor.device_class == "light_level":
                sensor.value = self._sim_light_level(sensor, t, hour_of_day)

            sensor.value = max(sensor.min_val, min(sensor.max_val, sensor.value))

        for motion in self._motion_sensors:
            if motion.cooldown > 0:
                motion.cooldown -= 1
                if motion.cooldown == 0:
                    motion.value = False
            else:
                if random.random() < 0.15:
                    motion.value = True
                    motion.cooldown = random.randint(2, 6)

    def _sim_temperature(self, sensor, t, hour):
        base = 20.0 + 3.0 * math.sin((hour - 6) * math.pi / 12)
        loc = sensor.location

        if loc == "living_room":
            ac = self._actuators.get("ac_living_room")
            if isinstance(ac, ThermostatState) and ac.on:
                diff = ac.target_temp - sensor.value
                base = sensor.value + diff * 0.05
            else:
                base = sensor.value + (base - sensor.value) * 0.02
        elif loc == "bedroom":
            heater = self._actuators.get("heater_bedroom")
            if isinstance(heater, ThermostatState) and heater.on:
                diff = heater.target_temp - sensor.value
                base = sensor.value + diff * 0.05
            else:
                base = sensor.value + (base - sensor.value) * 0.02
        elif loc == "office":
            heater = self._actuators.get("heater_office")
            if isinstance(heater, ThermostatState) and heater.on:
                diff = heater.target_temp - sensor.value
                base = sensor.value + diff * 0.05
            else:
                base = sensor.value + (base - sensor.value) * 0.02

        return base + random.gauss(0, 0.15)

    def _sim_humidity(self, sensor, t, hour):
        base = 60.0 - 15.0 * math.sin((hour - 6) * math.pi / 12)
        new_val = sensor.value + (base - sensor.value) * 0.03
        return new_val + random.gauss(0, 1.0)

    def _sim_light_level(self, sensor, t, hour):
        if 6 <= hour <= 20:
            daylight = 500 * math.sin((hour - 6) * math.pi / 14)
        else:
            daylight = 0

        blinds = self._actuators.get("blinds_living_room")
        if isinstance(blinds, BlindsState):
            daylight *= blinds.position / 100.0

        light = self._actuators.get("light_living_room")
        indoor = 0.0
        if isinstance(light, LightState) and light.on:
            indoor = light.brightness * 3.0

        base = daylight + indoor
        new_val = sensor.value + (base - sensor.value) * 0.1
        return max(0, new_val + random.gauss(0, 5.0))

    # ── Publishing ───────────────────────────────────────────

    def _publish_all(self):
        ts = datetime.now(timezone.utc).isoformat()

        for sensor in self._sensors:
            payload = {
                "value": round(sensor.value, 2),
                "unit": sensor.unit,
                "timestamp": ts,
            }
            self._client.publish(sensor.topic, json.dumps(payload), qos=1)

        for motion in self._motion_sensors:
            payload = {
                "value": motion.value,
                "timestamp": ts,
            }
            self._client.publish(motion.topic, json.dumps(payload), qos=1)

    def _print_dashboard(self):
        parts = []
        for s in self._sensors:
            if s.device_class == "temperature":
                parts.append("%s=%.1f°C" % (s.location[:3], s.value))
            elif s.device_class == "humidity":
                parts.append("hum=%.0f%%" % s.value)
            elif s.device_class == "light_level":
                parts.append("lux=%.0f" % s.value)

        motion_flags = []
        for m in self._motion_sensors:
            motion_flags.append("!" if m.value else ".")
        parts.append("motion=[%s]" % " ".join(motion_flags))

        act_parts = []
        for aid, state in self._actuators.items():
            short = aid.split("_")[0][:4]
            act_parts.append("%s:%s" % (short, state.summary()))

        self._log("DATA", " | ".join(parts) + "  --  " + " | ".join(act_parts))

    # ── Lifecycle ────────────────────────────────────────────

    def start(self):
        self._log(
            "INFO", "Connecting to MQTT broker at %s:%d" % (self._host, self._port)
        )
        self._log("INFO", "Publishing interval: %.1fs" % self._interval)
        self._log("INFO", "Press Ctrl+C to stop\n")

        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()
        self._running = True

        time.sleep(1.0)

        try:
            while self._running:
                self._update_sensors()
                self._publish_all()
                self._print_dashboard()
                self._tick += 1
                time.sleep(self._interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self._running = False
        self._client.loop_stop()
        self._client.disconnect()
        self._log("INFO", "Simulator stopped.")

    # ── Logging ──────────────────────────────────────────────

    @staticmethod
    def _log(level, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[36m",
            "CMD": "\033[33m",
            "DATA": "\033[32m",
            "WARN": "\033[31m",
            "ERROR": "\033[91m",
        }
        reset = "\033[0m"
        color = colors.get(level, "")
        print("%s[%s] [%4s]%s %s" % (color, ts, level, reset, msg))


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="IoT Smart Home Device Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect to Docker-mapped port on host
  python scripts/simulate_devices.py --host localhost --port 21883

  # Connect directly to Mosquitto container
  python scripts/simulate_devices.py --host mosquitto --port 1883

  # Faster publishing for demo
  python scripts/simulate_devices.py --interval 2
        """,
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MQTT_HOST", "localhost"),
        help="MQTT broker host (default: $MQTT_HOST or localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MQTT_PORT", "1883")),
        help="MQTT broker port (default: $MQTT_PORT or 1883)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between sensor updates (default: 5)",
    )

    args = parser.parse_args()

    sim = SmartHomeSimulator(
        host=args.host,
        port=args.port,
        interval=args.interval,
    )

    signal.signal(signal.SIGTERM, lambda *_: sim.stop())
    sim.start()


if __name__ == "__main__":
    main()
