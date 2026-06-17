import pandas as pd, json
path='data/Les Terrasses de Gallieni.xlsx'
xl = pd.ExcelFile(path)
info = {'sheets': xl.sheet_names, 'sheets_info': {}}
for s in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=s)
    info['sheets_info'][s] = {'columns': df.columns.tolist(), 'preview': df.head(3).to_dict(orient='records')}
print(json.dumps(info, ensure_ascii=False, indent=2))
