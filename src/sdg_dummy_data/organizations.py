"""A made-up university structure (faculty > institute > division). Names are generic and fictional."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Unit:
    set_spec: str
    name: str


@dataclass(frozen=True)
class Division:
    faculty: Unit
    institute: Unit
    division: Unit

    @property
    def set_spec(self) -> str:
        """The OAI-PMH setSpec of a record in this division: faculty:institute:division."""
        return f"{self.faculty.set_spec}:{self.institute.set_spec}:{self.division.set_spec}"


# faculty -> institutes -> divisions, plus the SDGs this faculty mostly publishes on
_STRUCTURE = [
    (
        "Faculty of Natural Sciences",
        (6, 7, 13, 14, 15),
        {
            "Institute of Environmental Systems": ("Division of Hydrology", "Division of Ecology"),
            "Institute of Earth and Climate": ("Division of Climate Dynamics", "Division of Marine Science"),
        },
    ),
    (
        "Faculty of Medicine",
        (3, 2, 6),
        {
            "Institute of Public Health": ("Division of Epidemiology", "Division of Global Health"),
            "Institute of Clinical Research": ("Division of Infectious Diseases", "Division of Nutrition"),
        },
    ),
    (
        "Faculty of Social Sciences",
        (4, 5, 10, 16),
        {
            "Institute of Education": ("Division of Learning Sciences", "Division of Inclusive Education"),
            "Institute of Political Science": ("Division of Governance", "Division of Gender Studies"),
        },
    ),
    (
        "Faculty of Economics and Engineering",
        (1, 8, 9, 11, 12, 17),
        {
            "Institute of Development Economics": ("Division of Labour Economics", "Division of Public Finance"),
            "Institute of Sustainable Engineering": ("Division of Urban Systems", "Division of Circular Economy"),
        },
    ),
]


def _set_spec(*parts: int) -> str:
    """Globally unique codes like ZORA's: F01 (faculty), I0102 (institute), D010203 (division)."""
    prefix = "FID"[len(parts) - 1]
    return prefix + "".join(f"{p:02d}" for p in parts)


DIVISIONS: list[Division] = []
FACULTY_SDGS: dict[str, tuple[int, ...]] = {}

for f_index, (faculty_name, sdgs, institutes) in enumerate(_STRUCTURE, start=1):
    faculty = Unit(_set_spec(f_index), faculty_name)
    FACULTY_SDGS[faculty.set_spec] = sdgs
    for i_index, (institute_name, divisions) in enumerate(institutes.items(), start=1):
        institute = Unit(_set_spec(f_index, i_index), institute_name)
        for d_index, division_name in enumerate(divisions, start=1):
            DIVISIONS.append(Division(faculty, institute, Unit(_set_spec(f_index, i_index, d_index), division_name)))


def divisions_for_sdg(sdg_id: int) -> list[Division]:
    """Divisions of the faculties that publish on this SDG (falls back to all divisions)."""
    matching = [d for d in DIVISIONS if sdg_id in FACULTY_SDGS[d.faculty.set_spec]]
    return matching or DIVISIONS
