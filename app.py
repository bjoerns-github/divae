import requests_html
import time
import pandas as pd
import sqlite3
import os.path
import argparse

pd.options.mode.chained_assignment = None


def check_if_db_exits():
    return os.path.exists('nba.db')


def get_saleries(session):
    """
    Get saleries of all players in season 2020/21
    :param session: DB connection
    :return: DataFrame with saleries
    """
    print('Getting Saleries Page: 1')
    r = session.get('http://www.espn.com/nba/salaries/_/year/2021/seasontype/4')
    pages = int(r.html.xpath("//*[contains(@class,'page-numbers')]")[0].text.split('of ')[1])
    tab = r.html.xpath("//*[contains(@class,'tablehead')]")[0].html
    data = pd.read_html(tab)[0]
    data = data[data[0] != 'RK']

    for i in range(2, pages + 1):
        print('Getting Saleries Page: ' + str(i))
        time.sleep(1)
        r = session.get('http://www.espn.com/nba/salaries/_/page/' + str(i) + '/seasontype/4')
        tab = r.html.xpath("//*[contains(@class,'tablehead')]")[0]
        df = pd.read_html(tab.html)[0]
        df = df[df[0] != 'RK']
        data = data.append(df)
    data = data.rename(columns={1: 'NamePos', 2: 'Team', 3: 'Salery'})
    data['Name'] = data['NamePos'].str.split(', ', expand=True)[0]
    data['Position'] = data['NamePos'].str.split(', ', expand=True)[1]
    data['Team'] = data['Team'].str.lower()
    saleries = data[['Name', 'Team', 'Position', 'Salery']]
    saleries.loc[:, 'Salery'] = pd.to_numeric(saleries.loc[:, 'Salery'].str.replace('$', '').str.replace(',', ''))
    return saleries


def get_teams(session):
    """
    Get the post season teams
    :param session:
    :return: DataFrame with teams
    """
    print('Getting Teams for Post Season 2020/2021')
    postseason_url = 'https://www.espn.com/nba/stats/team/_/view/team/season/2021/seasontype/3/table/offensive/' \
                     'sort/avgPoints/dir/desc'
    r = session.get(postseason_url)
    tab = r.html.xpath("//*[contains(@class,'Table Table--align-right Table--fixed Table--fixed-left')]")[0]
    post_teams = pd.DataFrame()
    post_teams['url'] = list(tab.links)
    post_teams['slug'] = post_teams['url'].str.split('/').str[5]
    post_teams['team'] = post_teams['url'].str.split('/').str[6].str.replace('-', ' ')
    return post_teams


def get_stats(session, teams):
    """
    Get statistics for players of post season
    :param session: DB connection
    :param teams: Teams DF
    :return: DataFrame
    """
    stats = pd.DataFrame()

    for p in teams.iterrows():
        slug = p[1]['slug']
        print('Getting stats for: ' + str(p[1]['team']))
        stats_url = 'https://www.espn.com/nba/team/stats/_/name/' + slug + '/season/2021/seasontype/3'
        r = session.get(stats_url)
        t_stats = pd.read_html(r.html.xpath("//*[contains(@class,'ResponsiveTable')]")[0].xpath("//table")[1].html)[0]
        t_stats['Name'] = \
            pd.read_html(r.html.xpath("//*[contains(@class,'ResponsiveTable')]")[0].xpath("//table")[0].html)[0]['Name']
        t_stats['Position'] = t_stats['Name'].str.replace("*", '').str.strip().str.split(" ").str[-1]
        t_stats['Name'] = t_stats['Name'].str.replace("*", '').str.strip().str.split(" ").str[:-1].str.join(' ')
        t_stats['Team'] = p[1]['team']
        t_stats = t_stats.drop(index=t_stats[t_stats['Position'] == 'Total'].index)
        stats = stats.append(t_stats)
    stats.reset_index(inplace=True)
    stats = stats.drop(columns='index')
    return stats


def print_comma_sep(df):
    """
    Print CSV string
    :param df: kpi DF
    :return:
    """
    from io import StringIO
    buf = StringIO()
    df.to_csv(buf, index=False)
    print(buf.getvalue())


def get_kpi(stats, saleries, printcsv):
    """
    Calculate and print KPI

    :param stats: Statistics DF
    :param saleries:  Saleries
    :param printcsv: Flag
    :return:
    """
    stats_salery = stats.join(saleries.set_index('Name'), on='Name', how='left', rsuffix='_s')
    mask = (stats_salery['GP'] > 0) & (stats_salery['PTS'] > 0) & -stats_salery['Salery'].isna()
    stats_salery['Price_per_Point'] = stats_salery['Salery'] / (stats_salery['GP'] * stats_salery['PTS'])
    kpi = stats_salery[mask].sort_values(by='Price_per_Point').head(10)[[
        'Name', 'Team', 'Position', 'GP', 'PTS', 'Salery', 'Price_per_Point']]
    print('\n\nTop 10 Players of 2020/2021 Post Season sorted by price per point (ASC)\n')
    if printcsv:
        print_comma_sep(kpi)
    else:
        print(kpi.to_string(index=False))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get Top 10 NBA Post Season 2020/21 Players by price per point. Data'
                                                 'saved to nba.db if file doesnt exits or --refresh option is used.')
    parser.add_argument('--refresh', dest='refresh', action='store_true',
                        help='Refresh nba.db if it already exits.')
    parser.add_argument('--print_csv', dest='print_csv', action='store_true',
                        help='Print comma separated data instead of command line friendly.')

    args = parser.parse_args()
    refresh = args.refresh
    print_csv = args.print_csv
    db_exits = check_if_db_exits()

    con = sqlite3.connect('nba.db')

    if not db_exits or refresh:
        print('Scrapping')
        ses = requests_html.HTMLSession()
        team = get_teams(ses)
        team.to_sql('teams', con=con, if_exists='replace', index=False)
        stat = get_stats(ses, team)
        stat.to_sql('stats', con=con, if_exists='replace', index=False)
        salery = get_saleries(ses)
        salery.to_sql('saleries', con=con, if_exists='replace', index=False)

    else:
        print('Reading from db nba.db')

        stat = pd.read_sql(sql='SELECT * FROM stats', con=con)
        salery = pd.read_sql(sql='SELECT * FROM saleries', con=con)

    get_kpi(stat, salery, print_csv)
