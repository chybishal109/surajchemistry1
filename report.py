import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
import chem


def pdf(name, smiles, m, d, works=""):
    buf = io.BytesIO()
    st = getSampleStyleSheet()
    img = io.BytesIO(); chem.image(m).save(img, format="PNG"); img.seek(0)
    rows = [["Property", "Value"], ["Formula", d["formula"]], ["Mol. weight", d["mw"]], ["LogP", d["logp"]],
            ["TPSA", d["tpsa"]], ["H-bond donors", d["hbd"]], ["H-bond acceptors", d["hba"]],
            ["Rotatable bonds", d["rotb"]], ["Rings", d["rings"]], ["Lipinski violations", d["violations"]]]
    t = Table(rows, colWidths=[200, 200])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#241833")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), .4, colors.grey)]))
    story = [Paragraph(f"Molecule Atlas - {name}", st["Title"]), Paragraph(f"SMILES: {smiles}", st["Normal"])]
    if works:
        story += [Spacer(1, 8), Paragraph(f"<b>Works:</b> {works}", st["Normal"])]
    story += [Spacer(1, 12), Image(img, 280, 200), Spacer(1, 12), t]
    SimpleDocTemplate(buf, pagesize=A4).build(story)
    return buf.getvalue()
