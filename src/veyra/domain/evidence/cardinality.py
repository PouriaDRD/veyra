"""Fact cardinality policy."""

from .enums import FactCardinality, FactKind

_MULTI_VALUE_FACT_KINDS = frozenset(
    {
        FactKind.EDUCATION,
        FactKind.INSTITUTION,
    }
)


def fact_cardinality_for(
    kind: FactKind,
) -> FactCardinality:
    """
    Return the resolution cardinality for one fact kind.

    Cardinality is domain policy. Most facts remain scalar. Education and
    institution represent collections of explicit affiliations/credentials and
    therefore may legitimately contain multiple simultaneously true values.
    """

    if kind in _MULTI_VALUE_FACT_KINDS:
        return FactCardinality.MULTIPLE

    return FactCardinality.SINGLE
