from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import paho.mqtt.client as mqtt

from src.common.exceptions import MQTTError
from src.common.logging import get_logger

logger = get_logger(__name__)

MessageCallback = Callable[[str, bytes, int], None]


@dataclass
class MQTTClientConfig:
    host: str
    port: int = 1883
    keepalive: int = 60
    client_id: str | None = None
    clean_session: bool = True
    protocol_version: int = 5
    username: str | None = None
    password: str | None = None
    reconnect_enabled: bool = True
    reconnect_min_delay: float = 1.0
    reconnect_max_delay: float = 60.0
    lwt_topic: str | None = None
    lwt_payload: str = "offline"
    lwt_qos: int = 1
    lwt_retain: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MQTTClientConfig:
        broker = data.get("broker", {})
        client = data.get("client", {})
        auth = data.get("auth", {})
        reconnect = data.get("reconnect", {})
        lwt = data.get("lwt", {})

        return cls(
            host=broker.get("host", "localhost"),
            port=broker.get("port", 1883),
            keepalive=broker.get("keepalive", 60),
            client_id=client.get("id"),
            clean_session=client.get("clean_session", True),
            protocol_version=client.get("protocol_version", 5),
            username=auth.get("username"),
            password=auth.get("password"),
            reconnect_enabled=reconnect.get("enabled", True),
            reconnect_min_delay=reconnect.get("min_delay", 1.0),
            reconnect_max_delay=reconnect.get("max_delay", 60.0),
            lwt_topic=lwt.get("topic"),
            lwt_payload=lwt.get("payload", "offline"),
            lwt_qos=lwt.get("qos", 1),
            lwt_retain=lwt.get("retain", True),
        )


class MQTTClient:
    def __init__(self, config: MQTTClientConfig) -> None:
        self._config = config
        self._client: mqtt.Client | None = None
        self._connected = threading.Event()
        self._subscriptions: dict[str, tuple[MessageCallback, int]] = {}
        self._lock = threading.Lock()
        self._reconnect_delay = config.reconnect_min_delay
        self._shutdown = False

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    def connect(self, timeout: float = 10.0) -> None:
        if self._client is not None:
            raise MQTTError("Client already connected")

        protocol = self._get_protocol_version()
        callback_api_version = mqtt.CallbackAPIVersion.VERSION2

        self._client = mqtt.Client(
            callback_api_version=callback_api_version,
            client_id=self._config.client_id or "",
            protocol=protocol,
            clean_session=self._config.clean_session,
        )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        if self._config.username:
            self._client.username_pw_set(self._config.username, self._config.password)

        if self._config.lwt_topic:
            self._client.will_set(
                self._config.lwt_topic,
                self._config.lwt_payload,
                self._config.lwt_qos,
                self._config.lwt_retain,
            )

        try:
            self._client.connect(
                self._config.host,
                self._config.port,
                self._config.keepalive,
            )
            self._client.loop_start()
        except Exception as e:
            self._client = None
            raise MQTTError(f"Failed to connect to MQTT broker: {e}") from e

        if not self._connected.wait(timeout):
            self.disconnect()
            raise MQTTError(f"Connection timeout after {timeout}s")

        logger.info(
            "Connected to MQTT broker at %s:%d",
            self._config.host,
            self._config.port,
        )

    def disconnect(self) -> None:
        self._shutdown = True
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
            finally:
                self._client = None
                self._connected.clear()
                logger.info("Disconnected from MQTT broker")

    def subscribe(
        self,
        topic: str,
        callback: MessageCallback,
        qos: int = 1,
    ) -> None:
        if not self.is_connected:
            raise MQTTError("Not connected to MQTT broker")

        with self._lock:
            self._subscriptions[topic] = (callback, qos)

        result, mid = self._client.subscribe(topic, qos)  # type: ignore[union-attr]
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise MQTTError(f"Failed to subscribe to {topic}")

        logger.debug("Subscribed to topic: %s (qos=%d)", topic, qos)

    def unsubscribe(self, topic: str) -> None:
        if not self.is_connected:
            raise MQTTError("Not connected to MQTT broker")

        with self._lock:
            self._subscriptions.pop(topic, None)

        self._client.unsubscribe(topic)  # type: ignore[union-attr]
        logger.debug("Unsubscribed from topic: %s", topic)

    def publish(
        self,
        topic: str,
        payload: str | bytes,
        qos: int = 1,
        retain: bool = False,
    ) -> None:
        if not self.is_connected:
            raise MQTTError("Not connected to MQTT broker")

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        result = self._client.publish(topic, payload, qos, retain)  # type: ignore[union-attr]
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise MQTTError(f"Failed to publish to {topic}")

        logger.debug("Published to topic: %s", topic)

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _flags: dict[str, Any],
        reason_code: mqtt.ReasonCode,
        _properties: Any = None,
    ) -> None:
        if reason_code == 0 or reason_code.is_failure is False:
            self._connected.set()
            self._reconnect_delay = self._config.reconnect_min_delay
            self._resubscribe()
            logger.info("MQTT connection established")
        else:
            logger.error("MQTT connection failed: %s", reason_code)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        _properties: Any = None,
    ) -> None:
        self._connected.clear()

        if self._shutdown:
            return

        logger.warning("MQTT disconnected: %s", reason_code)

        if self._config.reconnect_enabled:
            self._schedule_reconnect()

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        topic = message.topic
        payload = message.payload
        qos = message.qos

        with self._lock:
            for pattern, (callback, _) in self._subscriptions.items():
                if self._topic_matches(pattern, topic):
                    try:
                        callback(topic, payload, qos)
                    except Exception:
                        logger.exception("Error in message callback for %s", topic)

    def _resubscribe(self) -> None:
        with self._lock:
            for topic, (_callback, qos) in self._subscriptions.items():
                try:
                    self._client.subscribe(topic, qos)  # type: ignore[union-attr]
                    logger.debug("Resubscribed to: %s", topic)
                except Exception:
                    logger.exception("Failed to resubscribe to %s", topic)

    def _schedule_reconnect(self) -> None:
        delay = self._reconnect_delay
        self._reconnect_delay = min(
            self._reconnect_delay * 2,
            self._config.reconnect_max_delay,
        )
        logger.info("Scheduling reconnect in %.1f seconds", delay)
        threading.Timer(delay, self._reconnect).start()

    def _reconnect(self) -> None:
        if self._shutdown or self.is_connected:
            return

        try:
            if self._client is not None:
                self._client.reconnect()
                logger.info("Reconnection attempt initiated")
        except Exception:
            logger.exception("Reconnection attempt failed")
            if self._config.reconnect_enabled and not self._shutdown:
                self._schedule_reconnect()

    def _get_protocol_version(self) -> mqtt.MQTTProtocolVersion:
        version_map: dict[int, mqtt.MQTTProtocolVersion] = {
            3: mqtt.MQTTv31,
            4: mqtt.MQTTv311,
            5: mqtt.MQTTv5,
        }
        return version_map.get(self._config.protocol_version, mqtt.MQTTv5)

    @staticmethod
    def _topic_matches(pattern: str, topic: str) -> bool:
        if pattern == topic:
            return True

        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")

        for i, part in enumerate(pattern_parts):
            if part == "#":
                return True
            if i >= len(topic_parts):
                return False
            if part != "+" and part != topic_parts[i]:
                return False

        return len(pattern_parts) == len(topic_parts)
