# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "niquests",
#     "polars",
# ]
# ///
"""
Retrieve, extract, transform, and export  `BTS`_ (U.S.) `On-Time Flight Performance`_-derived datasets.

See Also
--------
``Flights``
``Spec``
``DateTimeFormat``

.. _BTS:
    https://www.transtats.bts.gov/Homepage.asp
.. _On-Time Flight Performance:
    https://www.transtats.bts.gov/TableInfo.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr&V0s1_b0yB=D
"""

from __future__ import annotations

# ruff: noqa: PLC1901
import asyncio
import datetime as dt
import io
import logging
import tomllib
import zipfile
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal
from typing import get_args as _typing_get_args

import niquests
import polars as pl
from polars import col
from polars import selectors as cs

if TYPE_CHECKING:
    import sys
    from collections.abc import Iterator
    from typing import Any, ClassVar, LiteralString

    if sys.version_info >= (3, 13):
        from typing import TypeIs
    else:
        from typing_extensions import TypeIs


logger = logging.getLogger(__name__)


type Extension = Literal[".arrow", ".csv", ".json", ".parquet"]
"""File extension/output format."""


def is_extension(obj: Any) -> TypeIs[Extension]:
    return obj in _get_args(Extension)


type WriteOptions = Mapping[str, Any]


def is_write_options(obj: Any) -> TypeIs[WriteOptions]:
    return isinstance(obj, Mapping) and (
        len(obj) == 0 or all(isinstance(k, str) for k in obj)
    )


type Column = Literal[
    "date",
    "time",
    "delay",
    "distance",
    "origin",
    "destination",
    "ScheduledFlightDate",
    "ScheduledFlightTime",
    "DepDelay",
]
"""
Columns available for ``flights`` datasets.

Descriptions
------------
*date*
    Either a **datetime-typed** value, or a formatted datetime string
*time*
    Either a **time-typed** value, or decimal hours.minutes when using decimal format (e.g., 6.5 for 6:30)
*distance*
    Flight distance in miles (integer)
*delay*
    Arrival delay in minutes (integer)
*origin*
    Origin airport code
*destination*
    Destination airport code
*ScheduledFlightDate*
    Original scheduled flight date (YYYY-MM-DD)
*ScheduledFlightTime*
    Original scheduled departure time (HHMM)
*DepDelay*
    Departure delay in minutes (integer)

See Also
--------
- https://www.bts.gov/topics/airlines-and-airports/world-airport-codes
- https://www.transtats.bts.gov/TableInfo.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr&V0s1_b0yB=D
"""


def is_columns(obj: Any) -> TypeIs[Sequence[Column]]:
    return obj is COLUMNS_DEFAULT or (
        isinstance(obj, Sequence) and set(_get_args(Column)).issuperset(obj)
    )


type YearMonthDay = tuple[int, int, int] | Sequence[int]
"""Arguments passed to ``datetime.date(...)``."""

type IntoDate = dt.date | dt.datetime | YearMonthDay
"""Anything that can be converted into a ``datetime.date``."""

type IntoDateRange = (
    tuple[IntoDate, IntoDate] | Mapping[Literal["start", "end"], IntoDate]
)
"""Anything that can be converted into a ``DateRange``."""

THOUSAND: Literal[1_000] = 1_000
MILLION: Literal[1_000_000] = 1_000_000
BILLION: Literal[1_000_000_000] = 1_000_000_000


def is_rows(obj: Any) -> TypeIs[Rows]:
    match obj:
        case int(n) if 1 <= n < THOUSAND:
            return True
        case int(n) if THOUSAND <= n < MILLION:
            return n % THOUSAND == 0
        case int(n) if MILLION <= n < BILLION:
            return n % MILLION == 0
        case int(n) if BILLION <= n < BILLION * THOUSAND:
            return n % BILLION == 0
        case _:
            return False


