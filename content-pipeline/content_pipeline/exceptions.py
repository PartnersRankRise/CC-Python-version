# Created: Thursday Jul 23, 2026, 11:48 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:48 AM (UTC-6)

"""Application-level exceptions."""


class ContentPipelineException(Exception):
    """Base exception for content pipeline."""
    pass


class MissingPrerequisiteError(ContentPipelineException):
    """Required predecessor stage output is missing."""
    pass


class StageBlockedError(ContentPipelineException):
    """Stage execution is blocked by pre-flight checks (e.g., Stage 7)."""
    pass


class InternalTokenLeakError(ContentPipelineException):
    """Internal control token found in output (e.g., <!--BRIEF:, ## Editorial Note)."""
    pass


class ClientNotFoundError(ContentPipelineException):
    """Client not found in database."""
    pass


class ClientAlreadyOnboardedError(ContentPipelineException):
    """Client is already fully onboarded."""
    pass


class RunNotFoundError(ContentPipelineException):
    """Run not found in database."""
    pass


class LLMProviderError(ContentPipelineException):
    """LLM provider operation failed."""
    pass


class MissingBrandColorError(ContentPipelineException):
    """Required brand color token is missing from client config."""
    pass


class ValidationError(ContentPipelineException):
    """Data validation failed."""
    pass


class OverlapDetectedError(ContentPipelineException):
    """Topic/keyword overlap detected with existing published content."""
    pass


class MissingReferenceFilesError(ContentPipelineException):
    """One or more required reference files are missing."""
    pass


class RunCreationFailedError(ContentPipelineException):
    """Run folder creation or database operation failed."""
    pass
