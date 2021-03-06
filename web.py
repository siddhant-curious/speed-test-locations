import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug.contrib.fixers import ProxyFix
import csv
import urllib.request

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'speed.db'),
    SECRET_KEY='developmentkey',
    USERNAME='admin',
    PASSWORD='default'
))
#app.config.from_envvar('SPEED_SETTINGS', silent=True)

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.cli.command('ucsv')
def updatecsv_command():
    con = sqlite3.connect(app.config['DATABASE'])
    stats = csv.reader(open("speedtest.csv"))
    con.execute('delete from entries')
    con.executemany("insert into entries (date,country,region,city,latitude,longitude,ispName,ispNameRaw,download,upload,latency,testId) values (?,?,?,?,?,?,?,?,?,?,?,?)",((rec[0],rec[2],rec[3],rec[4],rec[5],rec[6],rec[12],rec[13],rec[15],rec[16],rec[17],rec[19]) for rec in stats))
    con.commit()
    print('Updated The Table Entries')

def updatecsv():
    con = sqlite3.connect(app.config['DATABASE'])
    stats = csv.reader(open("speedtest.csv"))
    con.execute('delete from entries')
    con.executemany("insert into entries (date,country,region,city,latitude,longitude,ispName,ispNameRaw,download,upload,latency,testId) values (?,?,?,?,?,?,?,?,?,?,?,?)",((rec[0],rec[2],rec[3],rec[4],rec[5],rec[6],rec[12],rec[13],rec[15],rec[16],rec[17],rec[19]) for rec in stats))
    con.commit()
    print('Updated The Table Entries')

@app.cli.command('udwl')
def download_csv():
    url = "https://account.speedtestcustom.com/api/test/24578/export/latest?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik1qaEVSVFF4TkRVeU5qTXhRVE0zUWtJeFJETkNRVVk1UlRaQ016VkJNemhHT1RNMU5rUkNRUSJ9.eyJpc3MiOiJodHRwczovL29va2xhLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw1OWIyZWQxN2QxYTI1YzZiODA4MThjYmIiLCJhdWQiOlsiaHR0cHM6Ly9hcGkuc3QtY29ubmVjdC5jb20iLCJodHRwczovL29va2xhLmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE1MTI0MDk3MTgsImV4cCI6MTUxMjQ5NjExOCwiYXpwIjoielVnRHhzc2lHdXc2WGxjUHFFemxlS1RBOFE5Z2dfMzkiLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIGFkZHJlc3MgcGhvbmUiLCJndHkiOiJwYXNzd29yZCJ9.TxSRfA9k_86TBpTOpU7GLspc_GqvUNMCSejv1u8HSIaQRFtukqlQxCTOZdP2D1tjuillmyjDpWPCK4jc-fKsDeNLwniFiU8UajgwqOBSPDpMZ40NQcOB7ZbgKCKJrNSuxcjpirGSiiBlPnRjeAEHHeoZE0RT5YR02q_RlzJQcE3rHlh39drb96KOrcMfNUXx6Lk5SRf3LruiNN7mSkBEM7ivUf6-9IWCpMXjI6Yk0tK03Xx_geYFFMo16f_tORUC1laIkTiWvOtNBCGH9jJ2QzlJe5J8tIZD9JA_hCz4-s0NBxWKQHfeyjchbPRZ2nGNGgywB2fTZLg1YClgMgiang"

    file_name="speedtest.csv"
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        data = response.read() # a `bytes` object
        out_file.write(data)

    print('Downloaded The CSV File')
    updatecsv()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search/',methods=["GET"])
def search():
    query = request.args.get('query', '')
    if query:
         print ("q = ",query)
         db = get_db()
         cur = db.execute('select ispName,avg(download) as download,avg(upload) as upload,avg(latency) as latency,count(*) as tests from entries where region = ? or city = ? COLLATE NOCASE group by ispName ',[query,query])
         entries = cur.fetchall()
         found = False
         if len(entries)>0:
             found = True
         else:
             found = False
         return render_template('locationsearch.html',found=found,entries=entries,loc=query,search=True)
    return render_template('locationsearch.html')

@app.route('/result/')
@app.route('/result/<location>/<ispname>/')
def result(location=None,ispname=None):
    if location and ispname:
        print (location,ispname)
        db = get_db()
        cur = db.execute('select date,download,upload,latency,testId from entries where (ispName=? or ispNameRaw=?) and (region=? or city=?)',[ispname,ispname,location,location])
        results = cur.fetchall()
        found = False
        if len(results)>0:
            found = True
            for i in results:
                for k in i:
                    print (k)
        else:
            found = False
        return render_template('results.html',found=found,results=results,loc=location,isp=ispname,search=True)
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/siddhantmusttest')
def test():
    return 'Test 101'


app.wsgi_app = ProxyFix(app.wsgi_app)
