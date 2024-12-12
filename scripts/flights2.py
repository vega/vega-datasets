# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "polars",
# ]
# ///
from __future__ import annotations

import datetime as dt
import logging
import tomllib
import warnings
import zipfile
from collections import defaultdict, deque
from collections.abc import Sequence
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import IO, TYPE_CHECKING
from urllib import request

import polars as pl
from polars import col
from polars import selectors as cs

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Any, ClassVar, Literal, LiteralString


logger = logging.getLogger(__name__)


type Rows = Literal[
    1_000,
    2_000,
    5_000,
    10_000,
    20_000,
    100_000,
    200_000,
    500_000,
    1_000_000,
    3_000_000,
    5_000_000,
    10_000_000,
    100_000_000,
    500_000_000,
    1_000_000_000,
]
type Extension = Literal[".arrow", ".csv", ".json", ".parquet"]
type Columns = Literal[
    "date",
    "delay",
    "distance",
    "origin",
    "destination",
    "ScheduledFlightDate",
    "ScheduledFlightTime",
    "DepDelay",
    "time",
]
type YearMonthDay = tuple[int, int, int] | Sequence[int]
"""Arguments passed to ``datetime.date(...)``."""

type IntoDate = dt.date | dt.datetime | YearMonthDay
"""Anything that can be converted into a ``datetime.date``."""

type Dates = tuple[IntoDate, IntoDate] | Mapping[Literal["start", "end"], IntoDate]


type PlScanCsv = (
    str
    | Path
    | IO[str]
    | IO[bytes]
    | bytes
    | list[str]
    | list[Path]
    | list[IO[str]]
    | list[IO[bytes]]
    | list[bytes]
)


class DateTimeFormat(StrEnum):
    ISO = "iso"
    DECIMAL = "decimal"
    ACTUALLY_ISO = "ISO"


DTF_TO_FMT: Mapping[DateTimeFormat, LiteralString] = {
    DateTimeFormat.ISO: "%Y/%m/%d %H:%M",
    DateTimeFormat.ACTUALLY_ISO: "iso",
}

BASE_URL: LiteralString = "https://www.transtats.bts.gov/"
ROUTE_ZIP: LiteralString = f"{BASE_URL}PREZIP/"
REPORTING_PREFIX: LiteralString = (
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_"
)
ZIP: Literal[".zip"] = ".zip"
PATTERN_ZIP: LiteralString = f"*{REPORTING_PREFIX}*{ZIP}"

COLUMNS_DEFAULT: Sequence[Columns] = (
    "date",
    "delay",
    "distance",
    "origin",
    "destination",
)
"""Copied default from ``flights.py``."""

SCAN_SCHEMA: pl.Schema = pl.Schema({
    "FlightDate": pl.Date,
    "CRSDepTime": pl.String,
    "DepTime": pl.String,
    "DepDelay": pl.Float64,
    "ArrDelay": pl.Float64,
    "Distance": pl.Float64,
    "Origin": pl.String,
    "Dest": pl.String,
    "Cancelled": pl.Float64,
})


def _approx_latest(*, months_ago: int) -> dt.date:
    # Very loose, aiming for the last day of `today - months_ago`
    # In December, months_ago = 3 -> (2024, 8, 31)
    weeks_ago = dt.timedelta(weeks=months_ago * 4)
    current_month_start = dt.date.today().replace(day=1)
    return (current_month_start - weeks_ago).replace(day=1) - dt.timedelta(days=1)


def _into_date(obj: IntoDate, /) -> dt.date:
    """Normalize date input."""
    if isinstance(obj, dt.datetime):
        return obj.date()
    if isinstance(obj, dt.date):
        return obj
    if isinstance(obj, Sequence):
        match obj:
            case int(year), int(month), int(day):
                return dt.date(year, month, day)
            case int(year), int(month):
                return dt.date(year, month, 1)
            case (int(year),):
                return dt.date(year, 1, 1)
            case _:
                raise TypeError(type(obj))
    else:
        raise TypeError(type(obj))