type Rows = Annotated[int, is_rows]
"""
Number of rows to include in the output.

Constraints
-----------
- Positive integer
- Either
    - 1 <= n_rows < 1_000
    - Representable as thousands, millions, or billions **without** a remainder

Examples
--------
Ok:

    30
    123
    1_000
    20_000
    55_000_000
    999_000_000_000

Not ok:

    -30               # Negative
    1_230             # Remainder: 230
    1_001             # Remainder: 1
    20_502            # Remainder: 502
    55_555_000        # Remainder: 555_000
    1_000_000_000_000 # Trillions

---
"""


def is_chrono_str(s: Any) -> TypeIs[_ChronoFormat]:
    return s == "%Y/%m/%d %H:%M" or (isinstance(s, str) and s.startswith("%"))


def is_datetime_format(s: Any) -> TypeIs[DateTimeFormat]:
    return s in {"iso", "iso:strict", "decimal"} or is_chrono_str(s) or s is None


type _ChronoFormat = Literal["%Y/%m/%d %H:%M"] | Annotated[LiteralString, is_chrono_str]
"""https://docs.rs/chrono/latest/chrono/format/strftime/index.html"""

type DateTimeFormat = Literal["iso", "iso:strict", "decimal"] | _ChronoFormat | None
"""
Anything that is resolvable to a date/time column transform.

Notes
-----
When not provided:
- {``.arrow``, ``.parquet``} preserve temporal data types on write
- ``.json`` defaults to **"iso"**
- ``.csv`` defaults to **"iso:strict"**

Examples
--------
Each example will use the same input datetime:

    from datetime import datetime
    datetime(2020, 3, 1, 6, 30, 0)

**"iso"**, **"iso:strict"**: variants of `ISO 8601`_ used in `pl.Expr.dt.to_string`_:

    "2020-03-01 06:30:00.000000"
    "2020-03-01T06:30:00.000000"

**"decimal"**: represents **time only** with fractional minutes::

    6.5 # stored as a float

A format string using `chrono`_ specifiers:

    "%Y/%m/%d %H:%M" -> "2020/03/01 06:30"
    "%s"             -> "1583044200"               # UNIX timestamp
    "%c"             -> "Sun Mar  1 06:30:00 2020"
    "%T"             -> "06:30:00"
    "%Y-%B-%d"       -> "2020-March-01"
    "%e-%b-%Y"       -> " 1-Mar-2020"

.. _ISO 8601:
    https://en.wikipedia.org/wiki/ISO_8601
.. _pl.Expr.dt.to_string:
    https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.dt.to_string.html
.. _chrono:
    https://docs.rs/chrono/latest/chrono/format/strftime/index.html
"""


BASE_URL: LiteralString = "https://www.transtats.bts.gov/"
ROUTE_ZIP: LiteralString = f"{BASE_URL}PREZIP/"
REPORTING_PREFIX: LiteralString = (
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_"
)
ZIP: Literal[".zip"] = ".zip"
PARQUET: Literal[".parquet"] = ".parquet"
PATTERN_PARQUET: LiteralString = f"*{REPORTING_PREFIX}*{PARQUET}"

