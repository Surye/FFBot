import praw
import time
import sqlite3
import urllib2
from BeautifulSoup import BeautifulSoup

def connect_to_db():
    """
    Connects to SQL DB
    """
    conn = sqlite3.connect('players.db')
    c = conn.cursor()
    return c,conn

def find_week_number():
    """
    Opens up Fantasy Pros and Gets the Current Week Number
    return Week Number
    """
    response = urllib2.urlopen('http://www.fantasypros.com/nfl/rankings/qb.php')
    page_source = response.read()

    week_num = 1
    while week_num <= 16:
        week_num += 1
        if 'Week %d' % week_num in page_source:
            break

    return week_num

def detect_ppr(comment):
    """
    Detect if the comment is a PPR League or not in the many different ways I've seen people say PPR or Non PPR
    return True for PPR, False for Standard
    """
    ppr = False
    if 'PPR' in comment.upper():
        ppr = True
    if 'NON PPR' in comment.upper():
        ppr = False
    if 'NONPPR' in comment.upper():
        ppr = False
    if 'NON-PPR' in comment.upper():
        ppr = False
    if 'NO PPR' in comment.upper():
        ppr = False
    if 'STANDARD' in comment.upper():
        ppr = False
    if 'NOT A PPR' in comment.upper():
        ppr = False
    return ppr

def valid_third_names(third_name):
    """
    Some players have three names. Detect if its a valid third name, or if its a fantasy pro team name due to a duplicate Player Name.
    """
    valid = ['III','BEY']
    if third_name in valid:
        return True
    else:
        return False

def get_players_in_db(position):
    """
    Get all the Player Names from the DB
    """
    c,conn = connect_to_db()
    players = []
    for row in c.execute("SELECT name,rank,opponent FROM %s" % position.lower()):
        player = {
                'name':row[0],
                'rank':row[1],
                'opponent':row[2]
                }
        players.append(player)
    conn.close()
    return players


def check_if_common(c,name):
    """
    Checks if a name is common
    """
    name_blacklist = ['DALLAS','BEAR','QUICK','LITTLE','MIKE','ACE','ED']
    if name in name_blacklist:
        return True

    num_of_names = 0
    for row in c.execute("SELECT name FROM %s WHERE name LIKE '%%%s%%'" % (position.lower(),name)):
        num_of_names += 1


    # If a nickname contains part of a players name. Example CJ Spiller and CJ2K
    nick_name = False
    for row in c.execute("SELECT name FROM nick_names WHERE nick_name LIKE '%%%s%%'" % name):
        nick_name = True
    if nick_name:
        return True

    if num_of_names > 1:
        return True
    else:
        return False

def check_if_common_combo(c,name):
    """
    Checks if a combination name is common
    """
    name = name.lower()
    name = name.replace(' ','-')

    num_of_names = 0
    for row in c.execute("SELECT * FROM %s WHERE name LIKE '%%%s%%'" % (position.lower(),name)):
        num_of_names += 1

    # If a nickname contains part of a players name. Example CJ Spiller and CJ2K
    nick_name = 0
    for row in c.execute("SELECT * FROM nick_names WHERE nick_name LIKE '%%%s%%'" % name):
        nick_name += 1
    if nick_name > 0:
        return True

    if num_of_names > 1:
        return True
    else:
        return False




def get_players(comment,position):
    """
    Parses users comments and gets the players they mention
    """
    c,conn = connect_to_db()
    players_in_comment = []

    for player_in_db in get_players_in_db(position):
        player = player_in_db['name'].replace('-',' ').upper()
        rank = player_in_db['rank']
        opponent = player_in_db['opponent']
        in_comment = False

        # SOME PLAYERS HAVE 3 NAMES, GET CORRECT LAST NAME
        player_names = player.split(' ')
        last_name = player_names[-1]
        first_name = player_names[0]
        if len(player_names) > 2:
            if not valid_third_names(last_name):
                last_name = player_names[-2]
                temp_player = ""
                for part_name in player_names[0:-1]:
                    temp_player += '%s ' % part_name
                player = temp_player

        # CREATE VARIABLES FOR EACH TYPE OF NAME WERE GOING TO CHECK FOR
        first_initial = player.split(' ')[0][0]
        first_initial_last_name = '%s %s' % (first_initial,last_name)
        first_initial_last_name_period = '%s. %s' % (first_initial,last_name)
        first_name_last_initial = '%s %s' % (first_name,last_name[0])

        # CHECK FOR NICK NAMES FIRST
        nick_names = []

        for row in c.execute("SELECT nick_name FROM nick_names WHERE name='%s'" % player.replace(' ','-').lower()):
            nick_names.append(row[0])
        if len(nick_names) > 0:
            for nick_name in nick_names:
                if nick_name in ['AD','AP']: # AD,AP ARE SPECIAL CASES WHICH CAN APPEAR IN MANY DIFFERNT WORDS. SPECIAL CHECKS APPLY
                    check_for = ' %s ' % nick_name.upper()
                else:
                    check_for = nick_name.upper()
                if check_for in comment.upper():
                    in_comment = True

        if not in_comment:
            # CHECK FULL NAME
            if player in comment.upper():
                in_comment = True

            # CHECK FIRST INITIAL LAST NAME
            elif first_initial_last_name in comment.upper():
                in_comment = True

            # CHECK FIRST INITIAL WITH PERIOD
            elif first_initial_last_name_period in comment.upper():
                in_comment = True

            # CHECK FIRST INITIAL WITH PERIOD NO SPACE
            elif first_initial_last_name_period.replace(' ','') in comment.upper():
                in_comment = True

            # CHECK LAST NAME
            elif last_name in comment.upper() and not check_if_common(c,last_name):
                in_comment = True

            # CHECK FIRST NAME
            elif first_name in comment.upper() and not check_if_common(c,first_name):
                in_comment = True

            # CHECK FIRST NAME LAST INITIAL
            elif first_name_last_initial in comment.upper() and not check_if_common_combo(c,first_name_last_initial):
                in_comment = True

        if in_comment:
            if player not in players_in_comment:
                players_in_comment.append(player_in_db)
    conn.close()
    return players_in_comment

