import datetime
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import chem, db, report

st.set_page_config(page_title="Molecule Atlas", page_icon="🌌", layout="wide")
db.init()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=Outfit:wght@300;400;600&family=IBM+Plex+Mono&display=swap');
html, body, [class*="css"], .stMarkdown p { font-family:'Outfit',sans-serif; }
h1,h2,h3 { font-family:'Syne',sans-serif !important; color:#ff7a59; letter-spacing:-.5px; }
code, .stDataFrame { font-family:'IBM Plex Mono',monospace !important; }
.stApp { background:linear-gradient(160deg,#170f22 0%,#2a1740 60%,#170f22 100%); }
[data-testid=stSidebar] { background:#110a1a; border-right:1px solid #3a2a52; }
.card { background:#241833; border:1px solid #4a3568; border-radius:16px; padding:16px 20px; height:100%; }
.card b { font-size:1.8rem; color:#5eead4; font-family:'Syne',sans-serif; }
.card span { display:block; color:#b9a8d0; font-size:.75rem; text-transform:uppercase; letter-spacing:2px; }
.works { background:#2f1d45; border-left:4px solid #ff7a59; padding:12px 16px; border-radius:8px; font-size:1.05rem; }
.tag { display:inline-block; background:#5eead422; color:#5eead4; border:1px solid #5eead466; padding:2px 10px; border-radius:20px; margin:2px; font-size:.8rem; }
</style>""", unsafe_allow_html=True)

df = pd.DataFrame(db.all_rows())
PROPS = {"mw": "Mol. weight", "logp": "LogP", "tpsa": "TPSA", "hbd": "HBD", "hba": "HBA", "rotb": "Rot. bonds", "rings": "Rings"}
ALL_TAGS = sorted({t.strip() for s in df.tags for t in s.split(",") if t.strip()})


def tags_html(s):
    return "".join(f"<span class='tag'>{t.strip()}</span>" for t in s.split(",") if t.strip())


def viewer(block, style="ball & stick"):
    sty = {"stick": {"stick": {}}, "sphere": {"sphere": {"scale": .3}}, "ball & stick": {"stick": {"radius": .15}, "sphere": {"scale": .25}}}[style]
    components.html(f"""<script src="https://3dmol.org/build/3Dmol-min.js"></script>
    <div id="v" style="height:380px;width:100%;position:relative;border-radius:14px;overflow:hidden"></div>
    <script>let v=$3Dmol.createViewer("v",{{backgroundColor:"#110a1a"}});
    v.addModel(`{block}`,"sdf");v.setStyle({{}},{json.dumps(sty)});v.zoomTo();v.spin(true);v.render();</script>""", height=390)


def molecule_page(r):
    m = chem.parse(r["smiles"])
    st.subheader(r["name"])
    st.markdown(f"<div class='works'><b>Works:</b> {r['works']}</div>", unsafe_allow_html=True)
    st.markdown(tags_html(r["tags"]), unsafe_allow_html=True)
    a, b = st.columns(2)
    a.image(chem.image(m), caption=f"{r['formula']} · {r['category']}")
    with b:
        style = st.radio("3D style", ["ball & stick", "stick", "sphere"], horizontal=True, key=f"s{r['id']}")
        blk = chem.mol_block(m)
        viewer(blk, style) if blk else st.warning("3D embedding failed.")
    props = {"Works": r["works"], "Category": r["category"], "Formula": r["formula"], "Mol. weight": r["mw"], "LogP": r["logp"],
             "TPSA": r["tpsa"], "H-bond donors": r["hbd"], "H-bond acceptors": r["hba"], "Rotatable bonds": r["rotb"],
             "Rings": r["rings"], "Lipinski violations": r["violations"], "SMILES": r["smiles"]}
    st.table(pd.DataFrame({"Property": props.keys(), "Value": [str(v) for v in props.values()]}).set_index("Property"))
    st.download_button("⬇ PDF report", report.pdf(r["name"], r["smiles"], m, r, r["works"]), f"{r['name']}.pdf")


page = st.sidebar.radio("Navigate", ["Constellation", "Find by Purpose", "Molecule Page", "Lab Bench", "Compare", "About"])
st.sidebar.caption("Molecule Atlas · RDKit · 3Dmol.js")

if page == "Constellation":
    st.title("🌌 Molecule Atlas")
    st.caption("Every molecule is a star. Position = size and fat-solubility; colour = what it works for.")
    k = st.columns(4)
    for col, (lab, val) in zip(k, [("Molecules", len(df)), ("Purposes", len(ALL_TAGS)), ("Avg weight", round(df.mw.mean(), 1)),
                                    ("Drug-like", int((df.violations == 0).sum()))]):
        col.markdown(f"<div class='card'><span>{lab}</span><b>{val}</b></div>", unsafe_allow_html=True)
    df["main"] = df.tags.str.split(",").str[0]
    fig = px.scatter(df, x="mw", y="logp", color="main", size="tpsa", hover_name="name", hover_data={"works": True, "main": False},
                     template="plotly_dark", height=520, color_discrete_sequence=px.colors.qualitative.Pastel,
                     labels={"mw": "Molecular weight", "logp": "LogP", "main": "Main purpose"})
    fig.update_traces(marker=dict(line=dict(width=1, color="white"), opacity=.9))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
    pick = df.iloc[datetime.date.today().toordinal() % len(df)]
    st.subheader("✨ Molecule of the day")
    c1, c2 = st.columns([1, 2])
    c1.image(chem.image(chem.parse(pick.smiles)))
    c2.markdown(f"### {pick['name']}\n{pick['works']}")

elif page == "Find by Purpose":
    st.title("Find by Purpose")
    q = st.text_input("What do you need a molecule for? (e.g. sleep, pain, flavour, antioxidant)")
    sel = st.multiselect("Purpose tags", ALL_TAGS)
    f = df
    if q:
        f = f[f.apply(lambda r: q.lower() in f"{r['name']} {r['works']} {r['tags']} {r['formula']} {r['smiles']}".lower(), axis=1)]
    if sel:
        f = f[f.tags.apply(lambda s: any(t in s for t in sel))]
    st.write(f"**{len(f)}** molecule(s)")
    cols = st.columns(3)
    for i, (_, r) in enumerate(f.iterrows()):
        with cols[i % 3]:
            st.image(chem.image(chem.parse(r["smiles"]), (300, 210)))
            st.markdown(f"**{r['name']}** · {r['formula']}  \n{r['works']}", unsafe_allow_html=True)
            st.markdown(tags_html(r["tags"]), unsafe_allow_html=True)

elif page == "Molecule Page":
    st.title("Molecule Page")
    r = df[df.name == st.selectbox("Choose a molecule", df.name)].iloc[0].to_dict()
    molecule_page(r)
    if st.button("🗑 Remove from atlas"):
        db.delete(int(r["id"])); st.rerun()

elif page == "Lab Bench":
    st.title("Lab Bench")
    name = st.text_input("Name"); cat = st.text_input("Category", "Custom")
    works = st.text_area("Works (what is it used for?)"); tags = st.text_input("Purpose tags (comma separated)", "Custom")
    smi = st.text_input("SMILES", "CC(=O)Oc1ccccc1C(=O)O")
    m = chem.parse(smi)
    if m is None:
        st.error("Invalid SMILES")
    else:
        d = chem.analyze(m)
        a, b = st.columns(2)
        a.image(chem.image(m)); b.json(d)
        st.success("Passes Lipinski's rule of five") if d["violations"] == 0 else st.warning(f"{d['violations']} Lipinski violation(s)")
        blk = chem.mol_block(m)
        if blk: viewer(blk)
        st.download_button("⬇ PDF report", report.pdf(name or "Unnamed", smi, m, d, works), "report.pdf")
        if st.button("💾 Add to atlas") and name and works:
            db.add(name, cat, smi, works, tags); st.success("Added"); st.rerun()

elif page == "Compare":
    st.title("Compare")
    sel = st.multiselect("Pick 2–4 molecules", list(df.name), default=list(df.name[:2]), max_selections=4)
    if len(sel) >= 2:
        sub = df[df.name.isin(sel)]
        st.dataframe(sub.set_index("name")[["works"] + list(PROPS)].T, use_container_width=True)
        fig = go.Figure()
        for _, r in sub.iterrows():
            v = [r[p] / df[p].max() if df[p].max() else 0 for p in PROPS]
            fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=list(PROPS.values()) + [list(PROPS.values())[0]], fill="toself", name=r["name"]))
        st.plotly_chart(fig.update_layout(template="plotly_dark", title="Normalised property radar"), use_container_width=True)
        for col, (_, r) in zip(st.columns(len(sel)), sub.iterrows()):
            col.image(chem.image(chem.parse(r["smiles"]), (300, 220)), caption=r["name"])

else:
    st.title("About")
    st.markdown("**Molecule Atlas** maps everyday molecules as a constellation and lets you search them by what they *work* for. "
                "Built with Streamlit, RDKit, Plotly, 3Dmol.js, SQLite and ReportLab.")