COLUMNS_DEFAULT: Sequence[Column] = (
    "date",
    "delay",
    "distance",
    "origin",
    "destination",
)
"""
Copied default from `previous flights.py`_.

.. _previous flights.py:
    https://github.com/vega/vega-datasets/blob/14cc1461c7120004886f25c0b4b0a611976f2e52/scripts/flights.py#L370-L371
"""

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
    - Converts (*start*, *end*) to monthly file names
    - Acts as a key, for detecting unique periods

    Notes
    -----
    `Latest Available Data`_ extends to roughly 2-4 months before current date

    .. _Latest Available Data:
        https://www.transtats.bts.gov/TableInfo.asp?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr&V0s1_b0yB=D
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
    def from_dates(cls, dates: IntoDateRange, /) -> DateRange:
        """Construct from a sequence/mapping defined time period."""
        match dates:
            case (start, end):
                return cls(start, end)
            case {"start": start, "end": end}:
                return cls(start, end)
            case _:
                raise TypeError(type(dates))

    @property
    def monthly(self) -> pl.Expr:
        """Generate a date range expression, with a monthly interval."""
        return pl.date_range(self.start, self.end, interval="1mo").alias("date")

    @cached_property
    def file_stems(self) -> Sequence[str]:
        """Returns the file stems of all sources the input would require."""
        date = col("date")
        year, month = (date.dt.year().alias("year"), date.dt.month().alias("month"))
        return tuple(
            pl.select(self.monthly)
            .lazy()
            .select(_file_stem_source(year, month).sort_by(date))
            .collect()
            .to_series()
            .to_list()
        )

    def paths(self, input_dir: Path, /) -> list[Path]:
        return [input_dir / f"{stem}{PARQUET}" for stem in self.file_stems]

    def __eq__(self, other: Any, /) -> bool:
        """Two ``DateRange``s are equivalent if they would require the same files."""
        return isinstance(other, DateRange) and self.file_stems == other.file_stems

    def __hash__(self) -> int:
        return hash(self.file_stems)


