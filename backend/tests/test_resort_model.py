import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data import load_resorts
from models import Resort


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
