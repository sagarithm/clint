"""
Clint: AI-Driven Enterprise Outreach Engine

A production-ready library and CLI for autonomous lead generation, enrichment, and multi-channel outreach.

Library Usage:
    >>> from clint import Engine
    >>> engine = Engine(api_key="your_openrouter_key")
    >>> result = engine.personalize({
    ...     "name": "Jane Doe",
    ...     "company": "TechCorp",
    ...     "title": "CTO"
    ... })
    >>> print(result["body"])

CLI Usage:
    $ clint run --query "Dentists in California"
    $ clint dashboard --host 127.0.0.1 --port 8000

For full documentation, see: https://github.com/sagarithm/clint
"""

from engine.engine import Engine

__version__ = "1.0.3"
__author__ = "Clint Contributors"
__all__ = ["Engine"]
