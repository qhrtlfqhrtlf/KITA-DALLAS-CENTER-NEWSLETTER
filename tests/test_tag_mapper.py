import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from lib.tag_mapper import get_tags, OUTLET_MAP

def test_always_includes_fixed_tags():
    tags = get_tags("Reuters", "임의 본문")
    assert "@kitasns" in tags
    assert "@kita_dallas_center" in tags

def test_maps_reuters_to_account():
    tags = get_tags("Reuters", "임의 본문")
    assert "@reuters" in tags

def test_maps_bloomberg_to_account():
    tags = get_tags("Bloomberg", "임의 본문")
    assert "@bloombergbusiness" in tags

def test_no_duplicate_tags():
    tags = get_tags("Reuters", "Reuters mentioned again")
    assert tags.count("@reuters") == 1

def test_outlet_map_covers_all_sources():
    sources = ["Reuters", "Bloomberg", "WSJ", "FT", "Politico", "USTR"]
    for s in sources:
        assert s in OUTLET_MAP
