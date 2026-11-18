import os, sys, json
import pandas as pd
import streamlit as st
from pdf2image import convert_from_path
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from db import conn
from pipeline import traiter

DOSSIER_DEPOTS = "data/depots"
os.makedirs(DOSSIER_DEPOTS, exist_ok=True)

st.set_page_config(page_title="Factures IA", page_icon="🧾", layout="wide")

# ================= Etat de session =================
st.session_state.setdefault("lang", "fr")
st.session_state.setdefault("dark", False)
st.session_state.setdefault("page", "dash")
lang = st.session_state["lang"]

# ================= Traductions =================
TR = {
    "fr": {
        "app": "Factures IA", "tagline": "OCR · Extraction · Validation",
        "nav_dash": "📊 Tableau de bord", "nav_valid": "✍️ Validation",
        "nav_depot": "📤 Dépôt", "compose": "Nouveau dépôt", "theme": "Mode sombre",
        "dash_title": "Tableau de bord",
        "empty": "Aucune facture en base. Déposez une facture dans « Dépôt ».",
        "k_total": "Factures traitées", "k_valid": "Valides",
        "k_check": "À vérifier", "k_dup": "Doublons",
        "status": "Statut", "search": "Rechercher (fournisseur, numéro, fichier)",
        "shown": "{n} facture(s) affichée(s)", "export": "⬇️ Exporter en CSV",
        "c_file": "Fichier", "c_supplier": "Fournisseur", "c_number": "N° facture",
        "c_date": "Date", "c_fixed": "Corrigé",
        "s_valide": "🟢 Valide", "s_a_verifier": "🟠 À vérifier",
        "s_doublon": "🔴 Doublon", "s_rejete": "⚫ Rejeté",
        "valid_title": "Validation humaine",
        "all_done": " Tout est à jour : aucune facture en attente.",
        "n_pending": "{n} facture(s) en attente",
        "orig": "Document original", "no_preview": "Aperçu indisponible.",
        "extracted": "Données extraites", "supplier": "Fournisseur",
        "number": "Numéro de facture", "date": "Date (AAAA-MM-JJ)",
        "ht": "Montant HT (€)", "tva": "TVA (€)", "ttc": "Montant TTC (€)",
        "gap": "HT + TVA = {s:.2f} € · écart de {e:+.2f} € avec le TTC",
        "coherent": "Montants cohérents ✓",
        "btn_ok": "✅ Valider", "btn_ko": "🗑️ Rejeter",
        "help_ok": "Désactivé tant que les montants sont incohérents",
        "validated": "{f} validée", "rejected": "{f} rejetée",
        "a_incoh": "Montants incohérents : HT + TVA ≠ TTC",
        "a_dup": "Doublon probable de la facture n° {n} en base",
        "a_missing": "Champ non détecté : {n}",
        "depot_title": "Déposer une facture",
        "depot_cap": "Formats acceptés : PDF, PNG, JPG. Traitement automatique.",
        "drop": "Glissez une facture ici", "run": " Lancer le traitement",
        "spin": "OCR et extraction en cours...",
        "saved": "Facture enregistrée automatiquement.",
        "queued": "Facture envoyée dans la file de validation.",
    },
    "en": {
        "app": "Invoices AI", "tagline": "OCR · Extraction · Review",
        "nav_dash": "Dashboard", "nav_valid": " Review",
        "nav_depot": "Upload", "compose": "New upload", "theme": "Dark mode",
        "dash_title": "Dashboard",
        "empty": "No invoice in the database. Upload one in « Upload ».",
        "k_total": "Processed invoices", "k_valid": "Valid",
        "k_check": "To check", "k_dup": "Duplicates",
        "status": "Status", "search": "Search (supplier, number, file)",
        "shown": "{n} invoice(s) shown", "export": "⬇️ Export as CSV",
        "c_file": "File", "c_supplier": "Supplier", "c_number": "Invoice no.",
        "c_date": "Date", "c_fixed": "Corrected",
        "s_valide": "🟢 Valid", "s_a_verifier": "🟠 To check",
        "s_doublon": "🔴 Duplicate", "s_rejete": "⚫ Rejected",
        "valid_title": "Human review",
        "all_done": " All done: no invoice waiting.",
        "n_pending": "{n} invoice(s) waiting",
        "orig": "Original document", "no_preview": "Preview unavailable.",
        "extracted": "Extracted data", "supplier": "Supplier",
        "number": "Invoice number", "date": "Date (YYYY-MM-DD)",
        "ht": "Net amount (€)", "tva": "VAT (€)", "ttc": "Gross amount (€)",
        "gap": "Net + VAT = {s:.2f} € · gap of {e:+.2f} € with gross amount",
        "coherent": "Amounts are consistent ✓",
        "btn_ok": " Approve", "btn_ko": " Reject",
        "help_ok": "Disabled while amounts are inconsistent",
        "validated": "{f} approved", "rejected": "{f} rejected",
        "a_incoh": "Inconsistent amounts: net + VAT ≠ gross",
        "a_dup": "Probable duplicate of invoice no. {n} in database",
        "a_missing": "Field not detected: {n}",
        "depot_title": "Upload an invoice",
        "depot_cap": "Accepted formats: PDF, PNG, JPG. Automatic processing.",
        "drop": "Drop an invoice here", "run": " Start processing",
        "spin": "OCR and extraction in progress...",
        "saved": "Invoice saved automatically.",
        "queued": "Invoice sent to the review queue.",
    },
}


