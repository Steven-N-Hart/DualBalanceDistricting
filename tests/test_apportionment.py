import pytest

from dualbalance.apportionment import apportion_seats


def test_each_state_gets_at_least_one_seat():
    seats = apportion_seats({"A": 100, "B": 50}, total_seats=2)
    assert seats == {"A": 1, "B": 1}


def test_total_seats_matches_request():
    seats = apportion_seats({"A": 1000, "B": 500, "C": 200}, total_seats=10)
    assert sum(seats.values()) == 10


def test_hand_computed_three_state_example():
    # Worked by hand from the Method of Equal Proportions formula:
    # priority(s, n) = pop(s) / sqrt(n * (n+1))
    # After each state's initial seat, the assignment order with these pops is
    # A, A, B, A -> {A:4, B:2, C:1}.
    seats = apportion_seats({"A": 1000, "B": 500, "C": 200}, total_seats=7)
    assert seats == {"A": 4, "B": 2, "C": 1}


def test_too_few_seats_raises():
    with pytest.raises(ValueError, match="less than the number of states"):
        apportion_seats({"A": 100, "B": 50, "C": 25}, total_seats=2)


def test_negative_population_raises():
    with pytest.raises(ValueError, match="negative"):
        apportion_seats({"A": 100, "B": -1}, total_seats=5)


def test_tie_break_is_lexicographic():
    # Identical populations -> ties broken by ascending state name. With three
    # equal states and 5 seats: each gets 1 seat first, then the remaining 2
    # priorities are identical, so the alphabetically smallest two pick up the
    # extras (A and B, then back to A).
    seats = apportion_seats({"A": 100, "B": 100, "C": 100}, total_seats=5)
    assert seats == {"A": 2, "B": 2, "C": 1}


# 2020 U.S. apportionment populations (Census Bureau, includes overseas federal
# employees attributed to home state) and the resulting official seat counts.
# This is the strongest single regression test of the algorithm.
_APPORTIONMENT_2020_POPULATIONS: dict[str, int] = {
    "AL":  5_030_053, "AK":    736_081, "AZ":  7_158_923, "AR":  3_013_756,
    "CA": 39_576_757, "CO":  5_782_171, "CT":  3_608_298, "DE":    990_837,
    "FL": 21_570_527, "GA": 10_725_274, "HI":  1_460_137, "ID":  1_841_377,
    "IL": 12_822_739, "IN":  6_790_280, "IA":  3_192_406, "KS":  2_940_865,
    "KY":  4_509_342, "LA":  4_661_468, "ME":  1_363_582, "MD":  6_185_278,
    "MA":  7_029_917, "MI": 10_084_442, "MN":  5_709_752, "MS":  2_961_279,
    "MO":  6_160_281, "MT":  1_085_407, "NE":  1_963_333, "NV":  3_108_462,
    "NH":  1_379_089, "NJ":  9_294_493, "NM":  2_120_220, "NY": 20_215_751,
    "NC": 10_453_948, "ND":    779_702, "OH": 11_808_848, "OK":  3_963_516,
    "OR":  4_241_500, "PA": 13_011_844, "RI":  1_098_163, "SC":  5_124_712,
    "SD":    887_127, "TN":  6_916_897, "TX": 29_183_290, "UT":  3_275_252,
    "VT":    643_503, "VA":  8_654_542, "WA":  7_715_946, "WV":  1_795_045,
    "WI":  5_897_473, "WY":    577_719,
}

_APPORTIONMENT_2020_SEATS: dict[str, int] = {
    "AL":  7, "AK":  1, "AZ":  9, "AR":  4, "CA": 52, "CO":  8, "CT":  5,
    "DE":  1, "FL": 28, "GA": 14, "HI":  2, "ID":  2, "IL": 17, "IN":  9,
    "IA":  4, "KS":  4, "KY":  6, "LA":  6, "ME":  2, "MD":  8, "MA":  9,
    "MI": 13, "MN":  8, "MS":  4, "MO":  8, "MT":  2, "NE":  3, "NV":  4,
    "NH":  2, "NJ": 12, "NM":  3, "NY": 26, "NC": 14, "ND":  1, "OH": 15,
    "OK":  5, "OR":  6, "PA": 17, "RI":  2, "SC":  7, "SD":  1, "TN":  9,
    "TX": 38, "UT":  4, "VT":  1, "VA": 11, "WA": 10, "WV":  2, "WI":  8,
    "WY":  1,
}


def test_reproduces_2020_us_apportionment():
    result = apportion_seats(_APPORTIONMENT_2020_POPULATIONS, total_seats=435)
    assert result == _APPORTIONMENT_2020_SEATS
