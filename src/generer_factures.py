import json, random, os
from datetime import date, timedelta
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

fake = Faker("fr_FR")
random.seed(42)
OUT_PDF, OUT_GT = "data/factures", "data/verite_terrain"
os.makedirs(OUT_PDF, exist_ok=True)
os.makedirs(OUT_GT, exist_ok=True)

MOIS = ["janvier","février","mars","avril","mai","juin","juillet",
        "août","septembre","octobre","novembre","décembre"]

def fmt_montant(v, style):
    if style == 0:   # 1 234,50
        s = f"{v:,.2f}".replace(",", " ").replace(".", ",")
    elif style == 1: # 1234.50
        s = f"{v:.2f}"
    else:            # 1.234,50
        s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def fmt_date(d, style):
    if style == 0:
        return d.strftime("%d/%m/%Y")
    if style == 1:
        return f"{d.day} {MOIS[d.month-1]} {d.year}"
    return d.strftime("%Y-%m-%d")

def modele_1(c, f):  # classique, étiqueté
    c.setFont("Helvetica-Bold", 18); c.drawString(50, 780, f["fournisseur"])
    c.setFont("Helvetica", 12)
    c.drawString(50, 740, f"FACTURE N° {f['numero']}")
    c.drawString(50, 720, f"Date : {f['date_txt']}")
    c.drawString(50, 640, f"Total HT : {f['ht_txt']} EUR")
    c.drawString(50, 620, f"TVA {f['taux']}% : {f['tva_txt']} EUR")
    c.drawString(50, 600, f"Total TTC : {f['ttc_txt']} EUR")

def modele_2(c, f):  # tableau, "Net à payer"
    c.setFont("Helvetica-Bold", 16); c.drawString(300, 790, f["fournisseur"])
    c.setFont("Helvetica", 11)
    c.drawString(50, 750, f"Facture n° : {f['numero']}")
    c.drawString(50, 735, f"Date d'émission : {f['date_txt']}")
    c.rect(50, 560, 495, 120)
    c.drawString(60, 650, "Sous-total HT"); c.drawRightString(530, 650, f"{f['ht_txt']} EUR")
    c.drawString(60, 620, f"TVA ({f['taux']} %)"); c.drawRightString(530, 620, f"{f['tva_txt']} EUR")
    c.drawString(60, 590, "Net à payer TTC"); c.drawRightString(530, 590, f"{f['ttc_txt']} EUR")

def modele_3(c, f):  # compact, majuscules
    c.setFont("Courier-Bold", 14); c.drawString(50, 800, f["fournisseur"].upper())
    c.setFont("Courier", 11)
    c.drawString(50, 770, f"FACTURE N°{f['numero']}  DATE: {f['date_txt']}")
    c.drawString(50, 700, f"TOTAL HT: {f['ht_txt']}")
    c.drawString(50, 685, f"TVA {f['taux']}%: {f['tva_txt']}")
    c.drawString(50, 670, f"TOTAL TTC: {f['ttc_txt']}")

MODELES = [modele_1, modele_2, modele_3]

def generer(i, doublon_de=None, incoherent=False):
    if doublon_de:
        f = dict(doublon_de); f["fichier"] = f"facture_{i:02d}.pdf"
        f["doublon_de"] = doublon_de["fichier"]
    else:
        ht = round(random.uniform(50, 5000), 2)
        taux = random.choice([20, 10, 5.5])
        tva = round(ht * taux / 100, 2)
        ttc = round(ht + tva, 2)
        if incoherent:
            ttc = round(ttc + random.choice([10, 25, 100]), 2)
        d = date(2025, 1, 1) + timedelta(days=random.randint(0, 330))
        f = {
            "fichier": f"facture_{i:02d}.pdf",
            "fournisseur": fake.company(),
            "numero": f"FA-2025-{random.randint(1000, 9999)}",
            "date": d.isoformat(),
            "montant_ht": ht, "taux": taux, "tva": tva, "montant_ttc": ttc,
            "incoherent": incoherent, "doublon_de": None,
        }
    ms, ds = random.randint(0, 2), random.randint(0, 2)
    f["ht_txt"] = fmt_montant(f["montant_ht"], ms)
    f["tva_txt"] = fmt_montant(f["tva"], ms)
    f["ttc_txt"] = fmt_montant(f["montant_ttc"], ms)
    f["date_txt"] = fmt_date(date.fromisoformat(f["date"]), ds)
    f["modele"] = random.randint(0, 2)

    c = canvas.Canvas(os.path.join(OUT_PDF, f["fichier"]), pagesize=A4)
    MODELES[f["modele"]](c, f)
    c.save()
    with open(os.path.join(OUT_GT, f["fichier"].replace(".pdf", ".json")), "w", encoding="utf-8") as fh:
        json.dump(f, fh, ensure_ascii=False, indent=2)
    return f

if __name__ == "__main__":
    factures = []
    for i in range(1, 25):                     # 24 faktiora mahazatra
        factures.append(generer(i, incoherent=(i in (5, 12, 20))))
    for k, i in enumerate(range(25, 31)):      # 6 doublon
        factures.append(generer(i, doublon_de=factures[k * 3]))
    print(f"{len(factures)} factures générées dans {OUT_PDF}")