def format_player_name(name):
    """
    Formats a players name
    """
    name = name.replace('-',' ')
    name = name.upper()
    return name

def get_four_for_four_news_link(player):
    print 'yes'
    player = player.replace('-','%20')
    link = 'http://www.4for4.com/players/player_search.php?player_search=%s' % player
    response = urllib2.urlopen(link)
    page_source = response.read()

    found_player = False
    soup = BeautifulSoup(page_source)
    for a in soup.findAll('a'):
        if 'profile.php?PID=' in a['href']:
            found_player = True
            four_for_for_player = a['href']
            break

    if found_player:
        four_for_for_player = 'http://www.4for4.com%s' % four_for_for_player
        return four_for_for_player
    else:
        return False



def compare_two_players(players,ppr,position,week_num):
    """
    Compares two players using fantasy pros comparision tool
    """
    link = 'http://www.fantasypros.com/nfl/start/%s-%s.php' % (players[0]['name'],players[1]['name'])
    if ppr:
        if 'QB' not in position.upper():
            link +='?scoring=PPR'
    print link
    response = urllib2.urlopen(link)
    ffpro_page_source = response.read()

    player_a_news = get_four_for_four_news_link(players[0]['name'])
    player_b_news = get_four_for_four_news_link(players[1]['name'])

    percentages = []
    soup = BeautifulSoup(ffpro_page_source)
    for span in soup.findAll('span'):
        if '%' in span.text:
            percentages.append(span.text)
    if ppr:
        ppr_comment = 'In a PPR League:'
    else:
        ppr_comment = 'In a Standard League:'

    player_a_perc = int(percentages[0].rstrip('%%'))
    player_a_name = format_player_name(players[0]['name'])
    player_a_oppenent = players[0]['opponent']
    player_b_perc = int(percentages[1].rstrip('%%'))
    player_b_name = format_player_name(players[1]['name'])
    player_b_oppenent = players[1]['opponent']

    draw = False
    higher_ranked_news = False
    lower_ranked_news = False
    if player_a_perc > player_b_perc:
        higher_ranked_player = player_a_name
        higher_ranked_opponent = player_a_oppenent
        lower_ranked_player = player_b_name
        lower_ranked_opponent = player_b_oppenent
        if player_a_news:
            higher_ranked_player = '[%s](%s)' % (higher_ranked_player,player_a_news)
        if player_b_news:
            lower_ranked_player =  '[%s](%s)' % (lower_ranked_player,player_b_news)

    elif player_b_perc > player_a_perc:
        higher_ranked_player = player_b_name
        higher_ranked_opponent = player_b_oppenent
        lower_ranked_player = player_a_name
        lower_ranked_opponent = player_a_oppenent
        if player_b_news:
            higher_ranked_player = '[%s](%s)' % (higher_ranked_player,player_b_news)
        if player_a_news:
            lower_ranked_player =  '[%s](%s)' % (lower_ranked_player,player_a_news)
    else:
        draw = True

    if not draw:
        comment = '%s\n\n' \
              '**Experts say to start %s against %s** and to sit %s against %s.\n\n' % (ppr_comment,higher_ranked_player,higher_ranked_opponent,lower_ranked_player,lower_ranked_opponent)
    else:
        comment = '%s\n\n its a toss up. Hopefully another user can come in and help you out' \

    return comment,link

