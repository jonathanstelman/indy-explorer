import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data import load_resorts
from models import Resort, ResortSummary


def test_load_resorts_returns_list_of_resort():
    resorts = load_resorts()
    assert len(resorts) > 0
    assert all(isinstance(r, Resort) for r in resorts)


def test_all_resorts_have_required_fields():
    resorts = load_resorts()
    for resort in resorts:
        assert resort.resort_id
        assert resort.name
        assert resort.region
        assert resort.indy_page
        assert resort.reservation_status


def test_resort_ids_are_unique():
    resorts = load_resorts()
    ids = [r.resort_id for r in resorts]
    assert len(ids) == len(set(ids))


def test_unused_metric_and_tooltip_fields_are_dropped():
    # #128's unit toggle converts client-side from canonical imperial values, so these
    # precomputed fields (#132) are dead weight on the wire and in data/resorts.csv.
    dropped_fields = {'vertical_meters', 'trail_length_km', 'acres_tt', 'vertical_tt'}
    assert not dropped_fields & set(Resort.model_fields.keys())
    assert not dropped_fields & set(ResortSummary.model_fields.keys())
