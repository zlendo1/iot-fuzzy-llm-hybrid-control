from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
def test_mqtt_client_config_from_dict() -> None:
    from src.device_interface.mqtt_client import MQTTClientConfig

    data = {
        "broker": {"host": "mqtt.example.com", "port": 8883, "keepalive": 120},
        "client": {"id": "test-client", "clean_session": False, "protocol_version": 4},
        "auth": {"username": "user", "password": "pass"},
        "reconnect": {"enabled": True, "min_delay": 2.0, "max_delay": 120.0},
        "lwt": {
            "topic": "status/test",
            "payload": "disconnected",
            "qos": 2,
            "retain": False,
        },
    }

    config = MQTTClientConfig.from_dict(data)

    assert config.host == "mqtt.example.com"
    assert config.port == 8883
    assert config.keepalive == 120
    assert config.client_id == "test-client"
    assert config.clean_session is False
    assert config.protocol_version == 4
    assert config.username == "user"
    assert config.password == "pass"
    assert config.reconnect_enabled is True
    assert config.reconnect_min_delay == 2.0
    assert config.reconnect_max_delay == 120.0
    assert config.lwt_topic == "status/test"
    assert config.lwt_payload == "disconnected"


@pytest.mark.unit
def test_mqtt_client_config_defaults() -> None:
    from src.device_interface.mqtt_client import MQTTClientConfig

    data = {"broker": {"host": "localhost"}}

    config = MQTTClientConfig.from_dict(data)

    assert config.host == "localhost"
    assert config.port == 1883
    assert config.keepalive == 60
    assert config.clean_session is True
    assert config.reconnect_enabled is True


@pytest.mark.unit
def test_mqtt_client_is_not_connected_initially() -> None:
    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config = MQTTClientConfig(host="localhost")
    client = MQTTClient(config)

    assert client.is_connected is False


@pytest.mark.unit
def test_mqtt_client_publish_raises_when_not_connected() -> None:
    from src.common.exceptions import MQTTError
    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config = MQTTClientConfig(host="localhost")
    client = MQTTClient(config)

    with pytest.raises(MQTTError, match="Not connected"):
        client.publish("test/topic", "payload")


@pytest.mark.unit
def test_mqtt_client_subscribe_raises_when_not_connected() -> None:
    from src.common.exceptions import MQTTError
    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config = MQTTClientConfig(host="localhost")
    client = MQTTClient(config)

    with pytest.raises(MQTTError, match="Not connected"):
        client.subscribe("test/topic", lambda _t, _p, _q: None)


@pytest.mark.unit
def test_topic_matches_exact() -> None:
    from src.device_interface.mqtt_client import MQTTClient

    assert MQTTClient._topic_matches("home/temp", "home/temp") is True
    assert MQTTClient._topic_matches("home/temp", "home/humidity") is False


@pytest.mark.unit
def test_topic_matches_single_wildcard() -> None:
    from src.device_interface.mqtt_client import MQTTClient

    assert MQTTClient._topic_matches("home/+/temp", "home/living/temp") is True
    assert MQTTClient._topic_matches("home/+/temp", "home/bedroom/temp") is True
    assert MQTTClient._topic_matches("home/+/temp", "home/living/humidity") is False


@pytest.mark.unit
def test_topic_matches_multi_wildcard() -> None:
    from src.device_interface.mqtt_client import MQTTClient

    assert MQTTClient._topic_matches("home/#", "home/living/temp") is True
    assert MQTTClient._topic_matches("home/#", "home/bedroom/humidity") is True
    assert MQTTClient._topic_matches("home/#", "office/temp") is False


@pytest.mark.unit
def test_mqtt_client_connect_raises_if_already_connected() -> None:
    from src.common.exceptions import MQTTError
    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config = MQTTClientConfig(host="localhost")
    client = MQTTClient(config)
    client._client = MagicMock()

    with pytest.raises(MQTTError, match="already connected"):
        client.connect()


@pytest.mark.unit
def test_mqtt_client_disconnect_clears_state() -> None:
    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config = MQTTClientConfig(host="localhost")
    client = MQTTClient(config)

    mock_paho = MagicMock()
    client._client = mock_paho
    client._connected.set()

    client.disconnect()

    assert client._client is None
    assert client.is_connected is False
    mock_paho.loop_stop.assert_called_once()
    mock_paho.disconnect.assert_called_once()


@pytest.mark.unit
def test_mqtt_client_get_protocol_version() -> None:
    import paho.mqtt.client as mqtt

    from src.device_interface.mqtt_client import MQTTClient, MQTTClientConfig

    config_v31 = MQTTClientConfig(host="localhost", protocol_version=3)
    client_v31 = MQTTClient(config_v31)
    assert client_v31._get_protocol_version() == mqtt.MQTTv31

    config_v311 = MQTTClientConfig(host="localhost", protocol_version=4)
    client_v311 = MQTTClient(config_v311)
    assert client_v311._get_protocol_version() == mqtt.MQTTv311

    config_v5 = MQTTClientConfig(host="localhost", protocol_version=5)
    client_v5 = MQTTClient(config_v5)
    assert client_v5._get_protocol_version() == mqtt.MQTTv5
