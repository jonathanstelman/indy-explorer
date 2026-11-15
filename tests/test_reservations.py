import reservations


def test_normalize_reservation_name_strips_state_suffix():
    """The 26/27 reservations page appends a state/province code to each name
    ("Pats Peak, NH"), which broke every name match against resorts.csv."""
    assert reservations.normalize_reservation_name('Pats Peak, NH') == 'Pats Peak'
    assert reservations.normalize_reservation_name('Hardwood Ski & Bike, ON') == (
        'Hardwood Ski and Bike'
    )


def test_normalize_reservation_name_applies_name_map_after_stripping_suffix():
    assert reservations.normalize_reservation_name('Berkshire East, MA') == (
        'Berkshire East Mountain Resort'
    )
    assert reservations.normalize_reservation_name("Smugglers' Notch, VT") == (
        "Smugglers' Notch Resort"
    )


def test_normalize_reservation_name_leaves_unsuffixed_names_alone():
    assert reservations.normalize_reservation_name('Cannon Mountain') == 'Cannon Mountain'
    # A comma that isn't followed by a 2-letter code is part of the name.
    assert reservations.normalize_reservation_name('Resort, The Big One') == ('Resort, The Big One')