class DateRange:
    """
    Matching a time period w/ required files.

    - Validates provided dates are in range of known data
    - Converts (start, end) to monthly file names

    Notes
    -----
    - Latest Available Data: August 2024 (in December 2024)
        - 2024-12-07 -> max 2024-08-31
    - https://www.transtats.bts.gov/releaseinfo.asp
    """

    _EARLIEST: ClassVar[dt.date] = dt.date(1987, 10, 1)
    _LATEST: ClassVar[dt.date] = _approx_latest(months_ago=3)

    def __init__(self, start: IntoDate, end: IntoDate, /) -> None:
        start = _into_date(start)
        end = _into_date(end)
        if start >= end:
            msg = (
                f"Unable to generate negative date range:\n"
                f"{start!r} - {end!r}\n\n"
                f"Try reversing `start`, `end`."
            )
            raise TypeError(msg)
        elif start < self._EARLIEST or end > self._LATEST:
            msg = (
                f"Unable to request data for date range:\n"
                f"{start!r} - {end!r}\n\n"
                f"Available data spans {self._EARLIEST!r} - {self._LATEST!r}."
            )
            raise TypeError(msg)
        self.start: pl.Expr = pl.lit(start)
        self.end: pl.Expr = pl.lit(end)

    @classmethod
    def from_dates(cls, dates: Dates, /) -> DateRange:
        match dates:
            case (start, end):
                return cls(start, end)
            case {"start": start, "end": end}:
                return cls(start, end)
            case _:
                raise TypeError(type(dates))

    @property
    def monthly(self) -> pl.Expr:
        return pl.date_range(self.start, self.end, interval="1mo").alias("date")

    @cached_property
    def file_names(self) -> Sequence[str]:
        """Returns the file names of all sources the input would require."""
        date = col("date")
        year, month = (date.dt.year().alias("year"), date.dt.month().alias("month"))
        # Slightly different when only handling a single range
        name_parts = pl.lit(REPORTING_PREFIX), year, pl.lit("_"), month, pl.lit(ZIP)
        return tuple(
            pl.select(self.monthly)
            .lazy()
            .select(pl.concat_str(*name_parts).sort_by(date))
            .collect()
            .to_series()
            .to_list()
        )

    def __eq__(self, other: Any, /) -> bool:
        """Two ``DateRange``s are equivalent if they would require the same files."""
        return isinstance(other, DateRange) and self.file_names == other.file_names

    def __hash__(self) -> int:
        return hash(self.file_names)


class Spec:
    """Describes a target output file, based on flights data."""

    def __init__(
        self,
        range: DateRange | Dates,
        n_rows: Rows,
        suffix: Extension,
        dt_format: DateTimeFormat | None = None,
        columns: Sequence[Columns] = COLUMNS_DEFAULT,
    ) -> None:
        if {"date", "time"}.isdisjoint(columns):
            msg = (
                f"Must specify one of {['date', 'time']!r} columns, "
                f"but got:\n{columns!r}"
            )
            raise TypeError(msg)
        self.range: DateRange = (
            range if isinstance(range, DateRange) else DateRange.from_dates(range)
        )
        self.n_rows: Rows = n_rows
        self.suffix: Extension = suffix
        self.dt_format: DateTimeFormat | None = dt_format
        self.columns: Sequence[Columns] = columns

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any], /) -> Spec:
        """From a toml table definition."""
        match mapping:
            case {"range": (start, end), **rest} if {"start", "end"}.isdisjoint(rest):
                range = start, end
            case {"start": start, "end": end, **rest} if {"range"}.isdisjoint(rest):
                range = start, end
            case _:
                msg = (
                    "Must provide start/end dates as either:\n"
                    "  - {'range': (..., ...)}\n"
                    "  - {'start': ..., 'end': ...}\n\n"
                    f"But got:\n{mapping!r}"
                )
                raise TypeError(msg)
        return cls(range, **rest)

    @property
    def name(self) -> str:
        """Encodes a short form of ``n_rows`` into the file name."""
        frac = self.n_rows // 1_000
        if frac >= 1_000_000:
            s = f"{frac // 1_000_000}b"
        elif frac >= 1_000:
            s = f"{frac // 1_000}m"
        elif frac >= 1:
            s = f"{frac}k"
        else:
            raise TypeError(self.n_rows)
        return f"flights-{s}{self.suffix}"

    @property
    def sort_by(self) -> str:
        return "time" if "time" in self.columns else "date"

    def transform(self, ldf: pl.LazyFrame, /) -> pl.DataFrame:
        if dt_format := self.dt_format:
            ldf = _transform_temporal(ldf, dt_format)
        ldf = ldf.select(self.columns)
        if n_rows := self.n_rows:
            return ldf.collect().sample(n_rows).sort(self.sort_by)
        return ldf.sort(self.sort_by).collect()

    def write(self, df: pl.DataFrame, output_dir: Path, /) -> None:
        fp: Path = output_dir / self.name
        fp.touch()
        msg = f"Writing {fp.as_posix()!r} ..."
        logger.info(msg)
        match self.suffix:
            case ".arrow":
                df.write_ipc(fp, compression="zstd")
            case ".csv":
                df.write_csv(
                    fp,
                    date_format=None,
                    datetime_format=None,
                    time_format=None,
                    null_value=None,
                )
            case ".json":
                df.write_json(fp)
            case ".parquet":
                df.write_parquet(fp, compression="zstd", compression_level=22)
            case _:
                fp.unlink()
                msg = f"Unexpected extension {self.suffix!r}"
                raise NotImplementedError(msg)


