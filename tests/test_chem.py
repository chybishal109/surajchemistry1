import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import chem, db


def test_parse_invalid():
    assert chem.parse("not-a-smiles") is None


def test_vanillin():
    d = chem.analyze(chem.parse("COc1cc(C=O)ccc1O"))
    assert d["formula"] == "C8H8O3" and abs(d["mw"] - 152.15) < 0.1


def test_seed_valid_and_has_works():
    assert all(chem.parse(s) is not None and w and t for _, _, s, w, t in db.SEED)