def t(key, **kw):
    s = TR[lang][key]
    return s.format(**kw) if kw else s


# ================= Données =================
def charger():
    c = conn()
    df = pd.read_sql_query("SELECT * FROM factures ORDER BY id DESC", c)
    c.close()
    return df


def executer(sql, params):
    c = conn()
    c.execute(sql, params)
    c.commit()
    c.close()


def trouver_fichier(nom):
    for d in ("data/factures", DOSSIER_DEPOTS):
        p = os.path.join(d, nom)
        if os.path.exists(p):
            return p
    return None


@st.cache_data(show_spinner=False)
def apercu(chemin):
    if chemin.lower().endswith(".pdf"):
        return convert_from_path(chemin, dpi=110, first_page=1, last_page=1)[0]
    return Image.open(chemin)


def statut_txt(code):
    return t(f"s_{code}")


def libelle_anomalie(code):
    if code.startswith("doublon_de:"):
        return t("a_dup", n=code.split(":")[1])
    if code.startswith("champ_manquant:"):
        return t("a_missing", n=code.split(":")[1])
    if code == "incoherence_montants":
        return t("a_incoh")
    return code


def anomalies_liste(brut):
    try:
        return json.loads(brut) if brut else []
    except Exception:
        return []


def flash(msg, icone="✅"):
    st.session_state["flash"] = (msg, icone)


def aller(p):
    st.session_state["page"] = p


if "flash" in st.session_state:
    msg, icone = st.session_state.pop("flash")
    st.toast(msg, icon=icone)

df = charger()
nb_attente = int(df.statut.isin(["a_verifier", "doublon"]).sum()) if not df.empty else 0

# ================= CSS : thème + style Gmail + responsive =================
if st.session_state["dark"]:
    bg, bg2, fg, field, border, accent = "#0e1117", "#161b22", "#fafafa", "#1c2128", "#30363d", "#1f3a5f"
else:
    bg, bg2, fg, field, border, accent = "#ffffff", "#f6f8fc", "#1f2430", "#ffffff", "#d5d9e2", "#d3e3fd"

