from typing import Dict, Any, Type
from yasinfeed.database.base import BaseDatabaseProvider, DatabaseConfigurationError
from yasinfeed.database.sqlite import SQLiteDatabaseProvider

# Map of provider names to concrete implementation classes
PROVIDERS: Dict[str, Type[BaseDatabaseProvider]] = {
    "sqlite": SQLiteDatabaseProvider
}


def create_db_provider(provider_name: str, config: Dict[str, Any]) -> BaseDatabaseProvider:
    """
    Factory function to instantiate the requested database provider.

    Args:
        provider_name: The name of the database provider (e.g., "sqlite").
        config: Configuration dictionary for the provider.

    Returns:
        An instance of BaseDatabaseProvider.

    Raises:
        DatabaseConfigurationError: If the provider is unsupported or validation fails.
    """
    name_lower = (provider_name or "").strip().lower()
    if name_lower not in PROVIDERS:
        raise DatabaseConfigurationError(
            f"Unsupported database provider: '{provider_name}'. Supported providers: {list(PROVIDERS.keys())}"
        )

    provider_cls = PROVIDERS[name_lower]
    return provider_cls(config)
