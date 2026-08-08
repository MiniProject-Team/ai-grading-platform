class SmartHTRError(Exception):
    """Base error for expected SmartHTR failures."""


class ConfigurationError(SmartHTRError): pass
class DocumentLoadError(SmartHTRError): pass
class DetectionError(SmartHTRError): pass
class RecognitionError(SmartHTRError): pass
class ExportError(SmartHTRError): pass