class Spec:
    """
    Describes a target output file, based on flights data.

    Parameters
    ----------
    range
        Time period used for source data.
        The end date is rounded up to the end of the month.
    n_rows
        Number of rows to include in the output.
    suffix
        File extension/output format.
    dt_format
        Datetime conversion for semi-structured outputs,
        see ``DateTimeFormat`` doc.
    columns
        Columns included in the output.
    write_options
        Overrides for defaults defined in ``Spec._WRITE_OPTIONS``.
    """

    _PREFIX: ClassVar[Literal["flights-"]] = "flights-"
    _RANDOM_SEED: ClassVar[Literal[42]] = 42
    _WRITE_OPTIONS: ClassVar[Mapping[Extension, WriteOptions]] = {
        ".arrow": {"compression": "uncompressed"},
        ".parquet": {"compression": "zstd", "compression_level": 22},
        ".csv": {
            "date_format": None,
            "datetime_format": None,
            "time_format": None,
            "null_value": None,
        },
    }
    """Default keyword arguments used for each output format."""

    def __init__(
        self,
        range: DateRange | IntoDateRange,
        n_rows: Rows,
        suffix: Extension,
        dt_format: DateTimeFormat = None,
        columns: Sequence[Column] = COLUMNS_DEFAULT,
        write_options: WriteOptions | None = None,
    ) -> None:
        self.range: DateRange = (
            range if isinstance(range, DateRange) else DateRange.from_dates(range)
        )
        n_rows, suffix, dt_format, columns, write_options = self._validate(
            n_rows, suffix, dt_format, columns, write_options
        )
        self.n_rows: Rows = n_rows
        self.suffix: Extension = suffix
        self.dt_format: DateTimeFormat = dt_format
        self.columns: Sequence[Column] = columns
        self.write_options: WriteOptions = self._merge_write_options(write_options)

    @classmethod
    def from_dict(cls, mapping: Mapping[str, Any], /) -> Spec:
        """Construct from a toml table definition."""
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
        """
        Encodes a short form of ``n_rows`` into the file name.

        Examples
        --------
        Note that the final name depends on ``suffix``:

            | n_rows         | stem          |
            | -------------- | ------------- |
            | 10_000         | "flights-10k" |
            | 1_000_000      | "flights-1m"  |
            | 12_000_000_000 | "flights-12b" |
        """
        frac = self.n_rows // THOUSAND
        if frac >= MILLION:
            s = f"{frac // MILLION}b"
        elif frac >= THOUSAND:
            s = f"{frac // THOUSAND}m"
        elif frac >= 1:
            s = f"{frac}k"
        else:
            s = f"{self.n_rows}"
        return f"{self._PREFIX}{s}{self.suffix}"

    @property
    def sort_by(self) -> Column:
        """Temporal column used to sort the transformed data."""
        return "time" if "time" in self.columns else "date"

    def transform(self, ldf: pl.LazyFrame, /) -> pl.DataFrame:
        """
        Materialize the spec for export.

        Parameters
        ----------
        ldf
            Cleaned source data, spanning ``self.range``.
        """
        return (
            self._transform_temporal(ldf)
            .select(self.columns)
            .collect()
            .sample(self.n_rows, seed=self._RANDOM_SEED)
            .sort(self.sort_by)
        )

    def write(self, df: pl.DataFrame, output_dir: Path, /) -> None:
        """
        Export the materialized spec.

        Parameters
        ----------
        df
            Materialized spec data, the result of ``self.transform(...)``.
        output_dir
            Output directory.
        """
        fp: Path = output_dir / self.name
        fp.touch()
        msg = f"Writing {fp.as_posix()!r} ..."
        logger.info(msg)
        kwds = self.write_options
        match self.suffix:
            case ".arrow":
                df.with_columns(pl.all().shrink_dtype()).write_ipc(fp, **kwds)
            case ".csv":
                df.write_csv(fp, **kwds)
            case ".json":
                df.write_json(fp)
            case ".parquet":
                df.write_parquet(fp, **kwds)
            case _:
                fp.unlink()
                msg = f"Unexpected extension {self.suffix!r}"
                raise NotImplementedError(msg)

    def _merge_write_options(self, kwds: WriteOptions, /) -> WriteOptions:
        defaults = dict(self._WRITE_OPTIONS.get(self.suffix, {}))
        if kwds:
            defaults.update(kwds)
        return defaults

    def _transform_temporal(self, ldf: pl.LazyFrame, /) -> pl.LazyFrame:
        if not self.dt_format:
            return ldf
        date: pl.Expr = col("date")
        if self.dt_format == "decimal":
            return ldf.select(
                (date.dt.hour() + date.dt.minute() / 60).alias("time"), cs.exclude(date)
            )
        return ldf.with_columns(date.dt.to_string(self.dt_format))

    @staticmethod
    def _validate(
        n_rows: Any, suffix: Any, dt_format: Any, columns: Any, write_options: Any, /
    ) -> tuple[Rows, Extension, DateTimeFormat, Sequence[Column], WriteOptions]:
        if not is_columns(columns):
            msg = f"`columns` contains unrecognized names:\n{columns!r}"
            raise TypeError(msg)

        if {"date", "time"}.isdisjoint(columns):
            msg = (
                f"Must specify one of {['date', 'time']!r} columns, "
                f"but got: {columns!r}"
            )
            raise TypeError(msg)

        if not is_datetime_format(dt_format):
            msg = f"Unrecognized datetime format: {dt_format!r}"
            raise TypeError(msg)

        if not is_rows(n_rows):
            msg = (
                "Number of rows must be either:\n"
                "  - 1 <= n_rows < 1_000\n"
                "  - Representable as thousands, millions, or billions without a remainder\n\n"
                f"But got: {n_rows!r}"
            )
            raise TypeError(msg)

        if not is_extension(suffix):
            msg = f"Unexpected extension {suffix!r}"
            raise TypeError(msg)

        if suffix == ".json" and write_options:
            msg = (
                f"Keyword arguments are not supported for {pl.DataFrame.write_json.__qualname__!r}.\n"
                f"But got: {write_options!r}\n"
            )
            raise TypeError(msg)

        write_options = write_options or {}
        if not is_write_options(write_options):
            msg = (
                f"Expected a mapping of keyword arguments for `write_options`.\n"
                f"But got: {type(write_options).__name__!r}"
            )
            raise TypeError(msg)

        return n_rows, suffix, dt_format, columns, write_options


