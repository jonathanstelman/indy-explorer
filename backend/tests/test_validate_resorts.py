import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd

from models import Resort
from validate_resorts import (
    ValidationResult,
    _WarningCapture,
    check_expected_columns,
    check_row_count,
    render_summary,
    run_validation,
)


def test_check_row_count_empty_df_returns_error():
    df = pd.DataFrame()
    assert check_row_count(df) is not None


def test_check_row_count_nonempty_df_returns_none():
    df = pd.DataFrame({'a': [1]})
    assert check_row_count(df) is None


def test_check_expected_columns_missing_returns_error_naming_them():
    df = pd.DataFrame({'resort_id': ['r1']})
    error = check_expected_columns(df)
    assert error is not None
    assert 'name' in error


def test_check_expected_columns_all_present_returns_none():
    df = pd.DataFrame({name: [] for name in Resort.model_fields.keys()})
    assert check_expected_columns(df) is None


def test_warning_capture_records_nulled_fields():
    handler = _WarningCapture()
    logger = logging.getLogger('models')
    logger.addHandler(handler)
    try:
        Resort(
            resort_id='r1',
            name='Test',
            region='West',
            indy_page='https://example.com',
            reservation_status='Not Required',
            acres=-5,
        )
    finally:
        logger.removeHandler(handler)
    assert len(handler.messages) == 1
    assert 'acres' in handler.messages[0]


def test_render_summary_ok_no_warnings():
    result = ValidationResult(ok=True, resort_count=5)
    summary = render_summary(result)
    assert '5 resorts loaded successfully' in summary
    assert 'nulled' not in summary.lower()


def test_render_summary_failure_lists_errors():
    result = ValidationResult(ok=False, errors=['boom'])
    summary = render_summary(result)
    assert 'boom' in summary
    assert 'Validation failed' in summary


def test_render_summary_includes_nulled_warnings():
    result = ValidationResult(
        ok=True, resort_count=3, nulled_warnings=['resort=r1 field=acres value=-5.0 ...']
    )
    summary = render_summary(result)
    assert '1 field(s) nulled' in summary
    assert 'resort=r1' in summary


def test_run_validation_against_real_data():
    result = run_validation()
    assert result.ok
    assert result.resort_count > 0
