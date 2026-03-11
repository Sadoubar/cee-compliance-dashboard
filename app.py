# ============================================================================
# APPLICATION STREAMLIT - CATALOGUE CEE
# ============================================================================
# Dashboard interactif pour le suivi des fiches CEE
# - Recherche de fiches
# - Statistiques en temps réel
# - Suivi des modifications et abrogations
# - Scraping du site officiel pour données à jour
# ============================================================================

import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import calendar
import requests
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================

st.set_page_config(
    page_title="📊 Catalogue CEE - Green Prime",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLES CSS PERSONNALISÉS
# ============================================================================

st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* Global Styles */
    .stApp {
        font-family: 'Outfit', sans-serif;
    }

    /* Header Style */
    .main-header {
        background: linear-gradient(135deg, #1a5f2a 0%, #2d8f4e 50%, #3cb371 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(26, 95, 42, 0.3);
    }

    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .kpi-card.green { border-left-color: #2d8f4e; }
    .kpi-card.orange { border-left-color: #ff8c00; }
    .kpi-card.red { border-left-color: #dc3545; }
    .kpi-card.blue { border-left-color: #0066cc; }

    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        margin: 0;
    }

    .kpi-label {
        font-size: 0.95rem;
        color: #666;
        margin: 0.3rem 0 0 0;
        font-weight: 500;
    }

    /* Alert Box */
    .alert-box {
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .alert-box.warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
        border: 1px solid #ffc107;
    }

    .alert-box.danger {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #dc3545;
    }

    .alert-box.success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
    }

    .alert-box.info {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #17a2b8;
    }

    /* Section Headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1a5f2a;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #2d8f4e;
    }

    /* Fiche Card - Compact pour 2 colonnes */
    .fiche-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 4px solid #2d8f4e;
        min-height: 100px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .fiche-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .fiche-ref {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
        color: #1a5f2a;
    }

    .fiche-title {
        font-size: 0.85rem;
        color: #555;
        margin-top: 0.4rem;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }

    /* Badge - Compact */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }

    .badge.abrogation { background: #dc3545; color: white; }
    .badge.modification { background: #ff8c00; color: white; }
    .badge.future { background: #6f42c1; color: white; }
    .badge.passee { background: #6c757d; color: white; }

    /* Table Styles */
    .dataframe {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        font-size: 0.9rem;
        margin-top: 3rem;
        border-top: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FONCTIONS D'EXTRACTION ET D'ANALYSE
# ============================================================================

@st.cache_data(ttl=3600)
def charger_et_extraire_donnees():
    """Charge et extrait les données du PDF"""
    import pdfplumber
    import requests

    PDF_URL = "https://www.ecologie.gouv.fr/sites/default/files/documents/Catalogue%20fiches%20version%20actualis%C3%A9e%2077%C3%A8me%20arr%C3%AAt%C3%A9.pdf"

    # Télécharger le PDF
    response = requests.get(PDF_URL, timeout=120)
    pdf_content = response.content

    # Sauvegarder temporairement
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        f.write(pdf_content)
        pdf_path = f.name

    # Extraction
    all_dfs = []
    max_columns = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table:
                        df_table = pd.DataFrame(table)
                        if len(df_table.columns) > max_columns:
                            max_columns = len(df_table.columns)
                        all_dfs.append(df_table)

    # Normalisation
    for df in all_dfs:
        while len(df.columns) < max_columns:
            df[len(df.columns)] = None

    df = pd.concat(all_dfs, ignore_index=True)

    # Nettoyage
    df = df.dropna(how='all')
    mask = df.astype(str).apply(
        lambda x: x.str.contains("Catalogue|Intitulé|N° de référence", case=False, na=False)).any(axis=1)
    df = df[~mask]
    mask_valid = df.iloc[:, 1].astype(str).str.match(r'^[A-Z]{3,4}-[A-Z]{2}-\d{3}', na=False)
    df = df[mask_valid].reset_index(drop=True)

    # Renommer colonnes
    df.columns = ['Intitule', 'Reference'] + [f'Col_{i}' for i in range(2, len(df.columns))]

    # Ajouter Secteur
    secteurs_noms = {
        'AGRI': 'Agriculture',
        'BAR': 'Bât. Résidentiel',
        'BAT': 'Bât. Tertiaire',
        'IND': 'Industrie',
        'RES': 'Réseaux',
        'TRA': 'Transport'
    }
    df['Secteur'] = df['Reference'].apply(lambda x: secteurs_noms.get(str(x).split('-')[0], ''))

    return df, pdf_content


def extraire_abrogation(texte):
    """Extrait la date d'abrogation avec décodage des textes entrelacés"""
    if pd.isna(texte):
        return None

    texte = str(texte)

    # Pattern normal
    match = re.search(r'[Aa]brog[ée]+[e]?\s*au\s*[\r\n\s]*(\d{2}/\d{2}/\d{4})', texte, re.DOTALL)
    if match:
        return match.group(1)

    # Pattern avec tiret
    match = re.search(r'[Aa]brog[ée]+[e]?\s*au\s*[\r\n\s]*(\d{2}-\d{2}-\d{4})', texte, re.DOTALL)
    if match:
        return match.group(1).replace('-', '/')

    # Texte ENTRELACÉ (ex: "A0b1r/o0g8/é2e0 2a5u")
    if re.search(r'[Aa].*\d.*[Bb].*\d.*[Rr].*[Oo].*[Gg]', texte, re.IGNORECASE):
        chiffres = ''.join(re.findall(r'[\d/]', texte))
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', chiffres)
        if date_match:
            return date_match.group(1)

    # Contient "brog" et des chiffres
    if 'brog' in texte.lower():
        chiffres = ''.join(re.findall(r'[\d/]', texte))
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', chiffres)
        if date_match:
            return date_match.group(1)

    return None


def extraire_modification(texte):
    """Extrait les modifications (versions) d'une cellule"""
    if pd.isna(texte):
        return None

    texte = str(texte).replace('\r', ' ').replace('\n', ' ')
    match = re.search(r'(A\d+-\d+)\s*(?:applicable\s*(?:au|du)?\s*)?(\d{2}[-/]\d{2}[-/]\d{4})', texte)
    if match:
        return {
            'version': match.group(1),
            'date': match.group(2).replace('-', '/')
        }
    return None


@st.cache_data
def analyser_catalogue(_df):
    """Analyse le catalogue pour extraire abrogations et modifications"""
    df = _df.copy()

    abrogations = []
    modifications = []

    for idx in range(len(df)):
        row = df.iloc[idx]
        ref = str(row['Reference'])
        intitule = str(row['Intitule'])[:100] if row['Intitule'] else ''
        secteur = row['Secteur']

        for col_idx in range(2, len(row) - 1):  # -1 pour exclure Secteur
            cell = row.iloc[col_idx]

            # Abrogation
            date_abrog = extraire_abrogation(cell)
            if date_abrog:
                abrogations.append({
                    'Reference': ref,
                    'Intitule': intitule,
                    'Secteur': secteur,
                    'Date': date_abrog,
                    'Type': 'Abrogation'
                })

            # Modification
            mod = extraire_modification(cell)
            if mod:
                modifications.append({
                    'Reference': ref,
                    'Intitule': intitule,
                    'Secteur': secteur,
                    'Version': mod['version'],
                    'Date': mod['date'],
                    'Type': 'Modification'
                })

    # Créer DataFrames
    df_abrog = pd.DataFrame(abrogations).drop_duplicates(subset=['Reference', 'Date'])
    df_modif = pd.DataFrame(modifications).drop_duplicates()

    # Ajouter colonnes de date
    if not df_abrog.empty:
        df_abrog['DateObj'] = pd.to_datetime(df_abrog['Date'], format='%d/%m/%Y', errors='coerce')
        df_abrog['Statut'] = df_abrog['DateObj'].apply(
            lambda x: 'FUTURE' if pd.notna(x) and x >= datetime.now() else 'PASSEE'
        )

    if not df_modif.empty:
        df_modif['DateObj'] = pd.to_datetime(df_modif['Date'], format='%d/%m/%Y', errors='coerce')
        df_modif['Statut'] = df_modif['DateObj'].apply(
            lambda x: 'FUTURE' if pd.notna(x) and x >= datetime.now() else 'PASSEE'
        )

    return df_abrog, df_modif


def get_mois_nom(mois):
    """Retourne le nom du mois en français"""
    mois_fr = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return mois_fr.get(mois, '')


@st.cache_data(ttl=1800)  # Cache 30 minutes
def scraper_fiches_web():
    """
    Scrape la page du ministère pour récupérer les fiches CEE à jour
    URL: https://www.ecologie.gouv.fr/politiques-publiques/operations-standardisees-deconomies-denergie
    """
    URL = "https://www.ecologie.gouv.fr/politiques-publiques/operations-standardisees-deconomies-denergie"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL, headers=headers, timeout=120)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Chercher tous les liens de téléchargement
        links = soup.find_all('a', class_='fr-link--download')

        fiches = []

        # Pattern pour extraire: REF : Intitulé vXX-X à compter du DD-MM-YYYY
        pattern = r'([A-Z]{3,4}-[A-Z]{2}-\d{3}(?:-SE)?)\s*[:\s]*(.+?)\s*v([A-Z]?\d+[-\.]?\d*)\s*à compter du\s*(\d{2}[-/]\d{2}[-/]\d{4})'

        for link in links:
            title = link.get('title', '') or link.text
            href = link.get('href', '')

            # Extraire les informations
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                ref = match.group(1).upper()
                intitule = match.group(2).strip()
                # Nettoyer l'intitulé
                intitule = re.sub(r'\s+', ' ', intitule)
                intitule = intitule.replace('.pdf', '').strip()

                version = f"v{match.group(3)}"
                date_str = match.group(4).replace('-', '/')

                # Parser la date
                try:
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                except:
                    date_obj = None

                # Extraire le secteur
                secteur_code = ref.split('-')[0]
                secteurs_noms = {
                    'AGRI': 'Agriculture',
                    'BAR': 'Bât. Résidentiel',
                    'BAT': 'Bât. Tertiaire',
                    'IND': 'Industrie',
                    'RES': 'Réseaux',
                    'TRA': 'Transport'
                }
                secteur = secteurs_noms.get(secteur_code, secteur_code)

                # Extraire l'année d'application
                annee = date_obj.year if date_obj else None

                fiches.append({
                    'Reference': ref,
                    'Intitule': intitule,
                    'Version': version,
                    'Date_Application': date_str,
                    'DateObj': date_obj,
                    'Annee': annee,
                    'Secteur': secteur,
                    'URL': href if href.startswith('http') else f"https://www.ecologie.gouv.fr{href}"
                })

        # Créer DataFrame
        df = pd.DataFrame(fiches)

        # Garder uniquement la version la plus récente par fiche
        if not df.empty:
            df = df.sort_values(['Reference', 'DateObj'], ascending=[True, False])
            df = df.drop_duplicates(subset='Reference', keep='first')

        return df, None

    except Exception as e:
        return pd.DataFrame(), str(e)


# ============================================================================
# ÉCRAN DE CHARGEMENT
# ============================================================================

# Afficher l'écran de chargement
loading_placeholder = st.empty()

with loading_placeholder.container():
    st.markdown("""
    <style>
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
    @keyframes glow { 0%, 100% { text-shadow: 0 0 10px #4ade80; } 50% { text-shadow: 0 0 30px #4ade80, 0 0 50px #4ade80; } }
    .loader-box {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        min-height: 500px; background: linear-gradient(135deg, #0a1a0f 0%, #0d2818 50%, #051a0a 100%);
        border-radius: 20px; padding: 3rem; margin: 2rem 0; position: relative;
        box-shadow: 0 0 50px rgba(0,0,0,0.5), inset 0 0 80px rgba(74,222,128,0.03);
    }
    .loader-icon { font-size: 4rem; animation: pulse 2s ease-in-out infinite; margin-bottom: 1rem; }
    .loader-spinner {
        width: 80px; height: 80px; border: 3px solid rgba(74,222,128,0.2);
        border-top-color: #4ade80; border-radius: 50%; animation: spin 1s linear infinite;
        position: absolute; top: 50%; left: 50%; margin: -100px 0 0 -40px;
    }
    .loader-title {
        font-family: Georgia, serif; font-size: 1.8rem; color: #4ade80; letter-spacing: 6px;
        text-transform: uppercase; margin: 1rem 0; animation: glow 2s ease-in-out infinite;
    }
    .loader-sub { color: rgba(255,255,255,0.5); font-size: 0.9rem; letter-spacing: 2px; margin-top: 0.5rem; }
    .loader-line { width: 120px; height: 2px; background: linear-gradient(90deg, transparent, #4ade80, transparent); margin: 1rem 0; }
    .loader-dots { display: flex; gap: 8px; margin-top: 1.5rem; }
    .loader-dot { width: 8px; height: 8px; background: #4ade80; border-radius: 50%; animation: pulse 1.5s ease-in-out infinite; }
    .loader-dot:nth-child(2) { animation-delay: 0.2s; }
    .loader-dot:nth-child(3) { animation-delay: 0.4s; }
    .loader-credit {
        position: absolute; bottom: 20px; right: 25px; text-align: right;
        font-size: 0.75rem; color: rgba(255,255,255,0.4);
    }
    .loader-credit a { color: #4ade80; text-decoration: none; font-weight: 500; }
    .loader-version { position: absolute; top: 15px; left: 20px; font-size: 0.7rem; color: rgba(74,222,128,0.3); }
    </style>
    <div class="loader-box">
        <div class="loader-spinner"></div>
        <div class="loader-icon">🌿</div>
        <div class="loader-title">Catalogue CEE</div>
        <div class="loader-line"></div>
        <div class="loader-sub">Green Prime • Pôle Conformité</div>
        <div class="loader-dots">
            <div class="loader-dot"></div>
            <div class="loader-dot"></div>
            <div class="loader-dot"></div>
        </div>
        <div class="loader-version">v2.0 // 77ème arrêté</div>
        <div class="loader-credit">
            Développé par<br>
            <a href="https://www.linkedin.com/in/sadou-barry-881868164/" target="_blank">✦ Sadou BARRY ✦</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# CHARGEMENT DES DONNÉES
# ============================================================================

try:
    df_catalogue, pdf_content = charger_et_extraire_donnees()
    df_abrogations, df_modifications = analyser_catalogue(df_catalogue)
    data_loaded = True
except Exception as e:
    loading_placeholder.empty()
    st.error(f"❌ Erreur de chargement: {e}")
    data_loaded = False

if not data_loaded:
    st.stop()

# Effacer l'écran de chargement
loading_placeholder.empty()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 🌿 **Green Prime**")
    st.markdown("*Pôle Conformité CEE*")
    st.markdown("---")

    # Date de référence
    st.markdown("#### 📅 Date de référence")
    date_ref = st.date_input(
        "Afficher les changements à partir de:",
        value=datetime.now().date(),
        help="Sélectionnez une date pour voir les modifications et abrogations"
    )

    st.markdown("---")

    # Filtres
    st.markdown("#### 🔍 Filtres")

    secteurs = ['Tous'] + sorted(df_catalogue['Secteur'].unique().tolist())
    secteur_filtre = st.selectbox("Secteur", secteurs)

    type_filtre = st.multiselect(
        "Type d'événement",
        ['Abrogation', 'Modification'],
        default=['Abrogation', 'Modification']
    )

    st.markdown("---")

    # Téléchargements
    st.markdown("#### 📥 Téléchargements")


    # Excel du catalogue
    @st.cache_data
    def convert_to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Catalogue')
        return output.getvalue()


    excel_data = convert_to_excel(df_catalogue[['Reference', 'Intitule', 'Secteur']])
    st.download_button(
        label="📊 Catalogue Excel",
        data=excel_data,
        file_name=f"catalogue_cee_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # PDF source
    st.download_button(
        label="📄 PDF Source",
        data=pdf_content,
        file_name="catalogue_cee_source.pdf",
        mime="application/pdf"
    )

    # CSV abrogations
    if not df_abrogations.empty:
        csv_abrog = df_abrogations[['Reference', 'Intitule', 'Secteur', 'Date', 'Statut']].to_csv(index=False, sep=';')
        st.download_button(
            label="📕 Abrogations CSV",
            data=csv_abrog,
            file_name=f"abrogations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ============================================================================
# CONTENU PRINCIPAL
# ============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 Catalogue CEE - Suivi Réglementaire</h1>
    <p>Dashboard de veille sur les fiches d'opérations standardisées d'économies d'énergie</p>
</div>
""", unsafe_allow_html=True)

# Date actuelle
aujourd_hui = datetime.now()
mois_actuel = aujourd_hui.month
annee_actuelle = aujourd_hui.year

# Calculer le mois prochain
if mois_actuel == 12:
    mois_prochain = 1
    annee_prochaine = annee_actuelle + 1
else:
    mois_prochain = mois_actuel + 1
    annee_prochaine = annee_actuelle

# ============================================================================
# KPIs PRINCIPAUX
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card green">
        <p class="kpi-value">{len(df_catalogue)}</p>
        <p class="kpi-label">📋 Fiches dans le catalogue</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    nb_abrog_futures = len(df_abrogations[df_abrogations['Statut'] == 'FUTURE']) if (
                not df_abrogations.empty and 'Statut' in df_abrogations.columns) else 0
    st.markdown(f"""
    <div class="kpi-card red">
        <p class="kpi-value">{nb_abrog_futures}</p>
        <p class="kpi-label">🚨 Abrogations à venir</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    nb_modif_futures = len(df_modifications[df_modifications['Statut'] == 'FUTURE']) if (
                not df_modifications.empty and 'Statut' in df_modifications.columns) else 0
    st.markdown(f"""
    <div class="kpi-card orange">
        <p class="kpi-value">{nb_modif_futures}</p>
        <p class="kpi-label">📝 Modifications à venir</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    nb_secteurs = df_catalogue['Secteur'].nunique()
    st.markdown(f"""
    <div class="kpi-card blue">
        <p class="kpi-value">{nb_secteurs}</p>
        <p class="kpi-label">🏢 Secteurs couverts</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# ALERTES DU MOIS EN COURS ET MOIS PROCHAIN
# ============================================================================

st.markdown('<p class="section-header">🔔 Alertes - Mois en cours et à venir</p>', unsafe_allow_html=True)

col_mois_actuel, col_mois_prochain = st.columns(2)

with col_mois_actuel:
    st.markdown(f"#### 📅 {get_mois_nom(mois_actuel)} {annee_actuelle}")

    # Abrogations ce mois
    abrog_mois = pd.DataFrame()
    if not df_abrogations.empty and 'DateObj' in df_abrogations.columns:
        abrog_mois = df_abrogations[
            (df_abrogations['DateObj'].dt.month == mois_actuel) &
            (df_abrogations['DateObj'].dt.year == annee_actuelle)
            ]

    if not abrog_mois.empty:
        st.markdown(f"""
        <div class="alert-box danger">
            <span style="font-size: 1.5rem;">🚨</span>
            <div>
                <strong>{len(abrog_mois)} abrogation(s)</strong> ce mois<br>
                <small>{', '.join(abrog_mois['Reference'].tolist()[:5])}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-box success">
            <span style="font-size: 1.5rem;">✅</span>
            <div><strong>Aucune abrogation</strong> ce mois</div>
        </div>
        """, unsafe_allow_html=True)

    # Modifications ce mois
    modif_mois = pd.DataFrame()
    if not df_modifications.empty and 'DateObj' in df_modifications.columns:
        modif_mois = df_modifications[
            (df_modifications['DateObj'].dt.month == mois_actuel) &
            (df_modifications['DateObj'].dt.year == annee_actuelle)
            ]

    if not modif_mois.empty:
        st.markdown(f"""
        <div class="alert-box warning">
            <span style="font-size: 1.5rem;">📝</span>
            <div>
                <strong>{len(modif_mois)} modification(s)</strong> ce mois<br>
                <small>{', '.join(modif_mois['Reference'].unique().tolist()[:5])}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-box info">
            <span style="font-size: 1.5rem;">✅</span>
            <div><strong>Aucune modification</strong> ce mois</div>
        </div>
        """, unsafe_allow_html=True)

with col_mois_prochain:
    st.markdown(f"#### 📅 {get_mois_nom(mois_prochain)} {annee_prochaine}")

    # Abrogations mois prochain
    abrog_prochain = pd.DataFrame()
    if not df_abrogations.empty and 'DateObj' in df_abrogations.columns:
        abrog_prochain = df_abrogations[
            (df_abrogations['DateObj'].dt.month == mois_prochain) &
            (df_abrogations['DateObj'].dt.year == annee_prochaine)
            ]

    if not abrog_prochain.empty:
        st.markdown(f"""
        <div class="alert-box danger">
            <span style="font-size: 1.5rem;">⚠️</span>
            <div>
                <strong>{len(abrog_prochain)} abrogation(s)</strong> prévue(s)<br>
                <small>{', '.join(abrog_prochain['Reference'].tolist()[:5])}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-box success">
            <span style="font-size: 1.5rem;">✅</span>
            <div><strong>Aucune abrogation</strong> prévue</div>
        </div>
        """, unsafe_allow_html=True)

    # Modifications mois prochain
    modif_prochain = pd.DataFrame()
    if not df_modifications.empty and 'DateObj' in df_modifications.columns:
        modif_prochain = df_modifications[
            (df_modifications['DateObj'].dt.month == mois_prochain) &
            (df_modifications['DateObj'].dt.year == annee_prochaine)
            ]

    if not modif_prochain.empty:
        st.markdown(f"""
        <div class="alert-box warning">
            <span style="font-size: 1.5rem;">📝</span>
            <div>
                <strong>{len(modif_prochain)} modification(s)</strong> prévue(s)<br>
                <small>{', '.join(modif_prochain['Reference'].unique().tolist()[:5])}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-box info">
            <span style="font-size: 1.5rem;">✅</span>
            <div><strong>Aucune modification</strong> prévue</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# RECHERCHE DE FICHE
# ============================================================================

st.markdown('<p class="section-header">🔍 Recherche de fiche</p>', unsafe_allow_html=True)

col_search, col_result = st.columns([1, 2])

with col_search:
    search_ref = st.text_input(
        "Référence de la fiche",
        placeholder="Ex: BAT-TH-101",
        help="Entrez la référence complète ou partielle"
    ).upper()

with col_result:
    if search_ref:
        # Recherche
        mask = df_catalogue['Reference'].str.contains(search_ref, case=False, na=False)
        resultats = df_catalogue[mask]

        if not resultats.empty:
            st.success(f"✅ {len(resultats)} fiche(s) trouvée(s)")

            for _, fiche in resultats.iterrows():
                ref = fiche['Reference']
                intitule = fiche['Intitule']
                secteur = fiche['Secteur']

                # Chercher les événements liés
                abrog_fiche = df_abrogations[
                    df_abrogations['Reference'] == ref] if not df_abrogations.empty else pd.DataFrame()
                modif_fiche = df_modifications[
                    df_modifications['Reference'] == ref] if not df_modifications.empty else pd.DataFrame()

                with st.expander(f"📋 **{ref}** - {secteur}", expanded=True):
                    st.markdown(f"**Intitulé:** {intitule}")

                    if not abrog_fiche.empty:
                        for _, ab in abrog_fiche.iterrows():
                            statut_class = "future" if ab['Statut'] == 'FUTURE' else "passee"
                            st.markdown(f"""
                            <span class="badge abrogation">ABROGATION</span>
                            <span class="badge {statut_class}">{ab['Statut']}</span>
                            📅 {ab['Date']}
                            """, unsafe_allow_html=True)

                    if not modif_fiche.empty:
                        st.markdown("**Historique des versions:**")
                        for _, mod in modif_fiche.iterrows():
                            st.markdown(f"- {mod['Version']} applicable au {mod['Date']}")
        else:
            st.warning(f"⚠️ Aucune fiche trouvée pour '{search_ref}'")

# ============================================================================
# CHANGEMENTS À PARTIR D'UNE DATE
# ============================================================================

st.markdown(f'<p class="section-header">📅 Changements à partir du {date_ref.strftime("%d/%m/%Y")}</p>',
            unsafe_allow_html=True)

date_ref_dt = datetime.combine(date_ref, datetime.min.time())

# Filtrer par secteur si nécessaire
df_abrog_filtered = df_abrogations.copy() if not df_abrogations.empty else pd.DataFrame()
df_modif_filtered = df_modifications.copy() if not df_modifications.empty else pd.DataFrame()

if secteur_filtre != 'Tous':
    if not df_abrog_filtered.empty:
        df_abrog_filtered = df_abrog_filtered[df_abrog_filtered['Secteur'] == secteur_filtre]
    if not df_modif_filtered.empty:
        df_modif_filtered = df_modif_filtered[df_modif_filtered['Secteur'] == secteur_filtre]

# Filtrer par date
if not df_abrog_filtered.empty and 'DateObj' in df_abrog_filtered.columns:
    df_abrog_filtered = df_abrog_filtered[df_abrog_filtered['DateObj'] >= date_ref_dt]
if not df_modif_filtered.empty and 'DateObj' in df_modif_filtered.columns:
    df_modif_filtered = df_modif_filtered[df_modif_filtered['DateObj'] >= date_ref_dt]

tab_abrog, tab_modif, tab_echeances, tab_timeline, tab_web = st.tabs(
    ["🚨 Abrogations", "📝 Modifications", "⏰ Échéances", "📊 Timeline", "🌐 Fiches Web"])

with tab_abrog:
    if 'Abrogation' in type_filtre and not df_abrog_filtered.empty:
        st.markdown(f"**{len(df_abrog_filtered)} abrogation(s)** à partir du {date_ref.strftime('%d/%m/%Y')}")

        # Grouper par date
        for date in sorted(df_abrog_filtered['Date'].unique(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
            fiches = df_abrog_filtered[df_abrog_filtered['Date'] == date]
            is_future = datetime.strptime(date, '%d/%m/%Y') >= datetime.now()

            with st.expander(f"{'🔴' if is_future else '⚪'} **{date}** - {len(fiches)} fiche(s)", expanded=is_future):
                fiches_list = list(fiches.iterrows())
                for i in range(0, len(fiches_list), 2):
                    col1, col2 = st.columns(2)

                    # Première fiche
                    _, f1 = fiches_list[i]
                    with col1:
                        st.markdown(f"""
                        <div class="fiche-card">
                            <span class="fiche-ref">{f1['Reference']}</span>
                            <span class="badge {'future' if is_future else 'passee'}">{f1['Statut']}</span>
                            <p class="fiche-title">{str(f1['Intitule'])[:60]}</p>
                            <small>🏢 {f1['Secteur']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                    # Deuxième fiche (si existe)
                    if i + 1 < len(fiches_list):
                        _, f2 = fiches_list[i + 1]
                        with col2:
                            st.markdown(f"""
                            <div class="fiche-card">
                                <span class="fiche-ref">{f2['Reference']}</span>
                                <span class="badge {'future' if is_future else 'passee'}">{f2['Statut']}</span>
                                <p class="fiche-title">{str(f2['Intitule'])[:60]}</p>
                                <small>🏢 {f2['Secteur']}</small>
                            </div>
                            """, unsafe_allow_html=True)
    else:
        st.info("Aucune abrogation trouvée pour ces critères")

with tab_modif:
    if 'Modification' in type_filtre and not df_modif_filtered.empty:
        st.markdown(f"**{len(df_modif_filtered)} modification(s)** à partir du {date_ref.strftime('%d/%m/%Y')}")

        # Trier d'abord puis sélectionner les colonnes
        if 'DateObj' in df_modif_filtered.columns:
            df_display = df_modif_filtered.sort_values('DateObj')[
                ['Reference', 'Intitule', 'Secteur', 'Version', 'Date', 'Statut']]
        else:
            df_display = df_modif_filtered[['Reference', 'Intitule', 'Secteur', 'Version', 'Date', 'Statut']]

        st.dataframe(
            df_display,
            width='stretch',
            hide_index=True
        )
    else:
        st.info("Aucune modification trouvée pour ces critères")

with tab_echeances:
    st.markdown("### ⏰ Prochaines échéances à surveiller")

    # Combiner abrogations et modifications futures
    prochaines = []

    if not df_abrogations.empty and 'Statut' in df_abrogations.columns and 'DateObj' in df_abrogations.columns:
        futures_abrog = df_abrogations[df_abrogations['Statut'] == 'FUTURE'].copy()
        if not futures_abrog.empty:
            futures_abrog['Type'] = 'Abrogation'
            prochaines.append(futures_abrog[['Reference', 'Intitule', 'Secteur', 'Date', 'DateObj', 'Type']])

    if not df_modifications.empty and 'Statut' in df_modifications.columns and 'DateObj' in df_modifications.columns:
        futures_modif = df_modifications[df_modifications['Statut'] == 'FUTURE'].copy()
        if not futures_modif.empty:
            futures_modif['Type'] = 'Modification'
            prochaines.append(futures_modif[['Reference', 'Intitule', 'Secteur', 'Date', 'DateObj', 'Type']])

    if prochaines:
        df_prochaines = pd.concat(prochaines, ignore_index=True)
        df_prochaines = df_prochaines.sort_values('DateObj').head(30)

        # Statistiques rapides
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            nb_30j = len(df_prochaines[(df_prochaines['DateObj'] - datetime.now()).dt.days <= 30])
            st.metric("🔴 Sous 30 jours", nb_30j)
        with col_stat2:
            nb_90j = len(df_prochaines[((df_prochaines['DateObj'] - datetime.now()).dt.days > 30) & (
                        (df_prochaines['DateObj'] - datetime.now()).dt.days <= 90)])
            st.metric("🟠 30-90 jours", nb_90j)
        with col_stat3:
            nb_plus = len(df_prochaines[(df_prochaines['DateObj'] - datetime.now()).dt.days > 90])
            st.metric("🟢 Plus de 90 jours", nb_plus)

        st.markdown("---")

        # Filtrer les fiches valides
        fiches_valides = []
        for _, row in df_prochaines.iterrows():
            jours_restants = (row['DateObj'] - datetime.now()).days
            if jours_restants >= 0:
                fiches_valides.append((row, jours_restants))

        # Affichage en 2 colonnes
        for i in range(0, len(fiches_valides), 2):
            col1, col2 = st.columns(2)

            # Première fiche
            row1, jours1 = fiches_valides[i]
            urgence1 = "🔴" if jours1 <= 30 else ("🟠" if jours1 <= 90 else "🟢")
            type_badge1 = "abrogation" if row1['Type'] == 'Abrogation' else "modification"

            with col1:
                st.markdown(f"""
                <div class="fiche-card">
                    <span class="fiche-ref">{urgence1} {row1['Reference']}</span>
                    <span class="badge {type_badge1}">{row1['Type']}</span>
                    <p class="fiche-title">{str(row1['Intitule'])[:60]}</p>
                    <small>📅 {row1['Date']} | ⏱️ {jours1}j | 🏢 {row1['Secteur']}</small>
                </div>
                """, unsafe_allow_html=True)

            # Deuxième fiche (si existe)
            if i + 1 < len(fiches_valides):
                row2, jours2 = fiches_valides[i + 1]
                urgence2 = "🔴" if jours2 <= 30 else ("🟠" if jours2 <= 90 else "🟢")
                type_badge2 = "abrogation" if row2['Type'] == 'Abrogation' else "modification"

                with col2:
                    st.markdown(f"""
                    <div class="fiche-card">
                        <span class="fiche-ref">{urgence2} {row2['Reference']}</span>
                        <span class="badge {type_badge2}">{row2['Type']}</span>
                        <p class="fiche-title">{str(row2['Intitule'])[:60]}</p>
                        <small>📅 {row2['Date']} | ⏱️ {jours2}j | 🏢 {row2['Secteur']}</small>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.success("✅ Aucune échéance à venir - Tout est à jour !")

with tab_timeline:
    st.markdown("### 📊 Analyse temporelle des changements")

    # Collecter tous les événements
    events = []

    if 'Abrogation' in type_filtre and not df_abrog_filtered.empty and 'DateObj' in df_abrog_filtered.columns:
        for _, row in df_abrog_filtered.iterrows():
            if pd.notna(row['DateObj']):
                events.append({
                    'Date': row['DateObj'],
                    'Reference': row['Reference'],
                    'Type': 'Abrogation',
                    'Secteur': row['Secteur'],
                    'Mois': row['DateObj'].strftime('%Y-%m'),
                    'Annee': row['DateObj'].year
                })

    if 'Modification' in type_filtre and not df_modif_filtered.empty and 'DateObj' in df_modif_filtered.columns:
        for _, row in df_modif_filtered.iterrows():
            if pd.notna(row['DateObj']):
                events.append({
                    'Date': row['DateObj'],
                    'Reference': row['Reference'],
                    'Type': 'Modification',
                    'Secteur': row['Secteur'],
                    'Mois': row['DateObj'].strftime('%Y-%m'),
                    'Annee': row['DateObj'].year
                })

    if events:
        df_events = pd.DataFrame(events)

        # ===== Graphique 1: Barres par mois =====
        st.markdown("#### 📅 Répartition par mois")

        df_mois = df_events.groupby(['Mois', 'Type']).size().reset_index(name='Nombre')
        df_mois = df_mois.sort_values('Mois')

        fig_mois = px.bar(
            df_mois,
            x='Mois',
            y='Nombre',
            color='Type',
            barmode='group',
            color_discrete_map={'Abrogation': '#dc3545', 'Modification': '#ff8c00'},
            labels={'Mois': 'Période', 'Nombre': 'Nombre de fiches'}
        )
        fig_mois.update_layout(
            height=350,
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=50, b=80)
        )
        st.plotly_chart(fig_mois, width='stretch')

        # ===== Graphique 2: Camembert par secteur =====
        col_pie1, col_pie2 = st.columns(2)

        with col_pie1:
            st.markdown("#### 🏢 Par secteur")
            df_secteur = df_events.groupby('Secteur').size().reset_index(name='Nombre')

            fig_secteur = px.pie(
                df_secteur,
                values='Nombre',
                names='Secteur',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4
            )
            fig_secteur.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_secteur, width='stretch')

        with col_pie2:
            st.markdown("#### 📊 Par type")
            df_type = df_events.groupby('Type').size().reset_index(name='Nombre')

            fig_type = px.pie(
                df_type,
                values='Nombre',
                names='Type',
                color='Type',
                color_discrete_map={'Abrogation': '#dc3545', 'Modification': '#ff8c00'},
                hole=0.4
            )
            fig_type.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig_type, width='stretch')

        # ===== Tableau récapitulatif par date =====
        st.markdown("#### 📋 Détail par date")

        df_recap = df_events.groupby(['Date', 'Type']).agg({
            'Reference': lambda x: ', '.join(x),
            'Secteur': 'first'
        }).reset_index()
        df_recap['Date_Str'] = df_recap['Date'].dt.strftime('%d/%m/%Y')
        df_recap = df_recap.sort_values('Date')

        # Compter par date
        df_count = df_events.groupby(['Date', 'Type']).size().reset_index(name='Nb')
        df_count['Date_Str'] = df_count['Date'].dt.strftime('%d/%m/%Y')
        df_count = df_count.sort_values('Date')

        # Afficher en tableau compact
        for date_str in df_count['Date_Str'].unique():
            date_data = df_count[df_count['Date_Str'] == date_str]
            refs = df_events[df_events['Date'].dt.strftime('%d/%m/%Y') == date_str]

            nb_abrog = len(refs[refs['Type'] == 'Abrogation'])
            nb_modif = len(refs[refs['Type'] == 'Modification'])

            badges = ""
            if nb_abrog > 0:
                badges += f'<span class="badge abrogation">{nb_abrog} Abrog.</span> '
            if nb_modif > 0:
                badges += f'<span class="badge modification">{nb_modif} Modif.</span>'

            refs_list = refs['Reference'].tolist()
            refs_str = ', '.join(refs_list[:6])
            if len(refs_list) > 6:
                refs_str += f' ... (+{len(refs_list) - 6})'

            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 8px; padding: 10px 15px; margin: 5px 0; border-left: 3px solid #2d8f4e;">
                <strong>📅 {date_str}</strong> {badges}<br>
                <small style="color: #666;">{refs_str}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun événement à afficher pour cette période")

# ============================================================================
# ONGLET FICHES WEB - SCRAPING DU SITE DU MINISTÈRE
# ============================================================================

with tab_web:
    st.markdown("### 🌐 Fiches du site officiel du Ministère")
    st.markdown("""
    <div class="alert-box info">
        <span style="font-size: 1.5rem;">ℹ️</span>
        <div>
            <strong>Source:</strong> <a href="https://www.ecologie.gouv.fr/politiques-publiques/operations-standardisees-deconomies-denergie" target="_blank">ecologie.gouv.fr</a><br>
            <small>Données extraites directement du site officiel (plus à jour que le catalogue PDF)</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bouton pour charger/rafraîchir les données
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        refresh_web = st.button("🔄 Charger les fiches du site", type="primary")

    if refresh_web or 'df_web' in st.session_state:
        if refresh_web:
            with st.spinner("⏳ Scraping du site du ministère en cours..."):
                df_web, error = scraper_fiches_web()
                if error:
                    st.error(f"❌ Erreur: {error}")
                else:
                    st.session_state['df_web'] = df_web
                    st.success(f"✅ {len(df_web)} fiches récupérées du site web")

        if 'df_web' in st.session_state and not st.session_state['df_web'].empty:
            df_web = st.session_state['df_web']

            # Statistiques
            st.markdown("---")
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

            with col_stat1:
                st.metric("📋 Total fiches", len(df_web))
            with col_stat2:
                nb_2026 = len(df_web[df_web['Annee'] == 2026]) if 'Annee' in df_web.columns else 0
                st.metric("🔴 Applicables 2026", nb_2026)
            with col_stat3:
                nb_2025 = len(df_web[df_web['Annee'] == 2025]) if 'Annee' in df_web.columns else 0
                st.metric("🟠 Applicables 2025", nb_2025)
            with col_stat4:
                nb_secteurs = df_web['Secteur'].nunique() if 'Secteur' in df_web.columns else 0
                st.metric("🏢 Secteurs", nb_secteurs)

            st.markdown("---")

            # Filtres
            col_filtre1, col_filtre2, col_filtre3 = st.columns(3)

            with col_filtre1:
                annees_dispo = sorted([a for a in df_web['Annee'].unique() if pd.notna(a)], reverse=True)
                annee_filtre = st.selectbox("📅 Filtrer par année", ['Toutes'] + [int(a) for a in annees_dispo],
                                            key='web_annee')

            with col_filtre2:
                secteurs_dispo = ['Tous'] + sorted(df_web['Secteur'].unique().tolist())
                secteur_web_filtre = st.selectbox("🏢 Filtrer par secteur", secteurs_dispo, key='web_secteur')

            with col_filtre3:
                search_web = st.text_input("🔍 Rechercher (référence)", placeholder="Ex: BAR-TH", key='web_search')

            # Appliquer filtres
            df_display_web = df_web.copy()

            if annee_filtre != 'Toutes':
                df_display_web = df_display_web[df_display_web['Annee'] == annee_filtre]

            if secteur_web_filtre != 'Tous':
                df_display_web = df_display_web[df_display_web['Secteur'] == secteur_web_filtre]

            if search_web:
                df_display_web = df_display_web[df_display_web['Reference'].str.contains(search_web.upper(), na=False)]

            st.markdown(f"**{len(df_display_web)} fiche(s) affichée(s)**")


            # Fonction pour afficher les fiches en 2 colonnes
            def afficher_fiches_2col(fiches_df):
                fiches_list = list(fiches_df.iterrows())
                for i in range(0, len(fiches_list), 2):
                    col1, col2 = st.columns(2)

                    _, f1 = fiches_list[i]
                    with col1:
                        st.markdown(f"""
                        <div class="fiche-card">
                            <span class="fiche-ref">{f1['Reference']}</span>
                            <span class="badge modification">{f1['Version']}</span>
                            <p class="fiche-title">{str(f1['Intitule'])[:55]}</p>
                            <small>📅 {f1['Date_Application']} | 🏢 {f1['Secteur']}</small>
                        </div>
                        """, unsafe_allow_html=True)

                    if i + 1 < len(fiches_list):
                        _, f2 = fiches_list[i + 1]
                        with col2:
                            st.markdown(f"""
                            <div class="fiche-card">
                                <span class="fiche-ref">{f2['Reference']}</span>
                                <span class="badge modification">{f2['Version']}</span>
                                <p class="fiche-title">{str(f2['Intitule'])[:55]}</p>
                                <small>📅 {f2['Date_Application']} | 🏢 {f2['Secteur']}</small>
                            </div>
                            """, unsafe_allow_html=True)


            # Affichage par année avec détail par mois pour année courante/future
            if not df_display_web.empty:
                annee_courante = datetime.now().year

                # Ajouter colonne Mois pour le tri
                df_display_web['Mois'] = df_display_web['DateObj'].dt.month

                for annee in sorted(df_display_web['Annee'].dropna().unique(), reverse=True):
                    fiches_annee = df_display_web[df_display_web['Annee'] == annee].copy()
                    icon = "🔴" if annee > annee_courante else ("🟠" if annee == annee_courante else "🟢")

                    # Pour l'année en cours et future : détail par mois
                    if annee >= annee_courante:
                        # Titre de l'année (pas un expander pour éviter l'imbrication)
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {'#f8d7da' if annee > annee_courante else '#fff3cd'} 0%, #ffffff 100%); 
                                    padding: 12px 20px; margin: 20px 0 10px 0; border-radius: 10px;
                                    border-left: 5px solid {'#dc3545' if annee > annee_courante else '#ffc107'};">
                            <span style="font-size: 1.3rem;">{icon}</span>
                            <strong style="font-size: 1.2rem; margin-left: 10px;">{int(annee)}</strong>
                            <span style="background: {'#dc3545' if annee > annee_courante else '#ffc107'}; color: white; 
                                        padding: 4px 12px; border-radius: 15px; font-size: 0.85rem; margin-left: 15px;">
                                {len(fiches_annee)} fiche(s)
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

                        # Grouper par mois
                        mois_list = sorted(fiches_annee['Mois'].dropna().unique())

                        for mois in mois_list:
                            fiches_mois = fiches_annee[fiches_annee['Mois'] == mois]
                            nom_mois = get_mois_nom(int(mois))

                            # Déterminer si le mois est passé, en cours ou futur
                            if annee > annee_courante:
                                mois_icon = "🔴"  # Futur
                                mois_expanded = True
                            elif annee == annee_courante:
                                if mois > datetime.now().month:
                                    mois_icon = "🔴"  # Mois futur
                                    mois_expanded = True
                                elif mois == datetime.now().month:
                                    mois_icon = "🟡"  # Mois en cours
                                    mois_expanded = True
                                else:
                                    mois_icon = "🟢"  # Mois passé
                                    mois_expanded = False
                            else:
                                mois_icon = "🟢"
                                mois_expanded = False

                            # Expander pour chaque mois (cliquable!)
                            with st.expander(f"{mois_icon} {nom_mois} {int(annee)} — {len(fiches_mois)} fiche(s)",
                                             expanded=mois_expanded):
                                afficher_fiches_2col(fiches_mois)
                    else:
                        # Pour les années passées : juste l'année
                        with st.expander(f"{icon} **{int(annee)}** - {len(fiches_annee)} fiche(s)", expanded=False):
                            afficher_fiches_2col(fiches_annee)

            # Section comparaison avec le catalogue PDF
            st.markdown("---")
            st.markdown("### 🔄 Comparaison avec le catalogue PDF")

            # Trouver les fiches qui sont sur le web mais pas/différentes dans le PDF
            refs_catalogue = set(df_catalogue['Reference'].tolist()) if not df_catalogue.empty else set()
            refs_web = set(df_web['Reference'].tolist())

            # Fiches uniquement sur le web (nouvelles)
            nouvelles = refs_web - refs_catalogue

            col_comp1, col_comp2 = st.columns(2)

            with col_comp1:
                st.markdown(f"#### 🆕 Nouvelles fiches ({len(nouvelles)})")
                if nouvelles:
                    for ref in sorted(nouvelles)[:20]:
                        fiche = df_web[df_web['Reference'] == ref].iloc[0]
                        st.markdown(f"""
                        <div style="background: #d4edda; border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 0.85rem;">
                            <strong>{ref}</strong> | {fiche['Version']} | 📅 {fiche['Date_Application']}
                        </div>
                        """, unsafe_allow_html=True)
                    if len(nouvelles) > 20:
                        st.info(f"... et {len(nouvelles) - 20} autres")
                else:
                    st.success("✅ Aucune nouvelle fiche")

            with col_comp2:
                # Fiches 2026 à surveiller
                fiches_2026 = df_web[df_web['Annee'] == 2026]
                st.markdown(f"#### 🔴 Fiches 2026 à surveiller ({len(fiches_2026)})")
                if not fiches_2026.empty:
                    for _, f in fiches_2026.head(20).iterrows():
                        st.markdown(f"""
                        <div style="background: #f8d7da; border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 0.85rem;">
                            <strong>{f['Reference']}</strong> | {f['Version']} | 📅 {f['Date_Application']}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Aucune fiche pour 2026")

            # Export
            st.markdown("---")
            csv_web = df_web.to_csv(index=False, sep=';')
            st.download_button(
                label="📥 Exporter les fiches web (CSV)",
                data=csv_web,
                file_name=f"fiches_web_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("👆 Cliquez sur le bouton ci-dessus pour charger les fiches depuis le site du ministère")

# ============================================================================
# STATISTIQUES PAR SECTEUR
# ============================================================================

st.markdown('<p class="section-header">📊 Statistiques par secteur</p>', unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    # Répartition des fiches par secteur
    secteur_counts = df_catalogue['Secteur'].value_counts().reset_index()
    secteur_counts.columns = ['Secteur', 'Nombre']

    fig1 = px.pie(
        secteur_counts,
        values='Nombre',
        names='Secteur',
        title="Répartition des fiches par secteur",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig1.update_layout(font_family="Outfit")
    st.plotly_chart(fig1, width='stretch')

with col_chart2:
    # Abrogations par secteur
    if not df_abrogations.empty:
        abrog_secteur = df_abrogations.groupby(['Secteur', 'Statut']).size().reset_index(name='Nombre')

        fig2 = px.bar(
            abrog_secteur,
            x='Secteur',
            y='Nombre',
            color='Statut',
            title="Abrogations par secteur",
            color_discrete_map={'FUTURE': '#dc3545', 'PASSEE': '#6c757d'},
            barmode='group'
        )
        fig2.update_layout(font_family="Outfit")
        st.plotly_chart(fig2, width='stretch')

# ============================================================================
# FOOTER
# ============================================================================

st.markdown(f"""
<div class="footer">
    <p>🌿 <strong>Green Prime</strong> - Pôle Conformité CEE</p>
    <p>Données extraites du catalogue officiel (77ème arrêté) | Mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    <p style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ddd;">
        <span style="color: #888; font-size: 0.85rem;">Développé avec ✨ par </span>
        <a href="https://www.linkedin.com/in/sadou-barry-881868164/" target="_blank" 
           style="color: #2d8f4e; text-decoration: none; font-weight: 600;">
            Sadou BARRY
        </a>
    </p>
</div>
""", unsafe_allow_html=True)