class SourceMap:
    """
    Group specs by common data, scanning a `pl.LazyFrame`_ per-group.

    Parameters
    ----------
    input_dir
        Directory containing monthly input files.

    .. _pl.LazyFrame:
        https://docs.pola.rs/api/python/stable/reference/lazyframe/index.html
    """

    def __init__(self, input_dir: Path, /) -> None:
        self.input_dir: Path = input_dir
        self._mapping = defaultdict[DateRange, deque[Spec]](deque)
        self._frames: dict[DateRange, pl.LazyFrame] = {}

    @classmethod
    def from_specs(cls, specs: Iterable[Spec], input_dir: Path, /) -> SourceMap:
        """
        Construct with all dependent data grouped and loaded.

        Parameters
        ----------
        specs
            Target dataset definitions.
        input_dir
            Directory containing monthly input files.
        """
        obj = cls(input_dir)
        logger.info("Scanning dependencies ...")
        for spec in specs:
            obj.add_spec(spec)
        msg = f"Finished scanning {len(obj)!r} date ranges."
        logger.info(msg)
        return obj

    def add_spec(self, spec: Spec, /) -> None:
        """
        Adds a spec dependency, detecting and loading any shared resources.

        Required files for each unique ``DateRange`` are lazily read into a single table.

        Parameters
        ----------
        spec
            Describes a target output file.
        """
        d_range: DateRange = spec.range
        if d_range not in self._mapping:
            paths = d_range.paths(self.input_dir)
            self._frames[d_range] = self.clean(pl.scan_parquet(paths))
        self._mapping[d_range].append(spec)

    def iter_tasks(self) -> Iterator[tuple[Spec, pl.LazyFrame]]:
        """Yields each spec, with its respective clean source data."""
        if not len(self):
            msg = (
                "Dependent specs have not yet been added.\n\n"
                f"Try calling {self.add_spec.__qualname__}(...) first."
            )
            raise TypeError(msg)
        for d_range, frame in self._frames.items():
            for spec in self._mapping[d_range]:
                yield spec, frame

    @staticmethod
    def clean(ldf: pl.LazyFrame, /) -> pl.LazyFrame:
        """
        Fix *known* dataset issues, coerce types, rename columns.

        Parameters
        ----------
        ldf
            Monthly datasets, concatenated as a single table.

        Notes
        -----
        - Rows containing cancelled flights or null values are dropped (~3.16%)
        - Non compliant* `ISO-8601`_ times are corrected

        *Invalid midnight representation prior to `ISO-8601-1-2019-Amd-1-2022`_

        **Input schema**:

            {
                "FlightDate": datetime.date,
                "CRSDepTime": str,
                "DepTime": str,
                "DepDelay": float,
                "ArrDelay": float,
                "Distance": float,
                "Origin": str,
                "Dest": str,
                "Cancelled": float,
            }

        **Output schema**:

            {
                "date": datetime.datetime,
                "delay": int,
                "distance": int,
                "origin": str,
                "destination": str,
                "ScheduledFlightDate": datetime.date,
                "ScheduledFlightTime": datetime.time,
                "DepDelay": int,
            }

        .. _ISO-8601:
            https://en.wikipedia.org/wiki/ISO_8601
        .. _ISO-8601-1-2019-Amd-1-2022:
            https://cdn.standards.iteh.ai/samples/81801/f527872a9fe34281ae3a4af8e730f3f8/ISO-8601-1-2019-Amd-1-2022.pdf#page=8
        """
        cancelled = col("Cancelled").cast(bool)
        flight_date = col("FlightDate")
        dep_time = col("DepTime")
        times = cs.ends_with("DepTime")

        wrap_midnight = times.str.replace("2400", "0000").str.to_time("%H%M")
        datetime = flight_date.dt.combine(dep_time)
        flight_date_corrected = (
            pl.when(dep_time == pl.time(0, 0, 0, 0))
            .then(datetime.dt.offset_by("1d"))
            .otherwise(datetime)
        )
        return (
            ldf.filter(
                ~pl.any_horizontal(cancelled, dep_time == "", cs.float().is_null())
            )
            .with_columns(wrap_midnight, cs.float().cast(int))
            .select(
                flight_date_corrected.alias("date"),
                col("ArrDelay").alias("delay"),
                col("Distance", "Origin").name.to_lowercase(),
                col("Dest").alias("destination"),
                flight_date.alias("ScheduledFlightDate"),
                col("CRSDepTime").alias("ScheduledFlightTime"),
                "DepDelay",
            )
        )

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
        Directory to store monthly input files.
    output_dir
        Directory to write realised specs to.

    Notes
    -----
    - Detecting & downloading dependencies
        - Sharing common data
    - Extracting & concatenating
    - Transforms to meet a given spec
    - Writing to target formats

    Examples
    --------
    Specs can be defined programatically:

    >>> from pathlib import Path
    >>> input_dir = Path.cwd()
    >>> output_dir = Path.cwd() / "output"
    >>> date_range = DateRange((2001, 1), (2001, 12))
    >>> prog = Flights([
    ...     Spec(date_range, 5_000, ".csv", dt_format="iso:strict"),
    ...     Spec(date_range, 20_000, ".parquet"),
    ...     Spec(
    ...         date_range,
    ...         200_000,
    ...         ".json",
    ...         dt_format="%Y/%m/%d %H:%M",
    ...         columns=("date", "origin", "destination"),
    ...     ),
    ...     Spec(((2001, 1, 1), (2001, 3, 31)), 100_000, ".arrow"),
    ... ])
    >>> prog.run()  # doctest: +SKIP

    Or they can be loaded in from a ``.toml`` file:

    >>> source = Path.cwd() / "source.toml"
    >>> decl = Flights.from_toml(source, input_dir, output_dir)  # doctest: +SKIP
    >>> decl.run()  # doctest: +SKIP
    """

    input_dir: Path
    output_dir: Path
    specs: Sequence[Spec]
    sources: SourceMap

    def __init__(
        self, specs: Sequence[Spec], input_dir: str | Path, output_dir: str | Path
    ) -> None:
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.specs = specs

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
        return pl.select(pl.concat(spec.range.monthly for spec in self), eager=False)

    @property
    def _required_stems(self) -> set[str]:
        date = col("date")
        return set(
            self.ranges.select(
                date.dt.year().alias("year"), date.dt.month().alias("month")
            )
            .unique()
            .select(_file_stem_source("year", "month"))
            .collect()
            .to_series()
            .to_list()
        )

    @property
    def _existing_stems(self) -> set[str]:
        it = self.input_dir.glob(PATTERN_PARQUET)
        return {_without_suffixes(fp.name) for fp in it}

    @property
    def missing_stems(self) -> set[str]:
        missing = self._required_stems - self._existing_stems
        if n := len(missing):
            msg = f"Missing {n} sources"
            logger.info(msg)
            if n >= 5:
                logger.warning("Downloads may exceed 100MB")
            if n >= 11:
                logger.warning("Total number of rows will exceed 5_000_000")
        return missing

    async def _download_sources_async(self, names: Iterable[str], /) -> list[Path]:
        """Request, write missing data."""
        session = niquests.AsyncSession(base_url=ROUTE_ZIP)
        aws = (_request_async(session, name) for name in names)
        buffers = await asyncio.gather(*aws)
        writes = (_write_zip_to_parquet_async(self.input_dir, buf) for buf in buffers)
        return await asyncio.gather(*writes)

    def download_sources(self) -> None:
        """
        Ensure all required source data is saved to ``self.input_dir``.

        Any month(s) that are missing will be requested from `transtats`_.

        .. _transtats:
            https://www.transtats.bts.gov
        """
        logger.info("Detecting required sources ...")
        if missing := self.missing_stems:
            asyncio.run(self._download_sources_async(missing))
            logger.info("Successfully downloaded all missing sources.")
        else:
            logger.info("Sources already downloaded.")

    def run(self) -> None:
        """Top-level command providing fully managed data collection, transformation and export."""
        logger.info("Starting job ...")
        self.download_sources()
        self.sources = SourceMap.from_specs(self, self.input_dir)
        for spec, frame in self.sources.iter_tasks():
            result = spec.transform(frame)
            spec.write(result, self.output_dir)
        logger.info("Finished job.")


async def _request_async(session: niquests.AsyncSession, name: str, /) -> io.BytesIO:
    name = f"{_without_suffixes(name)}{ZIP}"
    msg = f"Requesting {name!r} ..."
    logger.info(msg)
    async with session:
        response = await session.get(name)
        if response.ok and (content := response.content):
            buf = io.BytesIO()
            buf.write(content)
            msg = f"Successful {name!r}"
            logger.info(msg)
            return buf
        msg = f"Failed for {name!r}"
        raise NotImplementedError(msg)


def _write_zip_to_parquet(input_dir: Path, buf: io.BytesIO, /) -> Path:
    """
    Extract inner ``.csv`` from ``.zip``, write to ``.parquet``of the same name.

    Parameters
    ----------
    input_dir
        Directory to store monthly input files.
    buf
        Buffer containing the zipped response.

    Notes
    -----
    - We pay the *decompress*->*compress* cost only **once** per-download
    - Only the subset of columns defined in ``SCAN_SCHEMA`` are preserved
        - Further reduces file size
        - Also, some unused columns contain invalid utf8 values

    Original file:

        On_Time_Reporting_Carrier_On_Time_Performance_1987_present_YYYY_M.zip
        ├──On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_YYYY_M.csv
        └──readme.html

    Result file:

        On_Time_Reporting_Carrier_On_Time_Performance_1987_present_YYYY_M.parquet

    Size comparison:

        | format   | min (KB) | max  (KB) |
        | -------- | -------- | --------- |
        | .parquet | 1_800    | 3_000     |
        | .zip     | 15_000   | 30_000    |
        | .csv     | 200_000  | 250_000   |
    """
    zip_csv = next(zipfile.Path(zipfile.ZipFile(buf)).glob("*.csv"))
    stem = zip_csv.at.replace("(", "").replace(")", "")
    output = (input_dir / stem).with_suffix(".parquet")
    output.touch()
    msg = f"Writing {output.as_posix()!r}"
    logger.debug(msg)
    with zip_csv.open("rb") as strm:
        ldf = pl.scan_csv(
            strm,
            try_parse_dates=True,
            schema_overrides=SCAN_SCHEMA,
            encoding="utf8-lossy",
        ).select(SCAN_SCHEMA.names())
    ldf.collect().write_parquet(output, compression="zstd", compression_level=17)
    return output


async def _write_zip_to_parquet_async(input_dir: Path, buf: io.BytesIO, /) -> Path:
    """
    Wraps ``_write_zip_to_parquet`` to run in a separate thread.

    - **Greatly** reduces the cost of the decompress > compress operations
    - During testing, each write would block for ~10s
    """
    return await asyncio.to_thread(_write_zip_to_parquet, input_dir, buf)


def _file_stem_source[T: (str, pl.Expr)](year: T, month: T, /) -> pl.Expr:
    """Returns an expression that composes the file stem for a single month."""
    return pl.concat_str(pl.lit(REPORTING_PREFIX), year, pl.lit("_"), month)


def _without_suffixes[T: (str, Path)](source: T, /) -> T:
    """Ensure all suffixes (not just the last) are removed."""
    if isinstance(source, str):
        return source.removesuffix("".join(Path(source).suffixes))
    return Path(str(source).removesuffix("".join(source.suffixes)))


def _get_args(tp: Any, /) -> tuple[Any, ...]:
    unwrapped = getattr(tp, "__value__", tp)
    return _typing_get_args(unwrapped)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    repo_root = Path(__file__).parent.parent
    source_toml = repo_root / "_data" / "flights.toml"
    app = Flights.from_toml(
        source_toml,
        input_dir=Path.home() / ".vega_datasets",
        output_dir=repo_root / "data",
    )
    app.run()


if __name__ == "__main__":
    main()
