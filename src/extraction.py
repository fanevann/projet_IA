import re
import dateparser
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from pretraitement import pretraiter

MONTANT = r"(\d[\d \u202f.,]*\d)"


def lire_texte(chemin, pretraitement=False):
    """OCR: PDF na sary -> soratra."""
    if str(chemin).lower().endswith(".pdf"):
        pages = convert_from_path(chemin, dpi=300)
    else:
        pages = [Image.open(chemin).convert("RGB")]
    if pretraitement:
        pages = [Image.fromarray(pretraiter(p)) for p in pages]
    return "\n".join(pytesseract.image_to_string(p, lang="fra+eng") for p in pages)


def nettoyer_montant(brut):
    """'1 234,50' | '1234.50' | '1.234,50' -> float"""
    s = brut.replace(" ", "").replace("\u202f", "")
    if "," in s and "." in s:          # 1.234,50
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:                     # 1234,50
        s = s.replace(",", ".")
    return float(s)


def _montant_strict(pattern, texte):
    """Isa eo amin'ny andalana ihany misy ny label."""
    m = re.search(pattern + r"[ \t]*:?[ \t]*" + MONTANT, texte, re.I)
    return nettoyer_montant(m.group(1)) if m else None


def _montants_en_bloc(texte):
    """Fallback: isa 'xxx EUR' araka ny filaharana."""
    nombres = re.findall(MONTANT + r"[ \t]*EUR", texte)
    vals = [nettoyer_montant(x) for x in nombres]
    if len(vals) >= 3:
        return vals[0], vals[1], vals[2]
    return None, None, None


def extraire_champs(texte):
    champs = {}

    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    champs["fournisseur"] = lignes[0] if lignes else None

    m = re.search(r"(FA-\d{4}-\d{4})", texte)
    champs["numero"] = m.group(1) if m else None

    m = re.search(
        r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+[A-Za-zéèûôî]+\s+\d{4})",
        texte,
    )
    champs["date"] = None
    if m:
        d = dateparser.parse(m.group(1), languages=["fr"],
                             settings={"DATE_ORDER": "DMY"})
        champs["date"] = d.date().isoformat() if d else None

    ht = _montant_strict(r"(?:Total|Sous-total)\s+HT", texte)
    tva = _montant_strict(r"TVA\s*\(?\s*[\d.,]+\s*%\s*\)?", texte)
    ttc = _montant_strict(r"(?:Total|Net\s+[àa]\s+payer)\s+T[TI]C", texte)

    if ht is None or tva is None or ttc is None:
        bht, btva, bttc = _montants_en_bloc(texte)
        ht = ht if ht is not None else bht
        tva = tva if tva is not None else btva
        ttc = ttc if ttc is not None else bttc

    champs["montant_ht"], champs["tva"], champs["montant_ttc"] = ht, tva, ttc
    return champs


if __name__ == "__main__":
    import sys
    chemin = sys.argv[1] if len(sys.argv) > 1 else "data/factures/facture_01.pdf"
    print(extraire_champs(lire_texte(chemin)))