import pytest


@pytest.mark.unit
def test_exception_hierarchy() -> None:
    from src.common.exceptions import (
        ConfigurationError,
        DeviceError,
        IoTFuzzyLLMError,
        MQTTError,
        OllamaError,
        RuleError,
        ValidationError,
    )

    assert issubclass(IoTFuzzyLLMError, Exception)
    assert issubclass(ConfigurationError, IoTFuzzyLLMError)
    assert issubclass(ValidationError, IoTFuzzyLLMError)
    assert issubclass(DeviceError, IoTFuzzyLLMError)
    assert issubclass(MQTTError, DeviceError)
    assert issubclass(OllamaError, IoTFuzzyLLMError)
    assert issubclass(RuleError, IoTFuzzyLLMError)


@pytest.mark.unit
def test_exceptions_can_be_raised_with_message() -> None:
    from src.common.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="test message"):
        raise ConfigurationError("test message")
