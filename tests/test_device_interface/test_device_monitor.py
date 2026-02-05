import pytest


@pytest.mark.unit
def test_device_status_enum_values() -> None:
    from src.device_interface.device_monitor import DeviceStatus

    assert DeviceStatus.ONLINE.value == "online"
    assert DeviceStatus.OFFLINE.value == "offline"
    assert DeviceStatus.UNKNOWN.value == "unknown"


@pytest.mark.unit
def test_device_monitor_register_device() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")

    assert monitor.get_status("sensor-001") == DeviceStatus.UNKNOWN


@pytest.mark.unit
def test_device_monitor_record_activity_marks_online() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.record_activity("sensor-001", "home/living/temp")

    assert monitor.get_status("sensor-001") == DeviceStatus.ONLINE


@pytest.mark.unit
def test_device_monitor_record_lwt_offline() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.record_activity("sensor-001")
    monitor.record_lwt("sensor-001", b"offline")

    assert monitor.get_status("sensor-001") == DeviceStatus.OFFLINE


@pytest.mark.unit
def test_device_monitor_record_lwt_online() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.record_lwt("sensor-001", b"online")

    assert monitor.get_status("sensor-001") == DeviceStatus.ONLINE


@pytest.mark.unit
def test_device_monitor_get_online_devices() -> None:
    from src.device_interface.device_monitor import DeviceMonitor

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.register_device("sensor-002")
    monitor.record_activity("sensor-001")

    online = monitor.get_online_devices()

    assert "sensor-001" in online
    assert "sensor-002" not in online


@pytest.mark.unit
def test_device_monitor_get_offline_devices() -> None:
    from src.device_interface.device_monitor import DeviceMonitor

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.record_activity("sensor-001")
    monitor.record_lwt("sensor-001", b"offline")

    offline = monitor.get_offline_devices()

    assert "sensor-001" in offline


@pytest.mark.unit
def test_device_monitor_status_callback_called_on_change() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    callback_calls: list[tuple[str, DeviceStatus, DeviceStatus]] = []

    def callback(
        device_id: str, old_status: DeviceStatus, new_status: DeviceStatus
    ) -> None:
        callback_calls.append((device_id, old_status, new_status))

    monitor.add_status_callback(callback)
    monitor.register_device("sensor-001")
    monitor.record_activity("sensor-001")

    assert len(callback_calls) == 1
    assert callback_calls[0][0] == "sensor-001"
    assert callback_calls[0][1] == DeviceStatus.UNKNOWN
    assert callback_calls[0][2] == DeviceStatus.ONLINE


@pytest.mark.unit
def test_device_monitor_get_state() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.record_activity("sensor-001", "home/temp")

    state = monitor.get_state("sensor-001")

    assert state is not None
    assert state.device_id == "sensor-001"
    assert state.status == DeviceStatus.ONLINE
    assert state.last_message_topic == "home/temp"


@pytest.mark.unit
def test_device_monitor_unregister_device() -> None:
    from src.device_interface.device_monitor import DeviceMonitor, DeviceStatus

    monitor = DeviceMonitor()
    monitor.register_device("sensor-001")
    monitor.unregister_device("sensor-001")

    assert monitor.get_status("sensor-001") == DeviceStatus.UNKNOWN
    assert monitor.get_state("sensor-001") is None