class SourceMap:
    """Handles resource sharing and reading."""

    def __init__(self, input_dir: Path, /) -> None:
        self.input_dir: Path = input_dir
        self._mapping = defaultdict[DateRange, deque[Spec]](deque)
        self._frames: dict[DateRange, pl.LazyFrame] = {}

    def add_dependency(self, spec: Spec, /) -> None:
        d_range: DateRange = spec.range
        if d_range not in self._mapping:
            self._frames[d_range] = self._extract(d_range).pipe(_clean_source)
        self._mapping[d_range].append(spec)

    def iter_tasks(self) -> Iterator[tuple[Spec, pl.LazyFrame]]:
        for d_range, frame in self._frames.items():
            for spec in self._mapping[d_range]:
                yield spec, frame

    def _extract(self, d_range: DateRange, /) -> pl.LazyFrame:
        """Combining zipped, monthly data into a single table."""
        some: list[bytes] = []
        for name in d_range.file_names:
            for fp in zipfile.Path(Path(self.input_dir / name)).glob("*.csv"):
                some.append(fp.read_bytes())
        return _scan_csv(some)

    def __len__(self) -> int:
        return len(self._frames)


class Flights:
    """
    Orchestrates flights dataset generation.

    Parameters
    ----------
    specs
        Target dataset definitions.
    input_dir
        Directory to store zip files.
    output_dir
        Directory to write realised specs to.

    Notes
    -----
    - Detecting & downloading dependencies
        - Sharing common data
    - Extracting & concatenating
    - Transforms to meet a given spec
    - Writing to target formats
    """

    def __init__(
        self,
        specs: Sequence[Spec],
        input_dir: str | Path,
        output_dir: str | Path,
    ) -> None:
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        self.specs: Sequence[Spec] = specs
        self.sources: SourceMap = SourceMap(self.input_dir)

    @classmethod
    def from_toml(
        cls,
        source: str | Path,
        /,
        input_dir: str | Path | None,
        output_dir: str | Path | None,
    ) -> Flights:
        """Construct from a toml file."""
        fp = Path(source)
        msg = f"Reading specs from {fp.as_posix()!r}"
        logger.info(msg)
        mapping = tomllib.loads(fp.read_text("utf-8"))
        if specs_array := mapping.get("specs"):
            return cls(
                specs=[Spec.from_dict(spec) for spec in specs_array],
                input_dir=input_dir or mapping["input_dir"],
                output_dir=output_dir or mapping["output_dir"],
            )
        msg = (
            f"Expected to find an array of tables keyed to `'specs'`, but got\n"
            f"{mapping!r}"
        )
        raise TypeError(msg)

    def __iter__(self) -> Iterator[Spec]:
        yield from self.specs

    @property
    def ranges(self) -> pl.LazyFrame:
        return pl.select(pl.concat(spec.range.monthly for spec in self)).lazy()

    @property
    def _required_names(self) -> set[str]:
        date = col("date")
        name_parts = pl.lit(REPORTING_PREFIX), "year", pl.lit("_"), "month", pl.lit(ZIP)
        return set(
            self.ranges.select(
                date.dt.year().alias("year"), date.dt.month().alias("month")
            )
            .unique()
            .select(pl.concat_str(*name_parts))
            .collect()
            .to_series()
            .to_list()
        )

    def _download_zip(self, name: str, /) -> Path:
        """Request a single month's data and write."""
        fp = self.input_dir / name
        msg = f"Requesting {name!r} ..."
        logger.debug(msg)
        with request.urlopen(f"{ROUTE_ZIP}{name}") as response:
            fp.touch()
            fp.write_bytes(response.read())
        msg = f"Downloaded {name!r}."
        logger.debug(msg)
        return fp

    def download_sources(self) -> None:
        """Detect and download any missing monthly flights data - which are required by specs."""
        logger.info("Detecting required sources ...")
        existing = {fp.name for fp in self.input_dir.glob(PATTERN_ZIP)}
        missing = self._required_names - existing
        if missing:
            msg_missing = f"Missing:\n  {'\n  '.join(sorted(missing))}"
            logger.info(msg_missing)
            if len(missing) >= 5:
                warnings.warn("Downloads may exceed 100MB", stacklevel=2)
            if len(missing) >= 11:
                warnings.warn(
                    "Total number of rows will exceed 5_000_000", stacklevel=2
                )
            for name in missing:
                self._download_zip(name)
            logger.info("Successfully downloaded all missing sources.")
        else:
            logger.info("Sources already downloaded.")

    def scan_sources(self) -> SourceMap:
        logger.info("Scanning dependencies ...")
        for spec in self:
            self.sources.add_dependency(spec)
        msg = f"Finished scanning {len(self.sources)!r} date ranges."
        logger.info(msg)
        return self.sources

    def run(self) -> None:
        logger.info("Starting job ...")
        self.download_sources()
        for spec, frame in self.scan_sources().iter_tasks():
            result = spec.transform(frame)
            spec.write(result, self.output_dir)
        logger.info("Finished job.")


