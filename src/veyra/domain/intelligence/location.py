"""Location intelligence domain values and lexicon."""

from dataclasses import dataclass
from enum import StrEnum


class LocationEntityKind(StrEnum):
    """Supported normalized geographic entity kinds."""

    COUNTRY = "country"
    CITY = "city"


@dataclass(frozen=True, slots=True)
class LocationEntity:
    """
    One normalized geographic entity.

    ``value`` is Veyra's stable normalized identifier.

    ``display_name`` is a human-readable canonical name.

    ``aliases`` contains multilingual textual forms that may appear in public
    profile data.
    """

    kind: LocationEntityKind

    value: str
    display_name: str

    aliases: tuple[str, ...]

    country_code: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize geographic entity metadata."""

        value = self.value.strip().casefold()
        display_name = self.display_name.strip()

        aliases = tuple(alias.strip() for alias in self.aliases if alias.strip())

        if not value:
            raise ValueError(
                "location value must not be empty.",
            )

        if not display_name:
            raise ValueError(
                "location display_name must not be empty.",
            )

        if not aliases:
            raise ValueError(
                "location aliases must not be empty.",
            )

        if len({alias.casefold() for alias in aliases}) != len(aliases):
            raise ValueError(
                "location aliases must be unique.",
            )

        country_code = self.country_code

        if country_code is not None:
            country_code = country_code.strip().upper()

            if len(country_code) != 2:
                raise ValueError(
                    "country_code must be a two-letter code.",
                )

        object.__setattr__(
            self,
            "value",
            value,
        )

        object.__setattr__(
            self,
            "display_name",
            display_name,
        )

        object.__setattr__(
            self,
            "aliases",
            aliases,
        )

        object.__setattr__(
            self,
            "country_code",
            country_code,
        )


@dataclass(frozen=True, slots=True)
class LocationLexicon:
    """
    Immutable multilingual location lexicon.

    This is intentionally separate from extraction/inference logic so Veyra
    can replace the built-in catalog with a larger database-backed or
    provider-backed geographic catalog later.
    """

    entries: tuple[
        LocationEntity,
        ...,
    ]

    def __post_init__(self) -> None:
        """Validate lexicon uniqueness."""

        if not self.entries:
            raise ValueError(
                "location lexicon must not be empty.",
            )

        keys = tuple(
            (
                entry.kind,
                entry.value,
            )
            for entry in self.entries
        )

        if len(
            set(
                keys,
            )
        ) != len(keys):
            raise ValueError(
                "location lexicon contains duplicate entities.",
            )

    def by_kind(
        self,
        kind: LocationEntityKind,
    ) -> tuple[LocationEntity, ...]:
        """Return all entities of one geographic kind."""

        return tuple(entry for entry in self.entries if entry.kind is kind)

    def find(
        self,
        *,
        kind: LocationEntityKind,
        value: str,
    ) -> LocationEntity | None:
        """Find one normalized entity."""

        normalized = value.strip().casefold()

        for entry in self.entries:
            if entry.kind is kind and entry.value == normalized:
                return entry

        return None


DEFAULT_LOCATION_LEXICON = LocationLexicon(
    entries=(
        LocationEntity(
            kind=LocationEntityKind.COUNTRY,
            value="iran",
            display_name="Iran",
            aliases=(
                "iran",
                "ایران",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="tehran",
            display_name="Tehran",
            aliases=(
                "tehran",
                "تهران",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="karaj",
            display_name="Karaj",
            aliases=(
                "karaj",
                "کرج",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="shiraz",
            display_name="Shiraz",
            aliases=(
                "shiraz",
                "شیراز",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="mashhad",
            display_name="Mashhad",
            aliases=(
                "mashhad",
                "مشهد",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="isfahan",
            display_name="Isfahan",
            aliases=(
                "isfahan",
                "esfahan",
                "اصفهان",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="tabriz",
            display_name="Tabriz",
            aliases=(
                "tabriz",
                "تبریز",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="qom",
            display_name="Qom",
            aliases=(
                "qom",
                "قم",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="ahvaz",
            display_name="Ahvaz",
            aliases=(
                "ahvaz",
                "اهواز",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="rasht",
            display_name="Rasht",
            aliases=(
                "rasht",
                "رشت",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="kerman",
            display_name="Kerman",
            aliases=(
                "kerman",
                "کرمان",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="yazd",
            display_name="Yazd",
            aliases=(
                "yazd",
                "یزد",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="urmia",
            display_name="Urmia",
            aliases=(
                "urmia",
                "orumiyeh",
                "ارومیه",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="bandar_abbas",
            display_name="Bandar Abbas",
            aliases=(
                "bandar abbas",
                "بندرعباس",
                "بندر عباس",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="arak",
            display_name="Arak",
            aliases=(
                "arak",
                "اراک",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="hamedan",
            display_name="Hamedan",
            aliases=(
                "hamedan",
                "hamadan",
                "همدان",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="qazvin",
            display_name="Qazvin",
            aliases=(
                "qazvin",
                "ghazvin",
                "قزوین",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="sari",
            display_name="Sari",
            aliases=(
                "sari",
                "ساری",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="gorgan",
            display_name="Gorgan",
            aliases=(
                "gorgan",
                "گرگان",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="sanandaj",
            display_name="Sanandaj",
            aliases=(
                "sanandaj",
                "سنندج",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="kermanshah",
            display_name="Kermanshah",
            aliases=(
                "kermanshah",
                "کرمانشاه",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="bushehr",
            display_name="Bushehr",
            aliases=(
                "bushehr",
                "بوشهر",
            ),
            country_code="IR",
        ),
        LocationEntity(
            kind=LocationEntityKind.CITY,
            value="zanjan",
            display_name="Zanjan",
            aliases=(
                "zanjan",
                "زنجان",
            ),
            country_code="IR",
        ),
    )
)