st.markdown(f"""
<style>
.stApp, [data-testid="stHeader"] {{ background-color:{bg}; color:{fg}; }}
[data-testid="stSidebar"] {{ background-color:{bg2}; border-right:none; }}
.stApp h1,.stApp h2,.stApp h3,.stApp label,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
[data-testid="stMetricValue"],[data-testid="stMetricLabel"],
[data-testid="stCaptionContainer"] {{ color:{fg} !important; }}
input, textarea, [data-baseweb="select"] > div {{
  background-color:{field} !important; color:{fg} !important;
  border-color:{border} !important; }}
[data-testid="stFileUploaderDropzone"] {{ background:{bg2}; border:1px dashed {border}; }}
[data-testid="stMetric"] {{ background:{bg2}; border:1px solid {border};
  border-radius:12px; padding:14px 16px; }}

/* Boutons principaux (zone centrale) */
.stApp button[kind="primary"] p,
.stApp [data-testid="stBaseButton-primary"] p {{ color:#fff !important; }}
button[kind="primary"], [data-testid="stBaseButton-primary"] {{ border-radius:10px; }}

/* ---- Sidebar style Gmail ---- */
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {{
  width:100%; justify-content:flex-start; text-align:left;
  border:none; border-radius:0 28px 28px 0; padding:10px 18px;
  background:transparent; box-shadow:none; }}
[data-testid="stSidebar"] button p {{ color:{fg} !important; font-weight:500; }}
[data-testid="stSidebar"] button:hover {{ background:{border}88; }}
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
  background:{accent}; }}
[data-testid="stSidebar"] button[kind="primary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p {{
  color:{fg} !important; font-weight:700; }}

/* ---- Barre du haut : reste sur une ligne ---- */
div[data-testid="stHorizontalBlock"]:has(.topbar-marker) {{
  flex-wrap:nowrap !important; align-items:center;
  border-bottom:1px solid {border}; padding-bottom:6px; margin-bottom:12px; }}
div[data-testid="stHorizontalBlock"]:has(.topbar-marker) > div {{ min-width:0 !important; }}
.topbar-title {{ font-weight:700; font-size:1.05rem; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; color:{fg}; }}

/* ---- Responsive ---- */
img {{ max-width:100%; height:auto; }}
@media (max-width: 768px) {{
  .block-container {{ padding:1rem 0.8rem 3rem 0.8rem !important; }}
  h1, h2 {{ font-size:1.35rem !important; }}
  [data-testid="stMetric"] {{ padding:10px 12px; }}
  [data-testid="stMetricValue"] {{ font-size:1.4rem !important; }}
  .topbar-title {{ font-size:0.95rem; }}
}}
</style>
""", unsafe_allow_html=True)

# ================= Sidebar (style Gmail) =================
st.sidebar.markdown(f"### 🧾 {t('app')}")
st.sidebar.caption(t("tagline"))

st.sidebar.button("➕  " + t("compose"), key="compose",
                  on_click=aller, args=("depot",), type="primary")
st.sidebar.write("")

items = [
    ("dash", t("nav_dash"), 0),
    ("valid", t("nav_valid"), nb_attente),
    ("depot", t("nav_depot"), 0),
]
for cle, label, badge in items:
    texte = f"{label}   ({badge})" if badge else label
    st.sidebar.button(
        texte, key=f"nav_{cle}", on_click=aller, args=(cle,),
        type="primary" if st.session_state["page"] == cle else "secondary",
    )

st.sidebar.divider()
st.sidebar.caption("v1.0 · M1 · Tesseract + OpenCV + SQLite")

page = st.session_state["page"]

# ================= Barre du haut : langue + thème à droite =================
c_titre, c_lang, c_theme = st.columns([5, 2.4, 1.6], vertical_alignment="center")
c_titre.markdown(
    f"<span class='topbar-marker'></span><div class='topbar-title'>🧾 {t('app')}</div>",
    unsafe_allow_html=True,
)
c_lang.radio("lang", ["fr", "en"], key="lang", horizontal=True,
             label_visibility="collapsed",
             format_func=lambda x: {"fr": "🇫🇷 FR", "en": "🇬🇧 EN"}[x])
c_theme.toggle("🌙", key="dark", help=t("theme"))

# ================= Page 1 : Tableau de bord =================
if page == "dash":
    st.header(t("dash_title"))
    if df.empty:
        st.info(t("empty"))
    else:
        total = len(df)
        valides = int((df.statut == "valide").sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("k_total"), total)
        c2.metric(t("k_valid"), valides, f"{100 * valides / total:.0f} %")
        c3.metric(t("k_check"), int((df.statut == "a_verifier").sum()))
        c4.metric(t("k_dup"), int((df.statut == "doublon").sum()))

        st.divider()
        f1, f2 = st.columns([2, 3])
        codes = ["valide", "a_verifier", "doublon", "rejete"]
        choix = f1.multiselect(t("status"), codes, default=codes,
                               format_func=statut_txt)
        recherche = f2.text_input(t("search"), "")

        vue = df[df.statut.isin(choix)].copy()
        if recherche:
            m = (vue.fournisseur.fillna("").str.contains(recherche, case=False)
                 | vue.numero.fillna("").str.contains(recherche, case=False)
                 | vue.fichier.fillna("").str.contains(recherche, case=False))
            vue = vue[m]

        vue["statut"] = vue.statut.map(statut_txt)
        vue["corrige_par_humain"] = vue.corrige_par_humain.astype(bool)
        st.caption(t("shown", n=len(vue)))
        st.dataframe(
            vue[["fichier", "fournisseur", "numero", "date", "montant_ht", "tva",
                 "montant_ttc", "statut", "corrige_par_humain"]],
            width="stretch", hide_index=True,
            column_config={
                "fichier": t("c_file"), "fournisseur": t("c_supplier"),
                "numero": t("c_number"), "date": t("c_date"),
                "montant_ht": st.column_config.NumberColumn("HT", format="%.2f €"),
                "tva": st.column_config.NumberColumn("TVA", format="%.2f €"),
                "montant_ttc": st.column_config.NumberColumn("TTC", format="%.2f €"),
                "statut": t("status"),
                "corrige_par_humain": st.column_config.CheckboxColumn(t("c_fixed")),
            },
        )
        st.download_button(t("export"), vue.to_csv(index=False).encode("utf-8"),
                           "factures.csv", "text/csv")

