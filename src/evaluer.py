import json, time, glob, os, sys
from difflib import SequenceMatcher
from extraction import lire_texte, extraire_champs

CHAMPS = ["fournisseur", "numero", "date", "montant_ht", "tva", "montant_ttc"]


def ok(champ, pred, vrai):
    if pred is None:
        return False
    if champ == "fournisseur":
        return SequenceMatcher(None, str(pred).lower(), vrai.lower()).ratio() >= 0.9
    if champ in ("montant_ht", "tva", "montant_ttc"):
        return abs(pred - vrai) <= 0.01
    return pred == vrai


PRE = "--pre" in sys.argv
args = [a for a in sys.argv[1:] if a != "--pre"]
dossier = args[0] if args else "data/factures"
motif = "*.pdf" if dossier.rstrip("/").endswith("factures") else "*.jpg"
fichiers = sorted(glob.glob(os.path.join(dossier, motif)))
if not fichiers:
    sys.exit(f"Aucun fichier {motif} dans {dossier}")

bons = {c: 0 for c in CHAMPS}
temps, n = [], 0
for fichier in fichiers:
    base = os.path.splitext(os.path.basename(fichier))[0]
    gt = json.load(open(f"data/verite_terrain/{base}.json", encoding="utf-8"))
    t0 = time.time()
    try:
        pred = extraire_champs(lire_texte(fichier, pretraitement=PRE))
    except Exception as e:
        pred = {c: None for c in CHAMPS}
        print(f"[{base}] ERREUR: {e}")
    temps.append(time.time() - t0)
    n += 1
    for c in CHAMPS:
        if ok(c, pred[c], gt[c]):
            bons[c] += 1
        else:
            print(f"[{base}] {c}: obtenu={pred[c]!r} attendu={gt[c]!r}")

mode = "avec prétraitement" if PRE else "sans prétraitement"
print(f"\n=== Précision par champ ({dossier}, {n} fichiers, {mode}) ===")
for c in CHAMPS:
    print(f"{c:12s} {bons[c]}/{n} = {100*bons[c]/n:.1f}%")
print(f"Temps moyen: {sum(temps)/n:.2f} s / facture")