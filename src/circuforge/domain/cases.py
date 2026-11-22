"""Typed identifiers and numerical inputs for bounded local experiments."""
from pydantic import Field

from circuforge.domain.specs import DesignSpec, Model


class Case(Model):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,59}$")
    spec: DesignSpec
