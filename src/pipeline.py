import sys, os
from extraction import lire_texte, extraire_champs
from db import enregistrer


def traiter(chemin, pretraitement=True):
    champs = extraire_champs(lire_texte(chemin, pretraitement=pretraitement))
    statut, anomalies = enregistrer(os.path.basename(chemin), champs)
    return {"fichier": os.path.basename(chemin), **champs,
            "statut": statut, "anomalies": anomalies}


if __name__ == "__main__":
    for chemin in sys.argv[1:]:
        print(traiter(chemin))