import os, shutil, tempfile
from fastapi import FastAPI, UploadFile, File
from pipeline import traiter
from db import conn

app = FastAPI(title="API Factures")


@app.get("/")
def sante():
    return {"status": "ok"}


@app.post("/traiter")
def traiter_facture(fichier: UploadFile = File(...)):
    suffixe = os.path.splitext(fichier.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffixe) as tmp:
        shutil.copyfileobj(fichier.file, tmp)
    try:
        return traiter(tmp.name, nom=fichier.filename)
    finally:
        os.remove(tmp.name)


@app.get("/factures")
def lister(statut: str | None = None):
    c = conn()
    if statut:
        rows = c.execute("SELECT * FROM factures WHERE statut=?", (statut,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM factures").fetchall()
    c.close()
    return [dict(r) for r in rows]