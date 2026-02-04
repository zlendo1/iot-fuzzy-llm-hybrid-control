class IoTFuzzyLLMError(Exception):
    pass


class ConfigurationError(IoTFuzzyLLMError):
    pass


class ValidationError(IoTFuzzyLLMError):
    pass


class DeviceError(IoTFuzzyLLMError):
    pass


class MQTTError(DeviceError):
    pass


class OllamaError(IoTFuzzyLLMError):
    pass


class RuleError(IoTFuzzyLLMError):
    pass
