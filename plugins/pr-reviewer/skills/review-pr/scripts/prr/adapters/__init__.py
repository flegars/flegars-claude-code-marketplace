from . import ado, github, gitlab
from .ado import AzureDevOpsAdapter
from .base import Adapter, AdapterError, PlatformUnavailable
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .local import LocalAdapter

ADAPTERS = {
    "github": GitHubAdapter,
    "ado": AzureDevOpsAdapter,
    "gitlab": GitLabAdapter,
    "local": LocalAdapter,
}

PARSERS = {
    "github": github,
    "ado": ado,
    "gitlab": gitlab,
}

EXPERIMENTAL = {"ado", "gitlab"}

__all__ = ["ADAPTERS", "PARSERS", "EXPERIMENTAL", "Adapter", "AdapterError", "PlatformUnavailable"]
