"""Load the bounded hypothesis family from YAML into typed objects.

The family is data (D-1), and this is the only place that data becomes code. Everything
downstream — the schema, the prompts, the measures — derives its allowed values from here, so
that there is exactly one definition of what the instrument can say.

That single-definition property is load-bearing rather than tidy. If the probe's schema and the
prompt's instructions could drift apart, the instrument would be able to return a value it was
never told about, and no test would catch it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

import yaml

# v2 is current. v1 is retained, hash-locked and unedited, so that readings taken under it stay
# comparable to each other. A reading taken under one family is NOT comparable to a reading taken
# under the other, and the family hash travels with every reading for exactly that reason.
FAMILY_V1_PATH = Path(__file__).resolve().parent / "family_v1.yaml"
FAMILY_V2_PATH = Path(__file__).resolve().parent / "family_v2.yaml"
FAMILY_PATH = FAMILY_V2_PATH


@dataclass(frozen=True)
class Value:
    """One allowed value on one dimension, with the gloss the prompt will quote."""
    id: str
    gloss: str


@dataclass(frozen=True)
class Dimension:
    name: str
    kind: str
    load_bearing: bool
    why_in_family: str
    values: tuple[Value, ...]


@dataclass(frozen=True)
class Family:
    version: int
    dimensions: dict[str, Dimension]
    may_not_claim: tuple[str, ...]
    trade_off_schema: dict[str, str]

    @property
    def purposes(self) -> tuple[str, ...]:
        return tuple(v.id for v in self.dimensions["purpose"].values)

    @property
    def audiences(self) -> tuple[str, ...]:
        return tuple(v.id for v in self.dimensions["audience"].values)

    @property
    def affects(self) -> tuple[str, ...]:
        """v3 only. Empty under v1 and v2, which have no affective dimension.

        One value set, two layers. `leaked_affect` and `emblematic_affect` share it by YAML
        anchor, so a value can never exist in one layer and not the other — the divergence
        between them is the measurement, and a divergence over mismatched supports is not one.
        """
        d = self.dimensions.get("leaked_affect")
        return tuple(v.id for v in d.values) if d else ()

    @property
    def depth_levels(self) -> tuple[int, ...]:
        return tuple(int(v.id) for v in self.dimensions["depth"].values)

    @property
    def cost_levels(self) -> tuple[int, ...]:
        return tuple(int(v.id) for v in self.dimensions["cost_borne"].values)

    @property
    def artifact_effort_levels(self) -> tuple[int, ...]:
        """v2 only. Empty under v1, which had no effort dimension."""
        d = self.dimensions.get("artifact_effort")
        return tuple(int(v.id) for v in d.values) if d else ()

    @property
    def demonstrated_work_levels(self) -> tuple[int, ...]:
        """v2 only. Empty under v1."""
        d = self.dimensions.get("demonstrated_work")
        return tuple(int(v.id) for v in d.values) if d else ()

    def gloss(self, dimension: str, value_id: str | int) -> str:
        for v in self.dimensions[dimension].values:
            if str(v.id) == str(value_id):
                return v.gloss
        raise KeyError(f"{value_id!r} is not a value of {dimension!r}")


def _parse_values(raw: dict) -> tuple[Value, ...]:
    """Read a dimension's allowed values.

    The family file spells this two ways on purpose: categorical dimensions list `values`,
    ordinal ones list `levels`. That distinction is meaningful in the data — a level has an
    order and a value does not — so the loader accommodates both rather than the family file
    being flattened to suit the loader.

    `trade_offs` is structured rather than enumerated and has neither.
    """
    entries = raw.get("values") or raw.get("levels") or []
    return tuple(Value(id=str(v["id"]), gloss=v["gloss"]) for v in entries)


@lru_cache(maxsize=4)
def load_family(path: str | Path = FAMILY_PATH) -> Family:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    dims = {
        name: Dimension(
            name=name,
            kind=d["kind"],
            load_bearing=bool(d["load_bearing"]),
            why_in_family=d["why_in_family"],
            values=_parse_values(d),
        )
        for name, d in raw["dimensions"].items()
    }
    return Family(
        version=int(raw["version"]),
        dimensions=dims,
        may_not_claim=tuple(raw["may_not_claim"]),
        trade_off_schema=raw["dimensions"]["trade_offs"]["schema"],
    )


def _enum(name: str, ids) -> type[Enum]:
    return Enum(name, {str(i).upper() if isinstance(i, str) else f"L{i}": i for i in ids})


def purpose_enum() -> type[Enum]:
    return _enum("Purpose", load_family().purposes)


def audience_enum() -> type[Enum]:
    return _enum("Audience", load_family().audiences)
