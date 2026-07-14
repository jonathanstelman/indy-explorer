"""
Pre-PR sanity check for the scheduled data pipeline (#77).

Run after pipeline.py regenerates data/resorts.csv, before a PR is opened. Exits
non-zero (aborting the workflow before a PR is opened) only on structural failures:
an empty CSV, an entirely missing expected column, or a raised Pydantic
ValidationError from load_resorts() (missing required field, malformed indy_page).

Out-of-range/malformed optional field values are handled by Resort's own soft
validators (see models.py) — they get logged and nulled rather than raised. This
script captures those warnings and reports them in the summary for human review,
without failing the job.

Usage:
    poetry run python validate_resorts.py
"""

import logging
import os
import sys
from dataclasses import dataclass, field

import pandas as pd

from data import RESORTS_CSV, load_resorts
from models import Resort

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
SUMMARY_PATH = os.path.join(REPORTS_DIR, 'validation_summary.md')


@dataclass
class ValidationResult:
    ok: bool
    resort_count: int = 0
    errors: list[str] = field(default_factory=list)
    nulled_warnings: list[str] = field(default_factory=list)


class _WarningCapture(logging.Handler):
    """Captures WARNING-level log records (soft-null notices) emitted by models.py."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def check_row_count(df: pd.DataFrame) -> str | None:
    if len(df) == 0:
        return 'data/resorts.csv has 0 rows — pipeline output looks empty or broken.'
    return None


def check_expected_columns(df: pd.DataFrame) -> str | None:
    missing = sorted(set(Resort.model_fields.keys()) - set(df.columns))
    if missing:
        return (
            f'data/resorts.csv is missing {len(missing)} expected column(s): '
            f'{", ".join(missing)}'
        )
    return None


def run_validation() -> ValidationResult:
    df = pd.read_csv(RESORTS_CSV, na_values=[''], keep_default_na=False)
    errors = [e for e in (check_row_count(df), check_expected_columns(df)) if e]

    handler = _WarningCapture()
    logger = logging.getLogger('models')
    logger.addHandler(handler)
    resorts = []
    try:
        resorts = load_resorts()
    except Exception as e:
        errors.append(f'load_resorts() raised {type(e).__name__}: {e}')
    finally:
        logger.removeHandler(handler)

    return ValidationResult(
        ok=not errors,
        resort_count=len(resorts),
        errors=errors,
        nulled_warnings=handler.messages,
    )


def render_summary(result: ValidationResult) -> str:
    lines = ['## Data Validation', '']
    if result.ok:
        lines.append(f'✅ {result.resort_count} resorts loaded successfully.')
    else:
        lines.append('❌ Validation failed:')
        for e in result.errors:
            lines.append(f'- {e}')

    if result.nulled_warnings:
        lines.append('')
        lines.append(
            f'⚠️ {len(result.nulled_warnings)} field(s) nulled (out of range or malformed) '
            'during load — review before merging:'
        )
        for w in result.nulled_warnings:
            lines.append(f'- {w}')

    return '\n'.join(lines) + '\n'


def main() -> int:
    result = run_validation()
    summary = render_summary(result)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(SUMMARY_PATH, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(summary)
    return 0 if result.ok else 1


if __name__ == '__main__':
    sys.exit(main())
