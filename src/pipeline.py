import sys, os
from extraction import lire_texte, extraire_champs
from db import enregistrer


def _coherent(ch):
    ht, tva, ttc = ch.get("montant_ht"), ch.get("tva"), ch.get("montant_ttc")
    return None not in (ht, tva, ttc) and abs(ht + tva - ttc) <= 0.02


def traiter(chemin, nom=None):
    nom = nom or os.path.basename(chemin)
    est_pdf = chemin.lower().endswith(".pdf")
    # PDF natif: tsy misy prétraitement; sary scan: misy prétraitement
    champs = extraire_champs(lire_texte(chemin, pretraitement=not est_pdf))
    if not _coherent(champs):
        # Fanandramana faharoa amin'ny fomba mifanohitra
        champs2 = extraire_champs(lire_texte(chemin, pretraitement=est_pdf))
        if _coherent(champs2):
            champs = champs2
    statut, anomalies = enregistrer(nom, champs)
    return {"fichier": nom, **champs, "statut": statut, "anomalies": anomalies}


if __name__ == "__main__":
    for chemin in sys.argv[1:]:
        print(traiter(chemin))