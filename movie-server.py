import gspread
from oauth2client import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('spreadsheet-220015-83b4ef286d02.json', scope)


