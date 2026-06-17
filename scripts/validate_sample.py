import pandas as pd
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
path='data/Les Terrasses de Gallieni.xlsx'
xl=pd.ExcelFile(path)
print('Sheets found:', xl.sheet_names)
missing_sheets=[s for s in expected_sheets.keys() if s not in xl.sheet_names]
print('Missing sheets:', missing_sheets)
for sheet, cols in expected_sheets.items():
    df=pd.read_excel(xl, sheet_name=sheet)
    missing_cols=[c for c in cols if c not in df.columns]
    print(f"Sheet {sheet} missing cols: {missing_cols}")
print('Done')
