import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('spreadsheet-220015-58b6c82bc04b.json', scope)

gc = gspread.authorize(credentials)

wks = gc.open_by_key('1fith6AF1l9Ws_8nthr-xaCaR_4_Fv2QyR5ePA_2lwpM').sheet1

print(wks.get_all_records)
