import streamlit as st
import pandas as pd
import os
import json
import streamlit.components.v1 as components

st.set_page_config(page_title="Calculateur de Charges de Copropriété", layout="wide", initial_sidebar_state="expanded")

SIDEBAR_BG = "#2d0b53"
SIDEBAR_TEXT = "#ffffff"

st.markdown(
    f"""
    <style>
    [data-testid="stSidebar"] > div:first-child {{background-color: {SIDEBAR_BG} !important; color: {SIDEBAR_TEXT} !important;}}
    [data-testid="stSidebar"] * {{color: {SIDEBAR_TEXT} !important;}}
    .css-1d391kg, .css-1v3fvcr {{color: {SIDEBAR_TEXT} !important;}}
    button {{color: #ffffff !important;}}
    .stDownloadButton button {{
        background: linear-gradient(135deg, #5c2d91 0%, #7c3fa8 100%) !important;
        color: #ffffff !important;
        padding: 12px 24px !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        cursor: pointer !important;
        box-shadow: 0 4px 12px rgba(92, 45, 145, 0.3) !important;
        transition: all 0.3s ease !important;
    }}
    .stDownloadButton button:hover {{
        background: linear-gradient(135deg, #7c3fa8 0%, #9d4fbf 100%) !important;
        box-shadow: 0 6px 16px rgba(92, 45, 145, 0.5) !important;
        transform: translateY(-2px) !important;
    }}
    [data-testid="stFileUploadDropzone"] {{
        background: linear-gradient(135deg, #f0e6ff 0%, #e6d4f0 100%) !important;
        border: 2px dashed #5c2d91 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }}
    [data-testid="stFileUploadDropzone"]:hover {{
        background: linear-gradient(135deg, #e6d4f0 0%, #ddc2e6 100%) !important;
        border-color: #7c3fa8 !important;
        box-shadow: 0 4px 16px rgba(92, 45, 145, 0.15) !important;
    }}
    .uploadedFileName {{
        color: #5c2d91 !important;
        font-weight: 600 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "uploaded_data" not in st.session_state:
    st.session_state["uploaded_data"] = None
    st.session_state["uploaded_file_name"] = None

expected_sheets = {
    "Revenus": ["Label du revenu", "Montant"],
    "Budget": ["ID1", "Segment", "Classe de provision", "Label de la provision", "Provision"],
    "Propositions": ["Type de prestation", "Label de la prestation", "ID1", "Prestataire", "Cout", "Taxes", "Total TTC", "Description"],
    "Copropriétaires": [
        "Batiment",
        "Label de lot",
        "Nom du coproprietaire",
        "Tantièmes copropriété",
        "Tantièmes ascenseur 1-1",
        "Tantièmes ascenseur 1-2",
        "Tantièmes ascenseur 2",
        "Tantièmes ascenseur 3",
        "Tantièmes chauffage",
        "Tantièmes Batiment 1",
        "Tantièmes Batiment 2",
        "Tantièmes Batiment 3",
        "Tantièmes Hall 1-1",
        "Tantièmes Hall 1-2",
        "Tantièmes Hall 2",
        "Tantièmes Logement/Stationnements",
        "Stationnement",
        "Numéro de lot",
        "Lot Nexity",
        "Etage",
    ],
    "Règles": ["Label des règles", "Limite", "Taxes", "Total TTC"],
}

# Persistence file for storing selections between sessions
SAVE_DIR = "data"
SAVE_PATH = os.path.join(SAVE_DIR, "saved_state.json")
BUDGET_INITIAL_LABEL = "Budget initial"


def load_persisted_state():
    try:
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {}
    return {}


def normalize_provision_key(label: str) -> str:
    return "".join([c if c.isalnum() else "_" for c in str(label)])


def get_selected_prestations(selected_map: dict, provision_label: str) -> list:
    if not selected_map:
        return []
    if provision_label in selected_map:
        return selected_map.get(provision_label) or []

    normalized_provision = normalize_provision_key(provision_label)
    for saved_label, selected in selected_map.items():
        if normalize_provision_key(saved_label) == normalized_provision:
            return selected or []
        if str(saved_label).replace(" ", "_") == normalized_provision:
            return selected or []
    return []


def save_persisted_state():
    # 1. Charger l'état complet existant
    current_persisted_data = load_persisted_state()

    # Mettre à jour le propriétaire et les tantièmes globaux depuis l'état de session actuel
    if "selected_owner_main" in st.session_state:
        current_persisted_data["selected_owner_main"] = st.session_state.get("selected_owner_main")
    if "total_tantiemes_global" in st.session_state:
        current_persisted_data["total_tantiemes_global"] = st.session_state.get("total_tantiemes_global")

    # S'assurer que la clé 'scenarios' de niveau supérieur existe
    if "scenarios" not in current_persisted_data:
        current_persisted_data["scenarios"] = {}

    # Parcourir tous les scénarios possibles (1, 2, 3)
    # et mettre à jour leur état en fonction de ce qui est actuellement dans st.session_state.
    # Cela garantit que seules les données du scénario *actuellement rendu* sont mises à jour,
    # tandis que les données des autres scénarios (non rendus) restent telles qu'elles ont été chargées.
    for i in range(1, 4):
        scenario_key = str(i)
        
        # S'assurer que la structure de ce scénario existe dans les données chargées
        if scenario_key not in current_persisted_data["scenarios"]:
            current_persisted_data["scenarios"][scenario_key] = {}
        
        # Mettre à jour le filtre pour ce scénario s'il est dans session_state
        filter_key = f"scenario_{i}_type_filter"
        if filter_key in st.session_state:
            current_persisted_data["scenarios"][scenario_key]["filter"] = st.session_state.get(filter_key)
        # Si la clé de filtre n'est PAS dans session_state, cela signifie que ce scénario n'est pas actif
        # ou que son filtre a été effacé. Nous ne devrions PAS écraser le filtre persistant avec une liste vide
        # à moins qu'il n'ait été explicitement effacé pour le scénario actif.
        # La logique actuelle est : si filter_key est dans st.session_state, le mettre à jour. C'est correct.

        # Collecter les prestations pour ce scénario depuis st.session_state
        # Cela ne trouvera des clés que pour le scénario *actuellement rendu*.
        prestations_for_this_scenario = {}
        prefix = f"scenario_{i}_props_"
        provision_label_by_key = st.session_state.get("provision_label_by_key", {}) # Ce dict est rempli lorsque les multiselects sont rendus

        found_any_prestations_for_this_scenario = False
        for k, v in st.session_state.items():
            if k.startswith(prefix):
                found_any_prestations_for_this_scenario = True
                prov_label = provision_label_by_key.get(k, k.replace(prefix, "").replace("_", " "))
                prestations_for_this_scenario[prov_label] = v if isinstance(v, list) else ([v] if v and v != BUDGET_INITIAL_LABEL else [])
        
        # Mettre à jour prestations_by_provision uniquement si des clés ont été trouvées pour ce scénario dans st.session_state.
        # Cela évite d'écraser les prestations sauvegardées d'un scénario avec un dictionnaire vide
        # si ce scénario n'est pas actuellement actif/rendu.
        if found_any_prestations_for_this_scenario:
            current_persisted_data["scenarios"][scenario_key]["prestations_by_provision"] = prestations_for_this_scenario

    # 2. Sauvegarder l'état complet mis à jour
    state_to_save = current_persisted_data # Renommage pour la clarté
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(state_to_save, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        # best effort: show a non-blocking message in session state for debugging
        st.session_state["persist_error"] = str(exc)


# --- New callback functions for the simplified prestation selection UI ---
def add_prestation_to_scenario(provision_label, prestation_label, active_scenario):
    safe_label = normalize_provision_key(provision_label)
    key = f"scenario_{active_scenario}_props_{safe_label}"
    if key not in st.session_state:
        st.session_state[key] = []
    if prestation_label not in st.session_state[key]:
        st.session_state[key].append(prestation_label)
    save_persisted_state()

def remove_prestation_from_scenario(provision_label, prestation_label, active_scenario):
    safe_label = normalize_provision_key(provision_label)
    key = f"scenario_{active_scenario}_props_{safe_label}"
    if key in st.session_state and prestation_label in st.session_state[key]:
        st.session_state[key].remove(prestation_label)
    save_persisted_state()

def set_viewed_prestation_details(provision_label, prestation_label):
    st.session_state['current_viewed_prestation_label'] = prestation_label
    st.session_state['current_viewed_provision_label'] = provision_label
    # Force a rerun to display details immediately
    st.rerun()


def map_id_to_tantieme(id_poste: str) -> str:
    """Map Budget.ID1 to the ID used for tantièmes (DAX mapping provided by user)."""
    if not isinstance(id_poste, str):
        return "TOTAL"
    m = id_poste.strip()
    if m in {"ASC11", "ASC12", "ASC2", "ASC3"}:
        return m
    elif m == "ELECBAT1":
        return "BAT1"
    elif m == "ELECBAT2":
        return "BAT2"
    elif m == "ELECBAT3":
        return "BAT3"
    elif m in {"GAZ", "GRANULEBOIS", "MAINTCHAUF"}:
        return "CHAUFF"
    elif m in {"BACSABLE", "MAINTPORT", "POMPERELEVAGE", "REPARPORT", "VENTILPARKING"}:
        return "PARKING"
    elif m == "MAINTVERT":
        return "LOG/STAT"
    else:
        return "TOTAL"

_ID_TOKEN_MAP = {
    "TOTAL": ["copropri"],
    "ASC11": ["ascenseur 1-1", "ascenseur", "1-1"],
    "ASC12": ["ascenseur 1-2", "1-2"],
    "ASC2": ["ascenseur 2", "ascenseur 2"],
    "ASC3": ["ascenseur 3"],
    "BAT1": ["batiment 1", "batiment"],
    "BAT2": ["batiment 2"],
    "BAT3": ["batiment 3"],
    "CHAUFF": ["chauff", "chauffage"],
    "HALL11": ["hall 1-1", "hall"],
    "HALL12": ["hall 1-2"],
    "HALL2": ["hall 1-2", "hall 2"],
    "LOG/STAT": ["logement", "station"],
    "PARKING": ["stationnement", "parking", "stat"],
}


def get_owner_tantieme_for_id(id_tantieme: str, selected_owner: str, copro_df: pd.DataFrame) -> float:
    """Return the tantième value for selected_owner and the given id_tantieme.
    Supports both long (columns 'ID'/'Tantièmes') and wide formats (columns like 'Tantièmes copropriété').
    """
    if copro_df is None or copro_df.empty or not selected_owner:
        return 0.0

    # Case 1: long form with 'ID' and 'Tantièmes' columns
    if "ID" in copro_df.columns and "Tantièmes" in copro_df.columns:
        rows = copro_df[(copro_df.get("Nom du coproprietaire") == selected_owner) & (copro_df.get("ID") == id_tantieme)]
        # Specific filter for Parking: only rows with a stationnement label
        if id_tantieme == "PARKING" and "Stationnement" in copro_df.columns:
            rows = rows[rows["Stationnement"].notna() & (rows["Stationnement"].astype(str).str.strip() != "")]
            
        if not rows.empty:
            vals = pd.to_numeric(rows["Tantièmes"], errors="coerce").fillna(0)
            return float(vals.sum())

    # Case 2: wide form — prefer an explicit mapping from ID to column name
    ID_TO_COLUMN = {
        "TOTAL": "Tantièmes copropriété",
        "ASC11": "Tantièmes ascenseur 1-1",
        "ASC12": "Tantièmes ascenseur 1-2",
        "ASC2": "Tantièmes ascenseur 2",
        "ASC3": "Tantièmes ascenseur 3",
        "BAT1": "Tantièmes Batiment 1",
        "BAT2": "Tantièmes Batiment 2",
        "BAT3": "Tantièmes Batiment 3",
        "CHAUFF": "Tantièmes chauffage",
        "HALL11": "Tantièmes Hall 1-1",
        "HALL12": "Tantièmes Hall 1-2",
        "HALL2": "Tantièmes Hall 2",
        "LOG/STAT": "Tantièmes Logement/Stationnements",
        "PARKING": "Stationnement",
    }

    preferred_col = ID_TO_COLUMN.get(id_tantieme)
    if preferred_col and preferred_col in copro_df.columns:
        copro_rows = copro_df[copro_df.get("Nom du coproprietaire") == selected_owner]
        # Specific filter for Parking: only rows with a stationnement label
        if id_tantieme == "PARKING" and "Stationnement" in copro_df.columns:
            copro_rows = copro_rows[copro_rows["Stationnement"].notna() & (copro_rows["Stationnement"].astype(str).str.strip() != "")]
            
        if not copro_rows.empty:
            vals = copro_rows[preferred_col]
            vals_num = pd.to_numeric(vals, errors="coerce").fillna(0)
            return float(vals_num.sum())

    # Fallback: old token-based heuristic
    cols = [c for c in copro_df.columns if "tanti" in c.lower()]
    tokens = _ID_TOKEN_MAP.get(id_tantieme, [])
    matching_cols = []
    for c in cols:
        cl = c.lower()
        for t in tokens:
            if t in cl:
                matching_cols.append(c)
                break

    # Fallback: if no matching columns found, try looser matching using id_tantieme itself
    if not matching_cols:
        for c in cols:
            if id_tantieme.lower() in c.lower():
                matching_cols.append(c)

    if matching_cols:
        copro_rows = copro_df[copro_df.get("Nom du coproprietaire") == selected_owner]
        # Specific filter for Parking: only rows with a stationnement label
        if id_tantieme == "PARKING" and "Stationnement" in copro_df.columns:
            copro_rows = copro_rows[copro_rows["Stationnement"].notna() & (copro_rows["Stationnement"].astype(str).str.strip() != "")]

        if not copro_rows.empty:
            vals = copro_rows[matching_cols]
            vals_num = vals.apply(pd.to_numeric, errors="coerce").fillna(0)
            return float(vals_num.values.sum())

    return 0.0


def get_total_tantiemes_for_id(id_tantieme: str, copro_df: pd.DataFrame) -> float:
    """Return total tantièmes across all copropriétaires for the given id_tantieme."""
    if copro_df is None or copro_df.empty:
        return 0.0

    ID_TO_COLUMN = {
        "TOTAL": "Tantièmes copropriété",
        "ASC11": "Tantièmes ascenseur 1-1",
        "ASC12": "Tantièmes ascenseur 1-2",
        "ASC2": "Tantièmes ascenseur 2",
        "ASC3": "Tantièmes ascenseur 3",
        "BAT1": "Tantièmes Batiment 1",
        "BAT2": "Tantièmes Batiment 2",
        "BAT3": "Tantièmes Batiment 3",
        "CHAUFF": "Tantièmes chauffage",
        "HALL11": "Tantièmes Hall 1-1",
        "HALL12": "Tantièmes Hall 1-2",
        "HALL2": "Tantièmes Hall 2",
        "LOG/STAT": "Tantièmes Logement/Stationnements",
        "PARKING": "Stationnement",
    }

    preferred_col = ID_TO_COLUMN.get(id_tantieme)
    if preferred_col and preferred_col in copro_df.columns:
        vals = copro_df[preferred_col]
        vals_num = pd.to_numeric(vals, errors="coerce").fillna(0)
        return float(vals_num.sum())

    # fallback: sum all 'tanti' columns
    cols = [c for c in copro_df.columns if "tanti" in c.lower()]
    if cols:
        vals = copro_df[cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        return float(vals.values.sum())

    return 0.0

sidebar_title = st.sidebar.title("Sommaire")
page = st.sidebar.radio("Navigation", ["Importer le fichier", "Sélection des prestations", "Simulation des charges"])

st.title("Calculateur de Charges de Copropriété")

if page == "Importer le fichier":
    # --- PATCH SÉCURITÉ VISUELLE POUR LE BOUTON BROWSE ---
    st.markdown("""
        <style>
        /* Force le texte du bouton Browse à être visible (sombre) et ajoute un contour */
        div[data-testid="stFileUploader"] button {
            color: #31333F !important;
            background-color: #f8f9fa !important;
            border: 1px solid #d3d3d3 !important;
        }
        /* Optionnel : Changement de couleur au survol */
        div[data-testid="stFileUploader"] button:hover {
            background-color: #e2e6ea !important;
            border-color: #dae0e5 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    # -----------------------------------------------------

    st.write("Bienvenue dans l'application de calcul des charges de copropriété.")
    st.write("Téléchargez ci-dessous le modèle Excel `Modele.xlsx` et utilisez-le pour préparer votre import.")
    st.write("Le fichier doit contenir plusieurs feuilles, comme indiqué dans le modèle.")

    download_path = "data/Modele.xlsx"
    try:
        with open(download_path, "rb") as f:
            st.download_button(
                label="Télécharger le modèle Excel",
                data=f,
                file_name="Modele.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except FileNotFoundError:
        st.error(f"Le modèle '{download_path}' est introuvable. Assurez-vous qu'il existe dans le dossier data.")

    uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            xl = pd.ExcelFile(uploaded_file)
            missing_sheets = [s for s in expected_sheets.keys() if s not in xl.sheet_names]
            if missing_sheets:
                st.error("Le fichier Excel ne contient pas toutes les feuilles requises.")
                st.write("Feuilles manquantes :", ", ".join(missing_sheets))
                st.write("Feuilles détectées :", ", ".join(xl.sheet_names))
            else:
                # Vérifier que chaque feuille contient toutes les colonnes attendues
                sheet_errors = {}
                for sheet, expected_cols in expected_sheets.items():
                    df_sheet = pd.read_excel(xl, sheet_name=sheet)
                    missing_cols = [col for col in expected_cols if col not in df_sheet.columns]
                    if missing_cols:
                        sheet_errors[sheet] = {"missing": missing_cols, "detected": df_sheet.columns.tolist()}

                if sheet_errors:
                    st.error("Certaines feuilles ne contiennent pas toutes les colonnes attendues.")
                    for sheet, errors in sheet_errors.items():
                        st.write(f"**Feuille '{sheet}'** - colonnes manquantes : {', '.join(errors['missing'])}")
                        st.write(f"Colonnes détectées : {', '.join(errors['detected'])}")
                else:
                    data = {sheet: pd.read_excel(xl, sheet_name=sheet) for sheet in xl.sheet_names}
                    st.session_state["uploaded_data"] = data
                    st.session_state["uploaded_file_name"] = uploaded_file.name
                    st.success("Fichier Excel importé et validé avec succès !")
                    st.write("Feuilles détectées :", ", ".join(xl.sheet_names))
                    st.write("Nom du fichier :", uploaded_file.name)
        except Exception as exc:
            st.error("Impossible de lire ou d'analyser le fichier Excel. Vérifiez le format et la compatibilité des feuilles.")
            st.write(str(exc))
    elif st.session_state["uploaded_data"] is not None:
        st.success(f"Fichier importé : {st.session_state['uploaded_file_name']}")
        st.write("Vous pouvez maintenant passer à la page 'Sélection des prestations'.")
    else:
        st.info("Veuillez importer un fichier Excel au format correct pour continuer (utilisez le modèle téléchargé ci-dessus).")

elif page == "Sélection des prestations":
    st.write("Sélectionnez d'abord le copropriétaire puis les scénarios, types de provision et prestations à simuler.")
    if st.session_state["uploaded_data"] is None:
        st.warning("Aucun fichier importé. Veuillez d'abord importer le fichier Excel sur la page 'Importer le fichier'.")
    else:
        data = st.session_state["uploaded_data"]
        # Ensure detail view state is initialized
        if 'current_viewed_prestation_label' not in st.session_state:
            st.session_state['current_viewed_prestation_label'] = None
        if 'current_viewed_provision_label' not in st.session_state:
            st.session_state['current_viewed_provision_label'] = None
        props = data.get("Propositions", pd.DataFrame())
        copro = data.get("Copropriétaires", pd.DataFrame())
        budget = data.get("Budget", pd.DataFrame())

        if props.empty or budget.empty or copro.empty:
            st.error("Le fichier importé ne contient pas toutes les données nécessaires pour la simulation (Budget / Propositions / Copropriétaires).")
        else:
            # Owner selection is required first
            # Load persisted selections and pre-populate session_state where possible
            persisted = load_persisted_state()
            if "persisted_state" not in st.session_state:
                st.session_state["persisted_state"] = persisted

            copro_names = copro["Nom du coproprietaire"].dropna().unique().tolist()
            # restore owner if saved and not already in session
            if persisted.get("selected_owner_main") and ("selected_owner_main" not in st.session_state or not st.session_state.get("selected_owner_main")):
                st.session_state["selected_owner_main"] = persisted.get("selected_owner_main")
            if "total_tantiemes_global" not in st.session_state:
                st.session_state["total_tantiemes_global"] = int(persisted.get("total_tantiemes_global", 10007) or 10007)

            selected_owner = st.selectbox("Sélectionnez un copropriétaire", [""] + copro_names, key="selected_owner_main", on_change=save_persisted_state)
            st.number_input(
                "Total des tantièmes de référence",
                min_value=1,
                step=1,
                key="total_tantiemes_global",
                on_change=save_persisted_state,
            )
            if not selected_owner:
                st.warning("Veuillez sélectionner un copropriétaire pour commencer la simulation.")
            else:
                # Prepare mappings: only keep propositions that have an ID1
                if "ID1" in props.columns:
                    props_ids = props["ID1"].dropna().astype(str).unique().tolist()
                else:
                    props_ids = []

                budget_ids = budget[budget["ID1"].astype(str).isin(props_ids)] if ("ID1" in budget.columns and props_ids) else pd.DataFrame()
                # Show all postes de provision in diagnostics and filters (not only those linked to propositions)
                type_options = budget["Label de la provision"].dropna().unique().tolist() if not budget.empty else []

                # Precompute diagnostics for all provisions once (same for all scénarios)
                tantieme_diagnostics = {}
                for LabelDuPosteDeProvision in type_options:
                    id_series = budget[budget["Label de la provision"] == LabelDuPosteDeProvision]["ID1"].dropna().astype(str).unique().tolist()
                    total_tantieme_for_owner = 0.0
                    if id_series:
                        for id1 in id_series:
                            id_t = map_id_to_tantieme(id1)
                            total_tantieme_for_owner += get_owner_tantieme_for_id(id_t, selected_owner, copro)
                    tantieme_diagnostics[LabelDuPosteDeProvision] = {"id_series": id_series, "total_tantieme": total_tantieme_for_owner}

                # Diagnostic affiché une seule fois sous la sélection du copropriétaire
                if st.checkbox("Montrer diagnostics des tantièmes (pour le copropriétaire sélectionné)"):
                    try:
                        diag_df = pd.DataFrame.from_dict(tantieme_diagnostics, orient="index")
                        st.dataframe(diag_df)
                    except Exception:
                        st.write(tantieme_diagnostics)

                st.markdown("### Saisie du scénario")
                scenario_labels = ["Scénario 1", "Scénario 2", "Scénario 3"]
                active_scenario_label = st.selectbox("Scénario à modifier", scenario_labels, key="active_scenario_selector", on_change=save_persisted_state)
                active_scenario = scenario_labels.index(active_scenario_label) + 1
                active_scenario_key = str(active_scenario)
                filter_key = f"scenario_{active_scenario}_type_filter"

                pers_scen = persisted.get("scenarios", {}).get(active_scenario_key, {})
                if pers_scen.get("filter") and (filter_key not in st.session_state or not st.session_state.get(filter_key)):
                    st.session_state[filter_key] = pers_scen.get("filter")

                control_cols = st.columns([2, 1])
                with control_cols[0]:
                    provision_filter = st.multiselect("Afficher seulement certains postes", type_options, key=filter_key, on_change=save_persisted_state)
                with control_cols[1]:
                    # show_modified_only checkbox removed for simplification
                if st.button("Réinitialiser le scénario actif"):
                    for LabelDuPosteDeProvision in type_options:
                        key = f"scenario_{active_scenario}_props_{normalize_provision_key(LabelDuPosteDeProvision)}"
                        st.session_state.setdefault("provision_label_by_key", {})[key] = LabelDuPosteDeProvision # S'assurer que le mapping est présent
                        st.session_state[key] = [] # Réinitialiser le multiselect à une liste vide
                    save_persisted_state()
                    st.rerun()

                # --- Prestation Details Display Area ---
                st.markdown("---")
                st.subheader("Détails de la prestation sélectionnée")
                if st.session_state['current_viewed_prestation_label']:
                    viewed_prestation_label = st.session_state['current_viewed_prestation_label']
                    viewed_provision_label = st.session_state['current_viewed_provision_label']
                    
                    # Find the prestation in the 'Propositions' DataFrame
                    details_df = props[
                        (props["Label de la prestation"] == viewed_prestation_label)
                    ]
                    
                    if not details_df.empty:
                        detail = details_df.iloc[0]
                        st.write(f"**Poste de provision:** {viewed_provision_label}")
                        st.write(f"**Prestation:** {detail.get('Label de la prestation', 'N/A')}")
                        st.write(f"**Prestataire:** {detail.get('Prestataire', 'N/A')}")
                        st.write(f"**Coût (HT):** {detail.get('Cout', 0):,.2f} €")
                        st.write(f"**Taxes:** {detail.get('Taxes', 0):,.2f} €")
                        st.write(f"**Total TTC:** {detail.get('Total TTC', 0):,.2f} €")
                        st.write(f"**Description:** {detail.get('Description', 'N/A')}")
                    else:
                        st.info("Détails non trouvés pour la prestation sélectionnée.")
                else:
                    st.info("Cliquez sur 'Détails' à côté d'une prestation pour afficher ses informations ici.")
                st.markdown("---")

                visible_types = type_options if not provision_filter else provision_filter

                # Initialize session state for current scenario's prestations if not already done
                for LabelDuPosteDeProvision in visible_types:
                    safe_label = normalize_provision_key(LabelDuPosteDeProvision)
                    key = f"scenario_{active_scenario}_props_{safe_label}"
                    st.session_state.setdefault("provision_label_by_key", {})[key] = LabelDuPosteDeProvision
                    
                    if key not in st.session_state:
                        saved_for_prov = get_selected_prestations(pers_scen.get("prestations_by_provision", {}), LabelDuPosteDeProvision)
                        
                        # Re-calculate prop_options for initialization
                        id_series_for_init = budget[budget["Label de la provision"] == LabelDuPosteDeProvision]["ID1"].dropna().astype(str).unique().tolist()
                        if id_series_for_init:
                            matching_props_for_init = props[props["ID1"].astype(str).isin(id_series_for_init)] if "ID1" in props.columns else pd.DataFrame()
                            prop_options_for_init = matching_props_for_init["Label de la prestation"].dropna().unique().tolist()
                        else:
                            prop_options_for_init = []
                        st.session_state[key] = [p for p in saved_for_prov if p in prop_options_for_init]

                # --- Main Loop for Provisions ---
                for LabelDuPosteDeProvision in visible_types:
                    diag = tantieme_diagnostics.get(LabelDuPosteDeProvision, {})
                    id_series = diag.get("id_series", [])
                    matching_budget = budget[budget["Label de la provision"] == LabelDuPosteDeProvision]
                    
                    budget_amount = 0.0
                    if not matching_budget.empty:
                        budget_amount = float(pd.to_numeric(matching_budget["Provision"], errors="coerce").fillna(0).sum())

                    if id_series:
                        matching_props = props[props["ID1"].astype(str).isin(id_series)] if "ID1" in props.columns else pd.DataFrame()
                        prop_options = matching_props["Label de la prestation"].dropna().unique().tolist()
                    else:
                        matching_props = pd.DataFrame()
                        prop_options = []

                    safe_label = normalize_provision_key(LabelDuPosteDeProvision)
                    key = f"scenario_{active_scenario}_props_{safe_label}"
                    
                    current_selected_props_for_provision = st.session_state.get(key, [])
                    available_props = [p for p in prop_options if p not in current_selected_props_for_provision]

                    st.markdown(f"#### {LabelDuPosteDeProvision} (Budget: {budget_amount:,.2f} €)")
                    
                    col_available, col_selected = st.columns(2)

                    with col_available:
                        st.subheader("Propositions disponibles")
                        if available_props:
                            for i, p in enumerate(available_props):
                                cols_item = st.columns([0.7, 0.3])
                                with cols_item[0]:
                                    st.write(p)
                                with cols_item[1]:
                                    st.button("Ajouter", key=f"add_{safe_label}_{p}_{i}", on_click=add_prestation_to_scenario, args=(LabelDuPosteDeProvision, p, active_scenario))
                                    st.button("Détails", key=f"view_avail_{safe_label}_{p}_{i}", on_click=set_viewed_prestation_details, args=(LabelDuPosteDeProvision, p))
                        else:
                            st.info("Aucune proposition disponible.")

                    with col_selected:
                        st.subheader("Prestations sélectionnées")
                        if current_selected_props_for_provision:
                            for i, p in enumerate(current_selected_props_for_provision):
                                cols_item = st.columns([0.7, 0.3])
                                with cols_item[0]:
                                    st.write(p)
                                with cols_item[1]:
                                    st.button("Retirer", key=f"remove_{safe_label}_{p}_{i}", on_click=remove_prestation_from_scenario, args=(LabelDuPosteDeProvision, p, active_scenario))
                                    st.button("Détails", key=f"view_sel_{safe_label}_{p}_{i}", on_click=set_viewed_prestation_details, args=(LabelDuPosteDeProvision, p))
                        else:
                            st.info("Aucune prestation sélectionnée pour ce poste.")
                    st.markdown("---") # Separator between provisions

                    # Calculate retained cost and delta for display (optional, can be removed for extreme simplification)
                    if current_selected_props_for_provision and not matching_props.empty:
                        retained_cost = pd.to_numeric(
                            matching_props[matching_props["Label de la prestation"].isin(current_selected_props_for_provision)].get("Total TTC", 0),
                            errors="coerce",
                        ).fillna(0).sum()
                    else:
                        retained_cost = budget_amount
                    cost_delta = retained_cost - budget_amount
                    # If you want to display these, you'd need to add them back into the layout,
                    # perhaps as a summary line below each provision's two columns.
                    # For now, they are calculated but not displayed to keep the layout clean.

                # --- Récapitulatif rapide des scénarios ---
                st.markdown("---")
                st.markdown("### Récapitulatif rapide des scénarios")
                
                # Reconstruct active_scenario_prestations_by_prov from st.session_state for the recap
                active_scenario_prestations_by_prov = {}
                for LabelDuPosteDeProvision in type_options:
                    safe_label = normalize_provision_key(LabelDuPosteDeProvision)
                    key = f"scenario_{active_scenario}_props_{safe_label}"
                    active_scenario_prestations_by_prov[LabelDuPosteDeProvision] = st.session_state.get(key, [])

                for i in range(1, 4):
                    if i == active_scenario:
                        selected_map = scenarios[i]["prestations_by_provision"]
                    else:
                        selected_map = persisted.get("scenarios", {}).get(str(i), {}).get("prestations_by_provision", {})

                    selected_lines = []
                    for LabelDuPosteDeProvision in type_options:
                        sels = get_selected_prestations(selected_map, LabelDuPosteDeProvision)
                        if sels:
                            selected_lines.append(f"- {LabelDuPosteDeProvision}: {', '.join(sels)}")

                    with st.expander(f"Scénario {i} ({len(selected_lines)} poste(s) modifié(s))", expanded=(i == active_scenario)):
                        if selected_lines:
                            st.write("\n".join(selected_lines))
                        else:
                            st.write("(aucune prestation sélectionnée)")

                st.markdown(f"Vous avez sélectionné le copropriétaire : **{selected_owner}**.")

elif page == "Simulation des charges":
    #Titre de la page
    st.header("Simulation des charges")
    st.write("Ici vous pouvez visualiser l'impact des scénarios sur les charges annuelles et mensuelles du copropriétaire sélectionné.")
    #On controle qu'un fichier de parametrage a été importé et que les feuilles nécessaires sont présentes
    if st.session_state.get("uploaded_data") is None:
        st.warning("Aucun fichier importé. Allez sur la page 'Importer le fichier' pour ajouter les données.")
    else:
    #A partir d'ici on a les données 

        data = st.session_state["uploaded_data"]
        budget = data.get("Budget", pd.DataFrame())
        props = data.get("Propositions", pd.DataFrame())
        copro = data.get("Copropriétaires", pd.DataFrame())

        if budget.empty or copro.empty:
            st.error("Les feuilles 'Budget' et 'Copropriétaires' sont nécessaires pour cette simulation.")
        else:
        #Création d'un slider de consommation individuelle de chauffage pour ajuster les tantièmes utilisés dans le calcul des charges
            # consumption slider 0-200%
            cons_frac = st.slider("Consommation individuelle de chauffage (%)", 0, 200, 100) / 100.0

            # load persisted scenarios and restore selected owner if missing
            persisted = load_persisted_state()
            scenarios_persist = persisted.get("scenarios", {})
            
            
            if "selected_owner_main" not in st.session_state or not st.session_state.get("selected_owner_main"):
                if persisted.get("selected_owner_main"):
                    st.session_state["selected_owner_main"] = persisted.get("selected_owner_main")
            if "total_tantiemes_global" not in st.session_state:
                st.session_state["total_tantiemes_global"] = int(persisted.get("total_tantiemes_global", 10007) or 10007)
            total_tantiemes_reference = int(st.session_state.get("total_tantiemes_global", 10007) or 10007)

            ###----------------------------------------------------------------------
            # Construire les intitulés de lignes du tableau à partir des provisions
            ###----------------------------------------------------------------------
            
            budget_items = []
            for _, brow in budget.iterrows():
                label = brow.get("Label de la provision")
                if pd.isna(label):
                    continue
                prov_amount = brow.get("Provision", 0)
                id1_val = brow.get("ID1") if "ID1" in brow.index else None
                id_series_row = []
                if pd.notna(id1_val):
                    id_series_row = [str(id1_val)]

                seg_field = brow.get("Segment", "")
                if pd.isna(seg_field) or str(seg_field).strip() == "":
                    segments = [""]
                else:
                    segments = [s.strip() for s in str(seg_field).split(",")]

                for seg in segments:
                    budget_items.append({
                        "segment": seg,
                        "label": label,
                        "provision": prov_amount,
                        "id_series": id_series_row,
                    })

            ###----------------------------------------------------------------------
            #Les calculs de charges se font ici
            ###----------------------------------------------------------------------
            rows = []
            calc_details = []
            for item in budget_items:
                LabelDuPosteDeProvision = item["label"]
                MontantDeLaProvision = float(item.get("provision", 0) or 0)
                segment_label = item.get("segment", "")
                id_series = item.get("id_series", [])
                id_display = ", ".join(id_series)

                owner = st.session_state.get("selected_owner_main", "")
                owner_tantieme = 0.0
                total_tantiemes = total_tantiemes_reference
                #Récupération des tantièmes du copropriétaire et du total pour le poste de provision
                for id1 in id_series:
                    id_t = map_id_to_tantieme(id1)
                    owner_tantieme += get_owner_tantieme_for_id(id_t, owner, copro)

                owner_tantieme_formula_part = "" # Initialize
                # heating adjustment
                heating_ids = {"GAZ", "GRANULEBOIS"}
                if any(id1 in heating_ids for id1 in id_series):
                    owner_tantieme_used = owner_tantieme * 0.3 + 0.7 * owner_tantieme * cons_frac
                    # Explicitly show the heating adjustment calculation in the formula
                    owner_tantieme_formula_part = f"({owner_tantieme:,.2f} x 0.3 + {owner_tantieme:,.2f} x 0.7 x {cons_frac:,.2f})"
                else:
                    owner_tantieme_used = owner_tantieme
                    # Simple tantieme value for the formula
                    owner_tantieme_formula_part = f"{owner_tantieme:,.2f}"

                owner_share = (owner_tantieme_used / total_tantiemes) if total_tantiemes else 0
                owner_provision_indiv_annual = MontantDeLaProvision * owner_share

                row = {
                    "Segment": segment_label, 
                    "Provision": LabelDuPosteDeProvision, 
                    "Provisions - Résidence (Annuel)": MontantDeLaProvision, 
                    "Provisions - Individuel (Annuel)": owner_provision_indiv_annual,
                    "Provisions - Individuel (Mensuel)": owner_provision_indiv_annual / 12.0
                }
                calc_details.append({
                    "Vue": "Provision",
                    "Segment": segment_label,
                    "Provision": LabelDuPosteDeProvision,
                    "ID1": id_display,
                    "Prestations retenues": "Budget initial",
                    "Lignes devis trouvées": "",
                    "Tantièmes": owner_tantieme,
                    "Tantièmes utilisés": owner_tantieme_used,
                    "Tantièmes total": total_tantiemes,
                    "Quote-part": owner_share,
                    "Coût résidence": MontantDeLaProvision,
                    "Annuel copro": owner_provision_indiv_annual,
                    "Mensuel copro": owner_provision_indiv_annual / 12.0,
                    "Formule": f"{MontantDeLaProvision:,.2f} € x {owner_tantieme_formula_part} / {total_tantiemes:,.0f}",
                })

                for si in range(1, 4):
                    scen = scenarios_persist.get(str(si), {})
                    selected_map = scen.get("prestations_by_provision", {})
                    sel_props = get_selected_prestations(selected_map, LabelDuPosteDeProvision)

                    if sel_props and not props.empty:
                        matching = props[props["Label de la prestation"].isin(sel_props)]
                        if "ID1" in props.columns and id_series:
                            matching = matching[matching["ID1"].astype(str).isin(id_series)]
                        sum_selected = pd.to_numeric(matching.get("Total TTC", 0), errors="coerce").fillna(0).sum()
                        count_selected = matching.shape[0]
                    else:
                        sum_selected = 0.0
                        count_selected = 0

                    if count_selected == 0:
                        residence_value = MontantDeLaProvision
                    else:
                        residence_value = sum_selected

                    if count_selected == 0:
                        owner_indiv_annual = owner_provision_indiv_annual
                    else:
                        owner_indiv_annual = owner_share * sum_selected

                    owner_monthly = owner_indiv_annual / 12.0

                    row[f"Scénario {si} - Résidence"] = residence_value
                    row[f"Scénario {si} - Annuel copro"] = owner_indiv_annual
                    row[f"Scénario {si} - Mensuel copro"] = owner_monthly
                    calc_details.append({
                        "Vue": f"Scénario {si}",
                        "Segment": segment_label,
                        "Provision": LabelDuPosteDeProvision,
                        "ID1": id_display,
                        "Prestations retenues": ", ".join(sel_props) if sel_props else "Budget initial",
                        "Lignes devis trouvées": count_selected if sel_props else "",
                        "Tantièmes": owner_tantieme,
                        "Tantièmes utilisés": owner_tantieme_used,
                        "Tantièmes total": total_tantiemes,
                        "Quote-part": owner_share,
                        "Coût résidence": residence_value,
                        "Annuel copro": owner_indiv_annual,
                        "Mensuel copro": owner_monthly,
                        "Formule": f"{residence_value:,.2f} € x {owner_tantieme_formula_part} / {total_tantiemes:,.0f}",
                    })

                rows.append(row)

            df_out = pd.DataFrame(rows)
            # reorder columns for readability: Segment, Provision, Provisions columns, then scenarios
            others = [c for c in df_out.columns if c not in ("Provision", "Segment")]
            df_out = df_out[["Segment", "Provision"] + others]

            # display with larger height using two-level column headers
            # keep 'Segment' and 'Provision' as text; numeric columns are the rest
            numeric_cols = [c for c in df_out.columns if c not in ("Provision", "Segment")]
            df_display = df_out.copy()
            for c in numeric_cols:
                df_display[c] = pd.to_numeric(df_display[c], errors="coerce").fillna(0)

            # Add totals row for numeric columns
            df_tot = df_display.copy()
            if numeric_cols:
                totals = {c: df_tot[c].sum() for c in numeric_cols}
            else:
                totals = {}
            total_row = {"Segment": "", "Provision": "Total de charges"}
            for c, v in totals.items():
                total_row[c] = v
            df_display = pd.concat([df_display, pd.DataFrame([total_row])], ignore_index=True)

            # Allow user to pick which view to show (Provision or one Scenario)
            if "display_mode" not in st.session_state:
                scenario_1 = scenarios_persist.get("1", {})
                scenario_1_selections = scenario_1.get("prestations_by_provision", {}).values()
                st.session_state["display_mode"] = "Scénario 1" if any(scenario_1_selections) else "Provision"
            display_mode = st.selectbox("Afficher", ["Provision", "Scénario 1", "Scénario 2", "Scénario 3"], key="display_mode")

            # choose which numeric columns to display depending on mode
            if display_mode == "Provision":
                display_numeric_cols = [c for c in df_display.columns if c.startswith("Provisions -")]
            else:
                # map 'Scénario 1' -> columns starting with 'Scénario 1 - '
                scen_label = display_mode
                display_numeric_cols = [c for c in df_display.columns if c.startswith(scen_label + " -")]

            # Build the DataFrame to render (only Segment, Provision plus chosen numeric cols)
            display_cols = ["Segment", "Provision"] + display_numeric_cols
            df_for_html = df_display[display_cols].copy()
            for c in display_numeric_cols:
                df_for_html[c] = df_for_html[c].map(lambda x: f"{x:,.2f} €")

            # Build MultiIndex columns: first level (group), second level (label)
            tuples = []
            for col in df_for_html.columns:
                if col == "Segment":
                    tuples.append(("", "Segment"))
                elif col == "Provision":
                    tuples.append(("", "Provision"))
                elif col.startswith("Provisions -"):
                    # e.g. 'Provisions - Résidence (Annuel)'
                    second = col.replace("Provisions - ", "")
                    tuples.append(("Provisions", second))
                elif col.startswith("Scénario"):
                    # 'Scénario X - Résidence' etc.
                    parts = col.split(" - ")
                    if len(parts) == 2:
                        tuples.append((parts[0], parts[1]))
                    else:
                        tuples.append((col, ""))
                else:
                    tuples.append(("", col))

            df_for_html.columns = pd.MultiIndex.from_tuples(tuples)

            # Render as HTML to preserve multi-level headers and allow scrolling
            html = df_for_html.to_html(index=False, border=0, classes="table table-striped table-sm")
            # small CSS to keep it readable in Streamlit
            style = """
            <style>
            .table {width:100%; border-collapse:collapse;}
            .table th, .table td {padding:6px 8px; border:1px solid #ddd; text-align:left}
            .table thead th {background:#fafafa;}
            </style>
            """
            # Calcul de la hauteur dynamique pour éviter l'ascenseur (environ 40px par ligne + 100px pour les entêtes multi-niveaux)
            table_height = (len(df_for_html) * 40) + 100
            components.html(style + html, height=table_height)

            st.markdown("### Détail des calculs")
            df_calc_details = pd.DataFrame(calc_details)
            df_calc_view = df_calc_details[df_calc_details["Vue"] == display_mode].copy()
            
            detail_numeric_cols = [
                "Tantièmes",
                "Tantièmes utilisés",
                "Quote-part",
                "Coût résidence",
                "Annuel copro",
                "Mensuel copro",
            ]

            if not df_calc_view.empty:
                # S'assurer que les colonnes sont numériques pour le calcul du total
                for col in detail_numeric_cols:
                    df_calc_view[col] = pd.to_numeric(df_calc_view[col], errors='coerce').fillna(0)

                # Calcul des sommes pour la ligne de total
                sums = df_calc_view[detail_numeric_cols].sum()
                
                total_detail_row = {
                    "Vue": display_mode,
                    "Segment": "",
                    "Provision": "TOTAL GÉNÉRAL",
                    "ID1": "",
                    "Prestations retenues": "",
                    "Lignes devis trouvées": "",
                    "Tantièmes": sums["Tantièmes"],
                    "Tantièmes utilisés": sums["Tantièmes utilisés"],
                    "Tantièmes total": total_tantiemes_reference,
                    "Quote-part": None, # Pas de sens de sommer des ratios
                    "Coût résidence": sums["Coût résidence"],
                    "Annuel copro": sums["Annuel copro"],
                    "Mensuel copro": sums["Mensuel copro"],
                    "Formule": "",
                }
                
                # Construction du DataFrame final pour l'affichage
                df_calc_display = pd.concat([df_calc_view, pd.DataFrame([total_detail_row])], ignore_index=True)
                df_calc_display = df_calc_display.drop(columns=["Vue"])

                # Formatage des colonnes numériques pour un affichage propre
                for col in detail_numeric_cols + ["Tantièmes total"]:
                    if col in df_calc_display.columns:
                        if col == "Quote-part":
                            df_calc_display[col] = df_calc_display[col].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "")
                        else:
                            df_calc_display[col] = df_calc_display[col].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) and x != 0 else ("0.00 €" if x == 0 else ""))
                
                # Calcul de la hauteur dynamique pour le dataframe (environ 35px par ligne + entête)
                calc_height = (len(df_calc_display) + 1) * 35 + 5
                st.dataframe(df_calc_display, use_container_width=True, hide_index=True, height=calc_height)
            else:
                st.info("Aucune donnée à afficher pour ce scénario.")
