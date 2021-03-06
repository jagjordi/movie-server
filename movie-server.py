import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from threading import Thread
import subprocess
import re
import urllib3
import json
from requests import get


SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/movie-server/spreadsheet-220015-0475fe052e80.json', SCOPE)
TRANSMISSION_USER = 'transmission'
TRANSMISSION_PASSWORD = 'transmission'
DOWNLOAD_DIR = '/media/pi/Elements/Movies'


def worker(sheet, row):
    while True:
        try:
            data = sheet.cell(row, 1).value
            break
        except:
            sleep(10)
    response_cells = [gspread.models.Cell(row, 2, 'No movies found')]
    print('working on ' + str(row) + ': ' + data)
    movies = search_movies(data)
    if movies:
        if len(movies) == 1:
            desired_movie = movies[0]
        else:
            # write number of movies found
            response_cells[0].value = str(len(movies)) + ' found:'
            for i, m in enumerate(movies):
                response_cells.append(gspread.models.Cell(row, 3 + i, m['title_long']))
            while True:
                try:
                    sheet.update_cells(response_cells)
                    break
                except:
                    sleep(10)

            # wait for answer (by deleting the desired cell)
            while True:
                try
                    while all([sheet.cell(row, i).value for i in range(3, 3 + len(movies))]):
                        time.sleep(2)
                    break
                except:
                    sleep(10)
            desired_movie = None
            while True:
                try:
                    for i in range(len(movies)):
                        desired_movie = movies[i]
                        if not sheet.cell(row, i + 3).value: 
                            break
                    break
                except:
                    sleep(10)
            
            for i, m in enumerate(movies):
                response_cells.append(gspread.models.Cell(row, 3 + i, ''))

            while True:
                try:
                    sheet.update_cells(response_cells)
                    break
                except:
                    sleep(10)
            
        name = desired_movie['title_long']

        # find apropiate torrent
        if len(desired_movie['torrents']) == 1:
            torrent = desired_movie['torrents'][0]
        else:
            torrents = [t for t in desired_movie['torrents'] if '1080p' in t['quality']]
            if not torrents:
                torrents = [t for t in desired_movie['torrents'] if '720p' in t['quality']]
            if not torrents:
                torrent = torrents[0]
            else:
                torrent = torrents[0]
        
        # start download
        while True:
            try:
                sheet.update_cells([gspread.models.Cell(row, 1, desired_movie['title'])])
                break
            except:
                sleep(10)
        call = 'transmission-remote -n \'' + TRANSMISSION_USER + ':' + TRANSMISSION_PASSWORD + '\' -a \'' + torrent['url'] + '\' -w \'' + DOWNLOAD_DIR + '\''
        proc = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
        resp, _ = proc.communicate()
        print(resp)
        if b'success' in resp:
            progress = '0%'
            call = 'transmission-remote -n \'' + TRANSMISSION_USER + ':' + TRANSMISSION_PASSWORD + '\' -t \'' + torrent['hash'] + '\' -l'
            while progress != '100%':
                proc = subprocess.Popen(call, stdout=subprocess.PIPE, shell=True)
                resp, _ = proc.communicate()
                print(resp)
                resp = resp.splitlines()[1].decode("utf-8")
                progress = re.search(' *[0-9]+% +', resp).group(0).strip()
                while True:
                    try:
                        sheet.update_cells([gspread.models.Cell(row, 2, progress)])
                        break
                    except:
                        sleep(10)
                time.sleep(10)
            print(desired_movie['title'] + ' ended')
        else:  # error adding torrent
            while True:
                try:
                    sheet.update_cells([gspread.models.Cell(row, 2, 'error adding torrent')])
                    break
                except:
                    sleep(10)
    else:  # movies not found
        while True:
            try:
                sheet.update_cells(response_cells)
                break
            except:
                sleep(10)


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
    gc = gspread.authorize(CREDENTIALS)
    wks = gc.open_by_key('1fith6AF1l9Ws_8nthr-xaCaR_4_Fv2QyR5ePA_2lwpM').sheet1
    
    with open('/home/pi/movie-server/moviecount', 'r') as fp:
        movie_count = int(fp.read())
    while True:
        print(movie_count)
        if len(wks.col_values(1)) - 1 > movie_count:
            Thread(target=worker, args=(wks, movie_count + 2)).start()
            movie_count += 1
            print('New entry')
            with open('/home/pi/movie-server/moviecount', 'w') as fp:
                fp.write(str(movie_count) + '\n')

        time.sleep(5)
