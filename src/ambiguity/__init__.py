"""
ambiguity — deterministic prompt analysis for human-to-model translation.
"""

from .analyzer import Analysis
from .parser import parse, ParseResult
from .scoring import AmbiguityScore
from .profile import Profile, get_profile
from .advisory import advisory
from .hooks import AnthropicHook, OpenaiHook, HookConfig
from .bridges import as_udl_envelope, as_minimal_envelope
from .review import review, render_review_report
from .extensions import get_registry, BaseExtension, MaxWordCountExtension, ExtensionResult
from .technical import assess, TechnicalAssessment, render_technical_report, render_technical_json

__all__ = [
    "Analysis",
    "AmbiguityScore",
    "parse",
    "ParseResult",
    "Profile",
    "get_profile",
    "advisory",
    "AnthropicHook",
    "OpenaiHook",
    "HookConfig",
    "as_udl_envelope",
    "as_minimal_envelope",
    "review",
    "render_review_report",
    "get_registry",
    "BaseExtension",
    "MaxWordCountExtension",
    "ExtensionResult",
    "assess",
    "TechnicalAssessment",
    "render_technical_report",
    "render_technical_json",
]

__version__ = "0.1.0"
