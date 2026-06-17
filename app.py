import streamlit as st
import pandas as pd

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

sidebar_title = st.sidebar.title("Copro Charges")
page = st.sidebar.radio("Navigation", ["Importer le fichier", "Simulation des charges"])

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
    st.write("Téléchargez ci-dessous le modèle Excel `Les Terrasses de Gallieni.xlsx` et utilisez-le pour préparer votre import.")
    st.write("Le fichier doit contenir plusieurs feuilles, comme indiqué dans le modèle.")

    download_path = "data/Les Terrasses de Gallieni.xlsx"
    try:
        with open(download_path, "rb") as f:
            st.download_button(
                label="Télécharger le modèle Excel",
                data=f,
                file_name="Les Terrasses de Gallieni.xlsx",
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
        st.write("Vous pouvez maintenant passer à la page de simulation des charges.")
    else:
        st.info("Veuillez importer un fichier Excel au format correct pour continuer (utilisez le modèle téléchargé ci-dessus).")

elif page == "Simulation des charges":
    st.write("Sélectionnez les propositions et le copropriétaire pour simuler la répartition des charges.")
    if st.session_state["uploaded_data"] is None:
        st.warning("Aucun fichier importé. Veuillez d'abord importer le fichier Excel sur la page 'Importer le fichier'.")
    else:
        data = st.session_state["uploaded_data"]
        props = data.get("Propositions", pd.DataFrame())
        copro = data.get("Copropriétaires", pd.DataFrame())
        budget = data.get("Budget", pd.DataFrame())

        if props.empty or copro.empty:
            st.error("Le fichier importé ne contient pas toutes les données nécessaires pour la simulation.")
        else:
            copro_names = copro["Nom du coproprietaire"].dropna().unique().tolist()
            selected_owner = st.selectbox("Sélectionnez un copropriétaire", copro_names)
            selected_ids = st.multiselect(
                "Choisissez les propositions à inclure",
                props["Label de la prestation"].fillna("").tolist(),
                default=props["Label de la prestation"].head(3).tolist(),
            )

            selected_props = props[props["Label de la prestation"].isin(selected_ids)]
            total_selected = selected_props["Total TTC"].fillna(0).sum()
            total_budget = budget["Provision"].fillna(0).sum() if "Provision" in budget.columns else 0.0

            owner_row = copro[copro["Nom du coproprietaire"] == selected_owner].head(1)
            owner_tantiemes = float(owner_row["Tantièmes copropriété"].iloc[0]) if not owner_row.empty and "Tantièmes copropriété" in owner_row.columns else 0.0
            total_tantiemes = float(copro["Tantièmes copropriété"].sum()) if "Tantièmes copropriété" in copro.columns else 0.0
            owner_share = (total_selected * owner_tantiemes / total_tantiemes) if total_tantiemes else 0.0

            st.markdown("### Résumé des charges")
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Propositions sélectionnées")
                if selected_props.empty:
                    st.info("Aucune proposition sélectionnée.")
                else:
                    st.dataframe(selected_props[["Type de prestation", "Label de la prestation", "Prestataire", "Cout", "Taxes", "Total TTC"]].reset_index(drop=True))
            with col2:
                st.subheader("Synthèse")
                summary = {
                    "Champ": [
                        "Total charges propositions",
                        "Total provisions Budget",
                        "Total charges résidence",
                        "Tantièmes propriétaire",
                        "Part du propriétaire"
                    ],
                    "Valeur": [
                        f"{total_selected:.2f} €",
                        f"{total_budget:.2f} €",
                        f"{total_selected + total_budget:.2f} €",
                        f"{owner_tantiemes:.2f}",
                        f"{owner_share:.2f} €"
                    ]
                }
                st.table(pd.DataFrame(summary))

            st.markdown("### Détails copropriétaire")
            st.write(owner_row.drop(columns=[col for col in owner_row.columns if col not in ["Batiment", "Label de lot", "Nom du coproprietaire", "Tantièmes copropriété", "Numéro de lot", "Lot Nexity", "Etage"]]).reset_index(drop=True))
