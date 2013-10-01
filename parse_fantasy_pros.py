import urllib2
import BeautifulSoup
import sqlite3

import sqlite3
# CONNECT TO THE DB, CREATES IT IF IT NEEDS TO
conn = sqlite3.connect('players.db')
c = conn.cursor()

# BELOW ARE THE POSTION NAMES OF EACH PAGE ON FANTASYPROS
positions = ['qb','rb','te','flex','wr','ppr_rb','ppr_te','ppr_flex','ppr_wr']

for position in positions:
    # TRY AND CREATE TABLE IF WE NEED TO
    try:
        c.execute('''CREATE TABLE %s (name,rank,opponent)''' % position)
        conn.commit()
    except:
        pass

    # REQUEST EACH PAGE
    request = urllib2.Request("http://www.fantasypros.com/nfl/rankings/%s.php" % position.replace('_','-'))
    response = urllib2.urlopen(request)
    source = BeautifulSoup.BeautifulSoup(response)

    # DELETE PREVIOUS PLAYERS AND GET NEW INFO
    c.execute("DELETE FROM %s" % position)

    rank = 0
    for tds in source.findAll('td'):
        if '<a href="/nfl/players/' in str(tds):
            opponent = False
            player_name = False
            link = False
            for td in tds:
                table_row = BeautifulSoup.BeautifulSoup(str(td))
                matchup = table_row.find('small')
                player = table_row.find('a')
                if matchup and ('at' in matchup.text or 'vs' in matchup.text):
                    opponent = matchup.text.split(' ')[-1]
                if player:
                    if '/nfl/players' in player['href']:
                        link = player['href'].split('/nfl/players/')[-1].split('.')[0]

            # Throw out the links to P,Q,D,O
            if len(link) > 1:
                rank += 1
                print rank,position,opponent,link
                c.execute("INSERT INTO %s VALUES ('%s','%s','%s')" % (position,link,rank,opponent))
                conn.commit()



# TRYS TO CREATE THE NICKNAME TABLE IF ITS NOT CREATED
try:
    c.execute('''CREATE TABLE nick_names (name,nick_name)''')
except:
    pass

# Right now I just delete everything and reput it in. Not ideal but Im lazy.
c.execute("DELETE FROM nick_names")

# List of touples with name as it is in the DB and the nick name
nick_names = [
    ('robert-griffin-iii','RG3'),
    ('matt-ryan', 'MATTY ICE'),
    ('ben-roethlisberger','BIG BEN'),
    ('marshawn-lynch','BEAST MODE'),
    ('adrian-peterson-min','AD'),
    ('adrian-peterson-min','ALL DAY'),
    ('adrian-peterson-min','AP'),
    ('darren-mcfadden','DMC'),
    ('maurice-jones-drew','MJD'),
    ('steve-johnson','STEVIE JOHNSON'),
    ('rob-gronkowski','GRONK'),
    ('larry-fitzgerald','FITZ'),
    ('chris-johnson','CJ2K'),
    ('chris-johnson','CJ0K'),
    ('vincent-jackson','VJAX'),
    ('vincent-jackson','V. JAX'),
    ('vincent-jackson','V JAX'),
    ('ryan-mathews','RYAN MATTHEWS'),
    ('benjarvus-green-ellis','BGE'),
    ('benjarvus-green-ellis','BJGE'),
    ('benjarvus-green-ellis','GREEN ELLIS'),
    ('benjarvus-green-ellis','BENJARVIS'),
    ('benjarvus-green-ellis','LAW FIRM'),
    ('jacquizz-rodgers','J-ROD'),
    ('kendall-wright','KENDELL WRIGHT'),
    ('giovani-bernard','GIO'),
    ('matthew-stafford','MATT STAFFORD'),
    ('leveon-bell','VEON BELL')
    ]

# insert the nick names in to the DB
for nick_name in nick_names:
    c.execute("INSERT INTO nick_names VALUES ('%s','%s')" % (nick_name[0],nick_name[1]))
    conn.commit()

# Close the DB
conn.close()


