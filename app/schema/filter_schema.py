"""
filter_schema.py
────────────────
Single source of truth for all filterable fields.
Update this file when new filters are added to the portal.
The system prompt is generated dynamically from this schema.
"""

from dataclasses import dataclass, field


@dataclass
class FilterKey:
    key: str                          # Exact key name used in the filter API
    filter_type: str                  # "filter" | "search" | "dateRange"
    aliases: list[str]                # Natural language phrases that map to this key
    valid_values: list[str]           # For enum fields. Empty = free-text / dynamic
    description: str                  # Used in prompt to help LLM understand context
    multi_value: bool = True          # Whether multiple values are allowed
    notes: str = ""                   # Any special behavior to mention in prompt


FILTER_SCHEMA: list[FilterKey] = [

    # ── Content Identity ──────────────────────────────────────────────────────
    FilterKey(
        key="TYPE",
        filter_type="filter",
        aliases=["content type", "type", "asset type"],
        valid_values=["EPISODE", "MOVIE", "SINGLEVOD", "MUSIC", "SHOW", "SEASON"],
        description="The type/category of the content asset",
    ),
    FilterKey(
        key="CONTENT_ID",
        filter_type="search",
        aliases=["content id", "id", "content identifier", "asset id"],
        valid_values=[],
        description="Unique identifier of the content asset",
    ),
    FilterKey(
        key="MAIN_TITLE",
        filter_type="search",
        aliases=["title", "name", "content name", "content title"],
        valid_values=[],
        description="Main title of the content asset",
    ),
    FilterKey(
        key="SHOW_TITLE",
        filter_type="search",
        aliases=["show name", "show title", "series name", "show"],
        valid_values=[],
        description="Title of the parent show. Works for SHOW, SEASON, EPISODE types",
        notes="Only applies to SHOW, SEASON, EPISODE content types",
    ),
    FilterKey(
        key="SEASON_TITLE",
        filter_type="search",
        aliases=["season name", "season title"],
        valid_values=[],
        description="Title of the parent season. Works for SEASON, EPISODE types",
        notes="Only applies to SEASON and EPISODE content types",
    ),
    FilterKey(
        key="SEASON_NO",
        filter_type="search",
        aliases=["season number", "season no", "season", "s1", "s2"],
        valid_values=[],
        description="Season number (numeric)",
        notes="Use numeric value only e.g. '1', '2', '3'",
    ),
    FilterKey(
        key="EPISODE_NO",
        filter_type="search",
        aliases=["episode number", "episode no", "episode"],
        valid_values=[],
        description="Episode number (numeric)",
        notes="Use numeric value only",
    ),

    # ── Status ────────────────────────────────────────────────────────────────
    FilterKey(
        key="ASSET_CURRENT_STATUS",
        filter_type="filter",
        aliases=["status", "current status", "asset status", "qc status", "state"],
        valid_values=[
            "Ready For QC",
            "QC in Progress",
            "QC Pass",
            "Temp QC Pass",
            "QC Fail",
            "Ready for Release",
            "Released",
            "Untrackable",
            "Revoked",
        ],
        description="Current workflow status of the content asset",
        notes="Casing must match exactly. 'Released' vs 'Ready for Release' are different statuses",
    ),
    FilterKey(
        key="DB_STATUS",
        filter_type="filter",
        aliases=["db status", "database status", "production status", "sync status"],
        valid_values=["STG", "PRD & STG", "Untrackable"],
        description="Whether content is in staging only or both production and staging",
    ),
    FilterKey(
        key="LIVE_ON_DEVICE",
        filter_type="filter",
        aliases=["live on device", "on device", "visible on device", "live"],
        valid_values=["Yes", "No", "Untrackable"],
        description="Whether the content is currently live and visible on device",
    ),

    # ── Provider / Partner ────────────────────────────────────────────────────
    FilterKey(
        key="VC_CP_NM",
        filter_type="filter",
        aliases=["provider", "partner", "content partner", "cp name", "ti name", "provider name"],
        valid_values=[],  # Injected at runtime from API
        description="Content partner / provider name. Use runtime provider list for valid values",
        notes="Values are injected dynamically from the provider list at runtime",
    ),
    FilterKey(
        key="CNTY_CD",
        filter_type="filter",
        aliases=["country", "country code", "region", "market"],
        valid_values=[],  # Injected at runtime from API
        description="Country/market code. Use runtime country list for valid values",
        notes="Values are injected dynamically from the country list at runtime",
    ),

    # ── License & Availability ────────────────────────────────────────────────
    FilterKey(
        key="LICENSE_STATUS",
        filter_type="filter",
        aliases=["license status", "availability", "license", "available"],
        valid_values=["UPCOMING", "ACTIVE", "EXPIRED"],
        description="Current license/availability status of the content",
    ),
    FilterKey(
        key="LICENSE_STATUS_RANGE",
        filter_type="dateRange",
        aliases=["license window", "available between", "license period", "availability range"],
        valid_values=[],
        description="Date range for license window (available_starting to exp_date)",
        notes="values[0]=start date, values[1]=end date. Use semantic tokens if relative",
    ),
    FilterKey(
        key="LICENSE_RANGE",
        filter_type="dateRange",
        aliases=["exact license dates", "exact availability dates"],
        valid_values=[],
        description="Exact available_starting and/or exp_date match",
        notes="values[0]=available_starting, values[1]=exp_date",
    ),
    FilterKey(
        key="ASSET_INGESTION_RANGE",
        filter_type="dateRange",
        aliases=["ingested between", "ingestion date", "added between", "registered between", "ingested last", "added last"],
        valid_values=[],
        description="Date range when content was ingested/registered into the system",
        notes="values[0]=start date, values[1]=end date. Use semantic tokens if relative",
    ),
    FilterKey(
        key="EVENT_RANGE",
        filter_type="dateRange",
        aliases=["event between", "event date", "event window"],
        valid_values=[],
        description="Date range for event_starting to event_ending",
        notes="values[0]=event_starting, values[1]=event_ending",
    ),

    # ── Content Metadata ──────────────────────────────────────────────────────
    FilterKey(
        key="GENRES",
        filter_type="filter",
        aliases=["genre", "genres", "category"],
        valid_values=[],
        description="Genre/category of the content. Partial match supported",
    ),
    FilterKey(
        key="AUDIO_LANG",
        filter_type="filter",
        aliases=["audio language", "audio lang", "language", "dubbed in"],
        valid_values=[],
        description="Audio language code of the content",
    ),
    FilterKey(
        key="SUBTITLE_LANG",
        filter_type="filter",
        aliases=["subtitle language", "subtitle lang", "subtitles", "subtitled in"],
        valid_values=[],
        description="Subtitle language code of the content",
    ),
    FilterKey(
        key="STARRING",
        filter_type="search",
        aliases=["starring", "actor", "actress", "cast", "director", "artist", "featuring"],
        valid_values=[],
        description="Search across cast (starring), artist, and director fields simultaneously",
        notes="This single key searches starring, artist, AND director columns together",
    ),
    FilterKey(
        key="SERIES_DESCR",
        filter_type="search",
        aliases=["series description", "show description", "synopsis"],
        valid_values=[],
        description="Description/synopsis of the series. Only applies to SHOW type",
    ),

    # ── Ingestion & Technical ─────────────────────────────────────────────────
    FilterKey(
        key="INGESTION_TYPE",
        filter_type="filter",
        aliases=["ingestion type", "feed type", "how ingested", "ingestion method"],
        valid_values=["CMS", "SMF QC", "SMF Non QC", "Untrackable"],
        description="How the content was ingested into the system",
    ),
    FilterKey(
        key="ONDEVICE_TRANS_YN",
        filter_type="filter",
        aliases=["on device transcoding", "transcoding", "device transcoding"],
        valid_values=["Yes", "No"],
        description="Whether on-device transcoding is enabled",
    ),
    FilterKey(
        key="CHAPTERS_YN",
        filter_type="filter",
        aliases=["has chapters", "chapters", "with chapters"],
        valid_values=["Yes", "No"],
        description="Whether the content has chapter markers",
    ),
    FilterKey(
        key="HISTORY",
        filter_type="filter",
        aliases=["qc history", "has qc history", "with history", "previously qc'd"],
        valid_values=["true"],
        description="Filter content that has QC history (previously went through QC)",
        notes="This is a flag filter — always use values=['true']. No other values needed",
    ),
    FilterKey(
        key="ATTRIBUTES",
        filter_type="filter",
        aliases=["attributes", "tags", "asset attributes"],
        valid_values=[],
        description="Custom attributes/tags on the content asset",
    ),
    FilterKey(
        key="EXTERNAL_PROGRAM_ID",
        filter_type="search",
        aliases=["external id", "external program id", "external identifier"],
        valid_values=[],
        description="External program ID from third-party providers",
    ),
    FilterKey(
        key="MATCH_INFORMATION",
        filter_type="search",
        aliases=["match", "teams", "team", "match info", "versus", "vs"],
        valid_values=[],
        description="Sports match team information (team1 vs team2)",
    ),
]

