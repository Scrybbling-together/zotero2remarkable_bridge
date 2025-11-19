from _typeshed import Incomplete
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

class LengthUnit(Enum):
    rmpts = "ReMarkable points"
    mupts = "PyMuPDF points"
    mm = "Millimeter"
    pt = "Typographic point"

@dataclass
class Dimensions:
    width: int
    height: int
    unit: LengthUnit
    @property
    def aspect_ratio_for_humans(self) -> Fraction: ...
    @property
    def aspect_ratio_for_calculations(self) -> float: ...

@dataclass()
class ReMarkableDimensions(Dimensions):
    unit: LengthUnit = ...
    def to_mm(self): ...

@dataclass
class PaperDimensions(Dimensions):
    unit: LengthUnit = ...
    def to_mu(self): ...

@dataclass
class TypographicDimensions(Dimensions):
    unit: LengthUnit = ...
    def to_mu(self): ...

@dataclass
class PyMuPDFDimensions(Dimensions):
    unit: LengthUnit = ...
    def to_mm(self): ...

a4_dimensions: Incomplete
REMARKABLE_PHYSICAL_SCREEN: Incomplete
REMARKABLE_DOCUMENT: Incomplete
mu_a4: Incomplete
REMARKABLE_PDF_EXPORT: Incomplete
