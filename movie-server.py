import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import threading
import yify
import subprocess
import re
import urllib3
import json
from requests import get


def worker(sheet, row):
    data = sheet.cell(row, 1).value
    response_cells = [gspread.models.Cell(row, 2, 'No movies found')]
    print('working on ' + str(row) + ': ' + data)
    movies = search_movies(data)
    if movies:
        response_cells[0].value = str(len(movies)) + ' found:'
        for i, m in enumerate(movies):
            response_cells.append(gspread.models.Cell(row, 3 + i, m['title_long']))
        sheet.update_cells(response_cells)
        # wait for answer (by deleting the desired cell)
        while all([sheet.cell(row, i).value for i in range(3, 3 + len(movies))]):
            time.sleep(2)
        desired_movie = None
        for i in range(movies):
            desired_movie = movies[i]
            if not sheet.cell(row, i + 3).value: 
                break
       # TODO: deal with the torrent qualities 
       # TODO: start download
       # TODO: monitor download
    else:
        sheet.update_cells(response_cells)


def search_movies(search_str):
    quality = 'All'
    minimum_rating = 0
    genre = ''

    url = "https://yts.ag/api/v2/list_movies.json"
    url = url+ '?' +  urllib3.request.urlencode({
        'minimum_rating' : minimum_rating, 
        'quality' : quality, 
        'query_term' : search_str, 
        'genre' : genre})
    resp = get(url, timeout=5)
    return json.loads(resp.text).get('data').get('movies')
    

if __name__ == '__main__':
    SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name('spreadsheet-220015-58b6c82bc04b.json', SCOPE)

    gc = gspread.authorize(CREDENTIALS)
    wks = gc.open_by_key('1fith6AF1l9Ws_8nthr-xaCaR_4_Fv2QyR5ePA_2lwpM').sheet1
    
    with open('moviecount', 'r') as fp:
        movie_count = int(fp.read())
    while True:
        print(movie_count)
        if len(wks.col_values(1)) - 1 > movie_count:
            threading.Thread(target=worker, args=(wks, movie_count + 2)).start()
            movie_count += 1
            print('New entry')
            with open('moviecount', 'w') as fp:
                fp.write(str(movie_count) + '\n')

        time.sleep(5)