# ================= Page 2 : Validation =================
elif page == "valid":
    st.header(t("valid_title"))
    a_traiter = df[df.statut.isin(["a_verifier", "doublon"])] if not df.empty else df
    if a_traiter.empty:
        st.success(t("all_done"))
    else:
        sel = st.selectbox(t("n_pending", n=len(a_traiter)), a_traiter.fichier.tolist())
        r = a_traiter[a_traiter.fichier == sel].iloc[0]
        rid = int(r.id)

        for code in anomalies_liste(r.anomalies):
            st.warning(libelle_anomalie(code))

        gauche, droite = st.columns([1, 1], gap="large")
        with gauche:
            st.subheader(t("orig"))
            chemin = trouver_fichier(r.fichier)
            if chemin:
                st.image(apercu(chemin), width="stretch")
            else:
                st.info(t("no_preview"))

        with droite:
            st.subheader(t("extracted"))
            f = st.text_input(t("supplier"), r.fournisseur or "", key=f"f{rid}")
            n = st.text_input(t("number"), r.numero or "", key=f"n{rid}")
            d = st.text_input(t("date"), r.date or "", key=f"d{rid}")
            m1, m2, m3 = st.columns(3)
            ht = m1.number_input(t("ht"), value=float(r.montant_ht or 0),
                                 step=0.01, format="%.2f", key=f"ht{rid}")
            tva = m2.number_input(t("tva"), value=float(r.tva or 0),
                                  step=0.01, format="%.2f", key=f"tva{rid}")
            ttc = m3.number_input(t("ttc"), value=float(r.montant_ttc or 0),
                                  step=0.01, format="%.2f", key=f"ttc{rid}")

            ecart = ht + tva - ttc
            if abs(ecart) > 0.02:
                st.error(t("gap", s=ht + tva, e=ecart))
            else:
                st.success(t("coherent"))

            b1, b2 = st.columns(2)
            if b1.button(t("btn_ok"), type="primary", width="stretch",
                         disabled=abs(ecart) > 0.02, help=t("help_ok")):
                executer(
                    """UPDATE factures SET fournisseur=?, numero=?, date=?, montant_ht=?,
                       tva=?, montant_ttc=?, statut='valide', corrige_par_humain=1
                       WHERE id=?""",
                    (f, n, d, ht, tva, ttc, rid),
                )
                flash(t("validated", f=sel))
                st.rerun()
            if b2.button(t("btn_ko"), width="stretch"):
                executer("UPDATE factures SET statut='rejete' WHERE id=?", (rid,))
                flash(t("rejected", f=sel), "⚫")
                st.rerun()

# ================= Page 3 : Dépôt =================
else:
    st.header(t("depot_title"))
    st.caption(t("depot_cap"))
    fichier = st.file_uploader(t("drop"), type=["pdf", "png", "jpg", "jpeg"])
    if fichier and st.button(t("run"), type="primary"):
        chemin = os.path.join(DOSSIER_DEPOTS, fichier.name)
        with open(chemin, "wb") as fh:
            fh.write(fichier.getbuffer())
        with st.spinner(t("spin")):
            res = traiter(chemin, nom=fichier.name)

        st.subheader(statut_txt(res["statut"]))
        for code in res["anomalies"]:
            st.warning(libelle_anomalie(code))
        if res["statut"] == "valide":
            st.success(t("saved"))
        else:
            st.info(t("queued"))

        a, b, c = st.columns(3)
        a.metric("HT", f"{res['montant_ht'] or 0:.2f} €")
        b.metric("TVA", f"{res['tva'] or 0:.2f} €")
        c.metric("TTC", f"{res['montant_ttc'] or 0:.2f} €")
        st.write(f"**{t('supplier')} :** {res['fournisseur']}  \n"
                 f"**N° :** {res['numero']}  \n**Date :** {res['date']}")