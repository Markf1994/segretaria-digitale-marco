import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SHEET_ID = "SegretariaDigitale"
CREDS_FILE = "segretariamarco-nuovo.json"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
client = gspread.authorize(creds)

def carica_df(sheet_name):
    sh = client.open(SHEET_ID)
    worksheet = sh.worksheet(sheet_name)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

def salva_df(df, sheet_name):
    sh = client.open(SHEET_ID)
    worksheet = sh.worksheet(sheet_name)
    worksheet.clear()
    worksheet.update([df.columns.tolist()] + df.values.tolist())
