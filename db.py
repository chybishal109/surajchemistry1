import sqlite3
import chem

DB = "atlas.db"

# name, category, smiles, works (what it does / where it is used), tags
SEED = [
    ("Vanillin", "Flavour", "COc1cc(C=O)ccc1O", "Gives vanilla flavour and scent to ice cream, baking, perfumes and chocolate.", "Flavour,Fragrance"),
    ("Menthol", "Flavour", "CC(C)C1CCC(C)CC1O", "Creates the cooling sensation in toothpaste, balms, lozenges and chewing gum.", "Flavour,Pain relief,Oral care"),
    ("Capsaicin", "Natural product", "COc1cc(CNC(=O)CCCCC=CC(C)C)ccc1O", "Makes chilli hot; used in pain-relief creams and pepper spray.", "Flavour,Pain relief"),
    ("Limonene", "Terpene", "CC1=CCC(CC1)C(C)=C", "Citrus scent in cleaners, solvents and aromatherapy oils.", "Fragrance,Cleaning"),
    ("Citric acid", "Acid", "OC(=O)CC(O)(CC(O)=O)C(O)=O", "Sour taste and preservative in drinks; descaler; part of the Krebs cycle.", "Flavour,Cleaning,Metabolism"),
    ("Dopamine", "Neurotransmitter", "NCCc1ccc(O)c(O)c1", "Brain messenger for reward, motivation and movement; drug for shock and heart failure.", "Mood,Medicine"),
    ("Serotonin", "Neurotransmitter", "NCCc1c[nH]c2ccc(O)cc12", "Regulates mood, appetite and sleep; target of antidepressants.", "Mood,Sleep"),
    ("Melatonin", "Hormone", "COc1ccc2[nH]cc(CCNC(C)=O)c2c1", "Controls the sleep-wake cycle; taken as a sleep and jet-lag aid.", "Sleep,Medicine"),
    ("Ascorbic acid", "Vitamin", "OC[C@H](O)[C@H]1OC(=O)C(O)=C1O", "Vitamin C: antioxidant, builds collagen, supports immunity, food preservative.", "Antioxidant,Nutrition"),
    ("Naproxen", "Drug", "COc1ccc2cc(ccc2c1)[C@H](C)C(O)=O", "NSAID that relieves pain, fever and inflammation.", "Pain relief,Medicine"),
    ("Lidocaine", "Drug", "CCN(CC)CC(=O)Nc1c(C)cccc1C", "Local anaesthetic for dental work and minor surgery; treats some heart arrhythmias.", "Pain relief,Medicine"),
    ("Resveratrol", "Natural product", "Oc1ccc(C=Cc2cc(O)cc(O)c2)cc1", "Antioxidant polyphenol in grape skins, studied for heart and ageing research.", "Antioxidant,Nutrition"),
]


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS molecules(
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, smiles TEXT UNIQUE, works TEXT, tags TEXT,
            formula TEXT, mw REAL, logp REAL, tpsa REAL, hbd INT, hba INT, rotb INT, rings INT, violations INT)""")
        if c.execute("SELECT COUNT(*) FROM molecules").fetchone()[0] == 0:
            for n, cat, s, w, t in SEED:
                add(n, cat, s, w, t, c)


def add(name, category, smiles, works, tags, c=None):
    m = chem.parse(smiles)
    if m is None:
        raise ValueError("Invalid SMILES")
    d = chem.analyze(m)
    own = c is None
    c = c or conn()
    c.execute("INSERT OR IGNORE INTO molecules(name,category,smiles,works,tags,formula,mw,logp,tpsa,hbd,hba,rotb,rings,violations) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (name, category, smiles, works, tags, d["formula"], d["mw"], d["logp"], d["tpsa"], d["hbd"], d["hba"], d["rotb"], d["rings"], d["violations"]))
    if own:
        c.commit(); c.close()


def all_rows():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM molecules ORDER BY name")]


def delete(mid):
    with conn() as c:
        c.execute("DELETE FROM molecules WHERE id=?", (mid,))
