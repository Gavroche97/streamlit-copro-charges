import streamlit as st
import pandas as pd

# Initialize the Streamlit app
st.title("Calculateur de Charges de Copropriété")

# Set up the layout for the user interface
st.write("Bienvenue dans l'application de calcul des charges de copropriété.")
st.write("Importez un fichier Excel (.xlsx) au format attendu pour charger vos provisions.")

expected_columns = ["provision_name", "amount", "frequency"]

st.markdown(
    """
    ### Format attendu
    Le fichier Excel doit contenir au minimum ces colonnes :
    - `provision_name`
    - `amount`
    - `frequency`
    """
)

uploaded_file = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            st.error("Le fichier Excel ne contient pas toutes les colonnes requises.")
            st.write("Colonnes manquantes :", ", ".join(missing))
            st.write("Colonnes détectées :", ", ".join(df.columns.tolist()))
        else:
            st.success("Fichier Excel importé avec succès !")
            st.dataframe(df[expected_columns].head(50))
            st.write("Nombre de lignes importées :", len(df))
    except Exception as exc:
        st.error("Impossible de lire le fichier Excel.")
        st.write(str(exc))
else:
    st.info("Veuillez importer un fichier Excel au format correct pour continuer.")
