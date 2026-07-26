"""
Custom Exceptions for Cloudkot
Standardized error handling across the application
"""


class CloudkotError(Exception):
    """Base exception for all Cloudkot errors"""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConfigurationError(CloudkotError):
    """Raised when there's a configuration problem"""

    def __init__(self, message: str, config_file: str | None = None):
        self.config_file = config_file
        if config_file:
            message = f"{message} (config: {config_file})"
        super().__init__(message, code="CONFIG_ERROR")


class ProviderError(CloudkotError):
    """Raised when there's a problem with an LLM provider"""

    def __init__(self, message: str, provider: str | None = None):
        self.provider = provider
        if provider:
            message = f"{message} (provider: {provider})"
        super().__init__(message, code="PROVIDER_ERROR")


class APIError(CloudkotError):
    """Raised when there's an API communication problem"""

    def __init__(self, message: str, status_code: int | None = None, provider: str | None = None):
        self.status_code = status_code
        self.provider = provider
        parts = [message]
        if status_code:
            parts.append(f"status: {status_code}")
        if provider:
            parts.append(f"provider: {provider}")
        super().__init__(" | ".join(parts), code="API_ERROR")


class PermissionError(CloudkotError):
    """Raised when a permission is denied"""

    def __init__(self, message: str, permission: str | None = None):
        self.permission = permission
        if permission:
            message = f"{message} (permission: {permission})"
        super().__init__(message, code="PERMISSION_ERROR")


class TokenLimitError(CloudkotError):
    """Raised when token limits are exceeded"""

    def __init__(self, message: str, current_tokens: int | None = None, max_tokens: int | None = None):
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens
        if current_tokens and max_tokens:
            message = f"{message} ({current_tokens}/{max_tokens} tokens)"
        super().__init__(message, code="TOKEN_LIMIT_ERROR")


class CloudkotValidationError(CloudkotError):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        if field:
            message = f"{message} (field: {field})"
        super().__init__(message, code="VALIDATION_ERROR")


class SkillError(CloudkotError):
    """Raised when there's a problem with a skill"""

    def __init__(self, message: str, skill_name: str | None = None):
        self.skill_name = skill_name
        if skill_name:
            message = f"{message} (skill: {skill_name})"
        super().__init__(message, code="SKILL_ERROR")


class ToolExecutionError(CloudkotError):
    """Raised when a tool execution fails"""

    def __init__(self, message: str, tool_name: str | None = None):
        self.tool_name = tool_name
        if tool_name:
            message = f"{message} (tool: {tool_name})"
        super().__init__(message, code="TOOL_ERROR")
