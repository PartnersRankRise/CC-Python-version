# Created: Thursday Jul 23, 2026, 11:38 AM (UTC-6)
# Last edited: Thursday Jul 23, 2026, 11:38 AM (UTC-6)

"""Custom exceptions for repository layer operations."""


class RepositoryException(Exception):
    """Base exception for repository operations."""
    pass


class ClientNotFoundError(RepositoryException):
    """Client not found in database."""
    pass


class RunNotFoundError(RepositoryException):
    """Run not found in database."""
    pass


class StageOutputNotFoundError(RepositoryException):
    """Stage output not found in database."""
    pass


class AuthorityModelNotFoundError(RepositoryException):
    """Authority model not found in database."""
    pass


class ReferenceFileNotFoundError(RepositoryException):
    """Reference file not found in database."""
    pass


class UnresolvedItemNotFoundError(RepositoryException):
    """Unresolved item not found in database."""
    pass
