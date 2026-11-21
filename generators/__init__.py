from .base import BaseGenerator
from .fasteners import FastenerGenerator
from .brackets import BracketGenerator
from .housings import HousingGenerator
from .shafts import ShaftGenerator
from .connectors import ConnectorGenerator
from .plates import PlateGenerator

GENERATOR_REGISTRY = {
    "fasteners": FastenerGenerator,
    "brackets": BracketGenerator,
    "housings": HousingGenerator,
    "shafts": ShaftGenerator,
    "connectors": ConnectorGenerator,
    "plates": PlateGenerator,
}

CATEGORY_COUNTS = {
    "fasteners": 6000,
    "brackets": 4000,
    "housings": 4000,
    "shafts": 4000,
    "connectors": 3500,
    "plates": 3500,
}