def _scan_csv(source: PlScanCsv, /) -> pl.LazyFrame:
    # NOTE: files from `2001` have unused columns that break reading losslessly
    return pl.scan_csv(
        source,
        try_parse_dates=True,
        schema_overrides=SCAN_SCHEMA,
        encoding="utf8-lossy",
    ).select(SCAN_SCHEMA.names())


def _clean_source(ldf: pl.LazyFrame, /) -> pl.LazyFrame:
    """Parsing data types, dropping invalid data, dropping unused columns, fixing a datetime issue."""
    cancelled: pl.Expr = col("Cancelled")
    flight_date: pl.Expr = col("FlightDate")
    dep_time: pl.Expr = col("DepTime")
    # NOTE: Replace invalid midnight, convert to time
    wrap_times: pl.Expr = (
        cs.ends_with("DepTime").str.replace("2400", "0000").str.to_time("%H%M")
    )
    convert_types: Sequence[pl.Expr] = wrap_times, cs.float().cast(int)
    # NOTE: Filter cancelled flights and drop nulls/empty values first
    drop_rows = pl.any_horizontal(cancelled, dep_time == "", cs.float().is_null())  # noqa: PLC1901
    flight_date_corrected: pl.Expr = (
        pl.when(dep_time != pl.time(0, 0, 0, 0))
        .then(flight_date.dt.combine(dep_time))
        .otherwise(flight_date.dt.offset_by("1d").dt.combine(dep_time))
    )
    return (
        ldf.with_columns(cancelled.cast(bool))
        .filter(~drop_rows)
        .with_columns(*convert_types)
        .select(
            flight_date_corrected.alias("date"),
            col("ArrDelay").alias("delay"),
            col("Distance").alias("distance"),
            col("Origin").alias("origin"),
            col("Dest").alias("destination"),
            flight_date.alias("ScheduledFlightDate"),
            col("CRSDepTime").alias("ScheduledFlightTime"),
            "DepDelay",
        )
    )


def _transform_temporal(
    ldf: pl.LazyFrame, dt_format: DateTimeFormat, /
) -> pl.LazyFrame:
    """Either converting a datetime to a string format, or replacing with a decimal time."""
    date: pl.Expr = col("date")
    match dt_format:
        case DateTimeFormat.DECIMAL:
            return ldf.select(
                (date.dt.hour() + date.dt.minute() / 60).alias("time"), cs.exclude(date)
            )
        case DateTimeFormat.ISO | DateTimeFormat.ACTUALLY_ISO:
            return ldf.with_columns(date.dt.to_string(DTF_TO_FMT[dt_format]))
        case _:
            raise TypeError(dt_format)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    repo_root = Path(__file__).parent.parent
    source_toml = repo_root / "_data" / "flights.toml"
    temp_out = repo_root / "data" / "_flights"
    real_out = repo_root / "data"
    app = Flights.from_toml(
        source_toml,
        input_dir=Path.home() / ".vega_datasets",
        output_dir=real_out,
    )
    app.run()
