import streamlit as st
import pandas as pd

# Initialize the Streamlit app
st.title("Calculateur de Charges de Copropriété")

# Set up the layout for the user interface
st.write("Bienvenue dans l'application de calcul des charges de copropriété.")
st.write("Téléchargez ci-dessous le modèle Excel `Les Terrasses de Gallieni.xlsx` (le fichier exact présent dans le dossier `data`) et utilisez-le pour préparer votre import.")

# Expected multi-sheet format (must match the template in data/Les Terrasses de Gallieni.xlsx)
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

st.markdown(
    """
    ### Format attendu (multi-feuilles)
    Le fichier Excel doit contenir les feuilles suivantes et les colonnes indiquées dans chacune :
    - `Revenus`
    - `Budget`
    - `Propositions`
    - `Copropriétaires`
    - `Règles`
    
    Téléchargez le modèle ci‑dessus pour voir l'exemple exact.
    """
)

download_path = "data/Les Terrasses de Gallieni.xlsx"
try:
    with open(download_path, "rb") as f:
        st.download_button(
            label="Télécharger le modèle Excel (fichier exact dans data)",
            data=f,
            file_name="Les Terrasses de Gallieni.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
except FileNotFoundError:
    st.error(f"Le modèle '{download_path}' est introuvable. Assurez-vous qu'il existe dans le dossier data.")

uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
if uploaded_file is not None:
    try:
        xl = pd.ExcelFile(uploaded_file)
        missing_sheets = [s for s in expected_sheets.keys() if s not in xl.sheet_names]
        if missing_sheets:
            st.error("Le fichier Excel ne contient pas toutes les feuilles requises.")
            st.write("Feuilles manquantes :", ", ".join(missing_sheets))
            st.write("Feuilles détectées :", ", ".join(xl.sheet_names))
        else:
            sheet_errors = {}
            previews = {}
            for sheet, expected_cols in expected_sheets.items():
                df_sheet = pd.read_excel(xl, sheet_name=sheet)
                missing_cols = [c for c in expected_cols if c not in df_sheet.columns]
                if missing_cols:
                    sheet_errors[sheet] = missing_cols
                else:
                    previews[sheet] = df_sheet[expected_cols].head(50)

            if sheet_errors:
                st.error("Certaines feuilles ne contiennent pas les colonnes attendues.")
                for s, cols in sheet_errors.items():
                    st.write(f"Feuille '{s}' - colonnes manquantes : {', '.join(cols)}")
            else:
                st.success("Fichier Excel importé et validé avec succès !")
                for s, df_preview in previews.items():
                    st.subheader(f"Aperçu - {s}")
                    st.dataframe(df_preview)
                st.write("Import complet.")
    except Exception as exc:
        st.error("Impossible de lire ou d'analyser le fichier Excel. Vérifiez le format et la compatibilité des feuilles.")
        st.write(str(exc))
else:
    st.info("Veuillez importer un fichier Excel au format correct pour continuer (utilisez le modèle téléchargé ci-dessus).")
