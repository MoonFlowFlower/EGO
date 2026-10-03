"""Standalone convention storage, validation, matching and annotation.

This package imports growthlab.state only; it has no dependency on fixtures,
scorers, prompts, model clients, or the U1 experiment scheduler.
"""
from .core import ConventionLibrary, normalize, trigger_matches

__all__ = ['ConventionLibrary', 'normalize', 'trigger_matches']
