##NBA Post Season 2020/21 Scrapper

Scrappe team, statistics and saleries for team off NBA Post Season 2020/21 from espn.com.

Requirements: Python 3.6

###Instructions:

If don't have python get it from python.org.

Change into the directory containing this repo and enter `divae`

You can install all required packages via (create a virtual env https://docs.python.org/3/library/venv.html):

    pip install -r requirements.txt

You can run the code with:

    python app.py


For details on arguments:

    python app.py -h

Output:

    usage: app.py [-h] [--refresh] [--print_csv]
    
    Get Top 10 NBA Post Season 2020/21 Players by price per point. Datasaved to
    nba.db if file doesnt exits or --refresh option is used.
    
    optional arguments:
      -h, --help   show this help message and exit
      --refresh    Refresh nba.db if it already exits.
      --print_csv  Print comma separated data instead of command line friendly.

An sqlite3 database file is created in the directory (nba.db).

You can also use Docker to run the python script although the `nba.db` will not persist in consecutive runs:

    docker build -t nba .

And run:

    docker run nba