# ── Semantic date tokens resolved by date_resolver.py ─────────────────────────
SEMANTIC_DATE_TOKENS = [
    "TODAY",
    "YESTERDAY",
    "LAST_7_DAYS",
    "LAST_30_DAYS",
    "THIS_MONTH",
    "LAST_MONTH",
    "THIS_YEAR",
]

# ── Default columns returned for each content type ────────────────────────────
DEFAULT_COLUMNS: dict[str, list[str]] = {
    "EPISODE": [
        "CONTENT_ID", "MAIN_TITLE", "SHOW_TITLE", "SEASON_TITLE",
        "SEASON_NO", "EPISODE_NO", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "UPD_DT", "AVAILABLE_STARTING", "EXP_DATE",
    ],
    "MOVIE": [
        "CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "GENRES", "UPD_DT", "AVAILABLE_STARTING", "EXP_DATE",
    ],
    "SHOW": [
        "CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "UPD_DT",
    ],
    "SEASON": [
        "CONTENT_ID", "MAIN_TITLE", "SHOW_TITLE", "SEASON_NO",
        "ASSET_CURRENT_STATUS", "TYPE", "CNTY_CD", "VC_CP_NM", "UPD_DT",
    ],
    "SINGLEVOD": [
        "CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "UPD_DT", "AVAILABLE_STARTING",
    ],
    "MUSIC": [
        "CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "ARTIST", "UPD_DT",
    ],
    "DEFAULT": [
        "CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS", "TYPE",
        "CNTY_CD", "VC_CP_NM", "UPD_DT",
    ],
}


def get_schema_by_key(key: str) -> FilterKey | None:
    return next((f for f in FILTER_SCHEMA if f.key == key), None)


def get_enum_keys() -> list[FilterKey]:
    return [f for f in FILTER_SCHEMA if f.filter_type == "filter" and f.valid_values]


def get_all_valid_values(key: str) -> list[str]:
    schema = get_schema_by_key(key)
    return schema.valid_values if schema else []
