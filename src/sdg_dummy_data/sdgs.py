"""The 17 UN Sustainable Development Goals with research vocabulary used to write and score synthetic papers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SDG:
    id: int
    name: str
    color: str
    # Research topics a paper about this SDG could cover
    topics: tuple[str, ...]
    # Words that mark a sentence as related to this SDG (used for the synthetic explanations)
    keywords: tuple[str, ...]


SDGS: tuple[SDG, ...] = (
    SDG(
        1,
        "No Poverty",
        "#E5243B",
        (
            "microfinance access in rural households",
            "social protection floors",
            "multidimensional poverty measurement",
            "cash transfer programmes",
            "informal settlements and income volatility",
        ),
        ("poverty", "poor", "income", "households", "cash", "welfare", "deprivation", "vulnerable"),
    ),
    SDG(
        2,
        "Zero Hunger",
        "#DDA83A",
        (
            "drought-tolerant crop varieties",
            "child undernutrition",
            "smallholder farm productivity",
            "food security under price shocks",
            "soil health and yields",
        ),
        ("hunger", "food", "nutrition", "crop", "farm", "agriculture", "yield", "undernutrition"),
    ),
    SDG(
        3,
        "Good Health and Well-being",
        "#4C9F38",
        (
            "antimicrobial resistance in hospitals",
            "maternal mortality",
            "vaccination coverage",
            "mental health interventions",
            "cardiovascular risk factors",
        ),
        ("health", "patients", "clinical", "disease", "mortality", "treatment", "hospital", "medical"),
    ),
    SDG(
        4,
        "Quality Education",
        "#C5192D",
        (
            "early childhood learning outcomes",
            "teacher training",
            "digital classrooms",
            "school dropout prevention",
            "inclusive education for learners with disabilities",
        ),
        ("education", "school", "students", "learning", "teachers", "curriculum", "literacy", "pupils"),
    ),
    SDG(
        5,
        "Gender Equality",
        "#FF3A21",
        (
            "gender pay gaps",
            "women's political participation",
            "gender-based violence prevention",
            "unpaid care work",
            "female entrepreneurship",
        ),
        ("gender", "women", "female", "girls", "equality", "violence", "empowerment", "discrimination"),
    ),
    SDG(
        6,
        "Clean Water and Sanitation",
        "#26BDE2",
        (
            "groundwater contamination",
            "urban wastewater treatment",
            "access to safe drinking water",
            "hygiene behaviour in schools",
            "water scarcity in river basins",
        ),
        ("water", "sanitation", "wastewater", "drinking", "hygiene", "groundwater", "contamination", "river"),
    ),
    SDG(
        7,
        "Affordable and Clean Energy",
        "#FCC30B",
        (
            "solar microgrids",
            "energy poverty",
            "battery storage for renewables",
            "building energy efficiency",
            "wind power integration",
        ),
        ("energy", "solar", "renewable", "electricity", "wind", "battery", "power", "efficiency"),
    ),
    SDG(
        8,
        "Decent Work and Economic Growth",
        "#A21942",
        (
            "youth unemployment",
            "labour rights in supply chains",
            "productivity of small firms",
            "platform work",
            "tourism and local employment",
        ),
        ("employment", "labour", "workers", "economic", "growth", "wages", "jobs", "productivity"),
    ),
    SDG(
        9,
        "Industry, Innovation and Infrastructure",
        "#FD6925",
        (
            "broadband infrastructure",
            "industrial innovation clusters",
            "resilient transport networks",
            "research and development spending",
            "additive manufacturing",
        ),
        (
            "infrastructure",
            "innovation",
            "industry",
            "industrial",
            "technology",
            "manufacturing",
            "research",
            "network",
        ),
    ),
    SDG(
        10,
        "Reduced Inequalities",
        "#DD1367",
        (
            "migrant remittances",
            "income inequality across regions",
            "social inclusion of minorities",
            "progressive taxation",
            "discrimination in hiring",
        ),
        (
            "inequality",
            "inequalities",
            "migrants",
            "inclusion",
            "minorities",
            "disparities",
            "redistribution",
            "marginalised",
        ),
    ),
    SDG(
        11,
        "Sustainable Cities and Communities",
        "#FD9D24",
        (
            "affordable urban housing",
            "public transport accessibility",
            "urban heat islands",
            "disaster resilience of cities",
            "green public spaces",
        ),
        ("urban", "cities", "city", "housing", "transport", "neighbourhoods", "municipal", "communities"),
    ),
    SDG(
        12,
        "Responsible Consumption and Production",
        "#BF8B2E",
        (
            "food waste in retail",
            "circular economy business models",
            "plastic recycling",
            "corporate sustainability reporting",
            "life cycle assessment of products",
        ),
        ("waste", "recycling", "consumption", "circular", "production", "packaging", "reuse", "lifecycle"),
    ),
    SDG(
        13,
        "Climate Action",
        "#3F7E44",
        (
            "climate adaptation planning",
            "carbon pricing",
            "extreme weather attribution",
            "greenhouse gas emissions of agriculture",
            "climate risk communication",
        ),
        ("climate", "emissions", "carbon", "warming", "adaptation", "greenhouse", "mitigation", "weather"),
    ),
    SDG(
        14,
        "Life Below Water",
        "#0A97D9",
        (
            "coral reef bleaching",
            "sustainable fisheries management",
            "ocean acidification",
            "marine plastic pollution",
            "marine protected areas",
        ),
        ("marine", "ocean", "fish", "fisheries", "coral", "coastal", "sea", "reef"),
    ),
    SDG(
        15,
        "Life on Land",
        "#56C02B",
        (
            "deforestation monitoring",
            "pollinator decline",
            "invasive species",
            "alpine ecosystem change",
            "habitat fragmentation",
        ),
        ("forest", "biodiversity", "species", "ecosystems", "habitat", "land", "wildlife", "deforestation"),
    ),
    SDG(
        16,
        "Peace, Justice and Strong Institutions",
        "#00689D",
        (
            "corruption in public procurement",
            "access to justice",
            "post-conflict reconciliation",
            "trust in institutions",
            "violence reduction policies",
        ),
        ("justice", "institutions", "corruption", "violence", "conflict", "governance", "courts", "peace"),
    ),
    SDG(
        17,
        "Partnerships for the Goals",
        "#19486A",
        (
            "development aid effectiveness",
            "international research partnerships",
            "debt sustainability",
            "technology transfer",
            "SDG data and monitoring",
        ),
        ("partnerships", "cooperation", "international", "aid", "development", "collaboration", "monitoring", "global"),
    ),
)

SDG_BY_ID = {sdg.id: sdg for sdg in SDGS}
