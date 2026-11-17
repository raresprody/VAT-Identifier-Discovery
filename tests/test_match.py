"""Each test is a case seen during the manual checks (data/candidates.csv)."""
from match import decide, normalise_name


def test_adore_golf_name_and_postcode_equal_is_tier_a():
    assert decide("GB140488125", "ADORE GOLF LIMITED", "NE35 9PE",
                  "ADORE GOLF LIMITED", "NE35 9PE", 1) == "tier A"


def test_deswik_accountants_address_is_tier_b():
    # Companies House: C/O Azets, Beaconsfield. HMRC: Wood Lane, London.
    assert decide("GB128277402", "DESWIK EUROPE LIMITED", "HP9 2JH",
                  "DESWIK EUROPE LTD", "W12 7FQ", 1) == "tier B"


def test_getthelabel_number_of_another_group_company_is_rejected():
    # Found on the company's own website. Same address, different company.
    assert decide("GB438752270", "GETTHELABEL.COM LIMITED", "NG20 8RY",
                  "TOPGRADE SPORTSWEAR LTD", "NG20 8RY", 1) == "reject: different company"


def test_inn_collection_similar_name_same_address_is_rejected():
    # rapidfuzz ratio 86.2, above the 85 threshold first considered.
    assert decide("GB179175273", "INN COLLECTION BIDCO 2 LIMITED", "NE12 8BS",
                  "INN COLLECTION TOPCO LIMITED", "NE12 8BS", 1) == "reject: different company"


def test_company_number_copied_by_mistake_fails_checksum():
    assert decide("11994089", "HH DEVELOPMENT GROUP LIMITED", "B90 4BN",
                  None, None, 1) == "reject: checksum"


def test_number_unknown_to_hmrc_is_rejected():
    assert decide("GB106566322", "ANY LTD", "RM1 1BW", None, None, 1) == "reject: not registered"


def test_shared_name_with_different_postcode_goes_to_review():
    assert decide("GB106566322", "ACME LIMITED", "RM1 1BW",
                  "ACME LTD", "SW1A 1AA", 2) == "review"


def test_no_candidate_is_not_found():
    assert decide("", "VENTAQUEST DEVELOPMENTS LIMITED", "SW3 1RT", None, None, 1) == "not found"


def test_harmless_differences_are_ignored():
    assert normalise_name("Deswik Europe Ltd") == normalise_name("DESWIK EUROPE LIMITED")
    assert normalise_name("Rothschild & Co Holdings Ltd.") == normalise_name("ROTHSCHILD AND CO HOLDINGS LIMITED")


def test_meaningful_differences_are_kept():
    assert normalise_name("INN COLLECTION BIDCO 2 LIMITED") != normalise_name("INN COLLECTION TOPCO LIMITED")
    assert normalise_name("HH DEVELOPMENT GROUP LIMITED") != normalise_name("HH DEVELOPMENTS LTD")
