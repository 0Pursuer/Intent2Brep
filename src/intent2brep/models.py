from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BasePlate(StrictModel):
    kind: Literal["base_plate"] = "base_plate"
    length: float = Field(gt=0, description="X size in mm")
    width: float = Field(gt=0, description="Y size in mm")
    thickness: float = Field(gt=0, description="Z size in mm")


class WebPlate(StrictModel):
    kind: Literal["web_plate"] = "web_plate"
    width: float = Field(gt=0, description="X span in mm")
    thickness: float = Field(gt=0, description="Y thickness in mm")
    height: float = Field(gt=0, description="Height above base top in mm")
    x: float | None = Field(default=None, description="Web center X; None means solved")
    y: float | None = Field(default=None, description="Web center Y; None means solved")
    centered_on_base: bool = True


class Hole(StrictModel):
    kind: Literal["hole"] = "hole"
    diameter: float = Field(gt=0)
    target: Literal["base", "web"]
    through: bool = True
    depth: float | None = Field(default=None, gt=0)
    x: float | None = None
    y: float | None = None
    z: float | None = None
    centered_on_target: bool = True

    @model_validator(mode="after")
    def depth_consistency(self):
        if not self.through and self.depth is None:
            raise ValueError("blind hole requires depth")
        return self


class Slot(StrictModel):
    kind: Literal["slot"] = "slot"
    target: Literal["base"] = "base"
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    through: bool = True
    x: float | None = None
    y: float | None = None
    centered_on_target: bool = True


class Constraint(StrictModel):
    type: Literal[
        "centered", "symmetric", "perpendicular", "parallel", "concentric"
    ]
    a: str
    b: str
    strength: Literal["hard", "soft"] = "hard"


class PartIntent(StrictModel):
    units: Literal["mm"] = "mm"
    name: str = "generated_part"
    base: BasePlate
    web: WebPlate | None = None
    holes: list[Hole] = Field(default_factory=list)
    slots: list[Slot] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unsupported_requests: list[str] = Field(default_factory=list)
