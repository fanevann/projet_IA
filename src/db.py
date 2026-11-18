import sqlite3, json
from datetime import datetime

DB = "data/factures.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS factures (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fichier TEXT, fournisseur TEXT, numero TEXT, date TEXT,
  montant_ht REAL, tva REAL, montant_ttc REAL,
  statut TEXT, anomalies TEXT, date_traitement TEXT,
  corrige_par_humain INTEGER DEFAULT 0
);
"""


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute(SCHEMA)
    return c


def verifier(champs, c):
    """Mamerina (statut, anomalies)."""
    anomalies = []
    for k in ("fournisseur", "numero", "date", "montant_ht", "tva", "montant_ttc"):
        if champs.get(k) is None:
            anomalies.append(f"champ_manquant:{k}")

    ht, tva, ttc = champs.get("montant_ht"), champs.get("tva"), champs.get("montant_ttc")
    if None not in (ht, tva, ttc) and abs(ht + tva - ttc) > 0.02:
        anomalies.append("incoherence_montants")

    d = c.execute(
        "SELECT id FROM factures WHERE numero=? AND fournisseur=? AND montant_ttc=?",
        (champs.get("numero"), champs.get("fournisseur"), ttc),
    ).fetchone()
    if d:
        anomalies.append(f"doublon_de:{d['id']}")

    if any(a.startswith("doublon") for a in anomalies):
        statut = "doublon"
    elif anomalies:
        statut = "a_verifier"
    else:
        statut = "valide"
    return statut, anomalies


def enregistrer(fichier, champs):
    c = conn()
    statut, anomalies = verifier(champs, c)
    c.execute(
        """INSERT INTO factures (fichier,fournisseur,numero,date,montant_ht,tva,
           montant_ttc,statut,anomalies,date_traitement)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (fichier, champs.get("fournisseur"), champs.get("numero"), champs.get("date"),
         champs.get("montant_ht"), champs.get("tva"), champs.get("montant_ttc"),
         statut, json.dumps(anomalies), datetime.now().isoformat(timespec="seconds")),
    )
    c.commit()
    c.close()
    return statut, anomalies