def compare_more_than_2_players(players,position,ppr,week_num):
    """
    Compares more than 3 users using fantasy pros rankings
    """
    if ppr:
        position = 'ppr-%s' % position
    c,conn = connect_to_db()
    players_and_ranks = []

    for player in players:
        player_news = get_four_for_four_news_link(player['name'])
        db = position.replace('-','_')
        for row in c.execute("SELECT rank FROM %s where name='%s'" % (db.lower(),player['name'])):
            player_rank = row[0]
            if player_news:
                players_and_ranks.append('%s. [%s](%s) against **%s**' % (player_rank,format_player_name(player['name']),player_news,player['opponent']))
            else:
                players_and_ranks.append('%s. %s against **%s**' % (player_rank,format_player_name(player['name']),player['opponent']))
    conn.close()
    players_and_ranks.sort

    if ppr:
        ppr_comment = 'in a PPR League'
    else:
        ppr_comment = 'in a Standard League'

    link = 'http://www.fantasypros.com/nfl/rankings/%s.php' %  position.lower()
    comment = 'Experts have the players that you mentioned ranked in the following order %s:\n\n' % ppr_comment
    for player_and_rank in players_and_ranks:
        comment += '%s\n\n' % player_and_rank
    return comment,link

def get_wdis_threads(ff_subreddit):
    """
    Gets recent threads from /r/fantasyfootball. Then parses name to make sure its the right threads and gets the positions
    from the threads. Right now im not doing anything with defenses as there are so many different formats of team names
    that I didnt feel like dealing with right now.

    return threads and postions
    """
    # GET ALL WDIS THREADS AND THE POSITIO
    wdis_posts = []
    # Get the last hot 35 threads. Seems to be the magic number to get the right WDIS threads
    for submission in ff_sub_reddit.get_hot(limit=35):
        kicker_te = False
        if 'WDIS' in submission.title and 'OFFICIAL' in submission.title:
            if 'WR' in submission.title:
                position = 'WR'
            elif 'RB' in submission.title:
                position = 'RB'
            elif 'QB' in submission.title:
                position = 'QB'
            elif 'FLEX' in submission.title:
                position = 'FLEX'
            elif 'TE/DEF/K' in submission.title:
                kicker_te = True
            else:
                position = 'UNKNOWN'

            if kicker_te:

                wdis_posts.append((submission,'TE'))
                wdis_posts.append((submission,'K'))
            else:
                wdis_posts.append((submission,position))

    return wdis_posts


# Sign into Reddit and get the subreddit info
r = praw.Reddit('Fantasy Football Bot by TonyG623')
r.login(username="username",password='password')
ff_sub_reddit = r.get_subreddit('ffbottest')
wdis_posts = get_wdis_threads(ff_sub_reddit)
print wdis_posts

# Get the week number straight from Fantasy Pros
week_num = find_week_number()
# Next weeks week number
next_week = week_num + 1

def create_footer(fantasy_pros_link):
    # The Footer that gets added to Every post
    comment_footer = '\nRankings currently based off of **Week %d**.' \
                     '\n\n\n\nPlayer Rankings provided by **[FantasyPros](%s)**' \
                     '\n\nPlayer News Provided by **[4for4](http://4for4.com)**'  % (week_num,fantasy_pros_link)
    return comment_footer

for thread in wdis_posts:
    # Get the submission
    submission = thread[0]
    # Get the position from the thread name
    position = thread[1]
    for comment in submission.comments:
        try:
            # If there are no replies, and the next Week Number isnt in the the comment. (Problem with Mondays
            # Where people are asking both week 4 and week 5 questions)
            if len(comment._replies) == 0 and 'Week %d' % next_week not in comment.body:
                # Calculate the Time since comment. Not sure why this doesn't equal the actual time. Didnt look to deep into it.
                time_since_comment = int(time.time()) - int(comment.created)
                # -27000 seems to be the magic number of a half hour.
                if time_since_comment > -30000:
                    # Parse the comment to see if its a PPR league or not
                    ppr = detect_ppr(comment.body)
                    # Parse the comment to get players
                    players = get_players(comment.body,position)

                    # Print the comment, players it finds for debugging purposes
                    print '\n\n\n\n'
                    print comment.body
                    print players

                    # If it finds two players, do a comparison.
                    if len(players) == 2:
                        wdis_comment,link = compare_two_players(players,ppr,position,week_num)
                        wdis_comment += create_footer(link)
                        # Print the WDIS comment for debugging
                        print wdis_comment
                        comment.upvote()
                        comment.reply(wdis_comment)

                    # if it finds more than two players do a rankings comparision.
                    elif len(players) > 2:
                        wdis_comment,link = compare_more_than_2_players(players,position,ppr,week_num)
                        wdis_comment += create_footer(link)
                        # Print the WDIS comment for debugging
                        print wdis_comment
                        comment.upvote()
                        comment.reply(wdis_comment)
        except:
            # Catch random exceptions that the reddit library doesnt like. I know this is bad and I shouldnt do this way
            # but it works for now.
            raise
