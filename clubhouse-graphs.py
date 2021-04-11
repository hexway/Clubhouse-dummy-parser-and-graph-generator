"""
POC for clubhouse parser based
"""

import os
import sys
import time
import logging
import sqlite3
import argparse
import configparser
from pyvis.network import Network
from prettytable import PrettyTable
from clubhouse.clubhouse import Clubhouse

# Set some global variables

sqlite_file = 'club_db.sqlite'

try:
    import agorartc
    RTC = agorartc.createRtcEngineBridge()
    eventHandler = agorartc.RtcEngineEventHandlerBase()
    RTC.initEventHandler(eventHandler)
    # 0xFFFFFFFE will exclude Chinese servers from Agora's servers.
    RTC.initialize(Clubhouse.AGORA_KEY, None, agorartc.AREA_CODE_GLOB & 0xFFFFFFFE)
    # Enhance voice quality
    if RTC.setAudioProfile(
            agorartc.AUDIO_PROFILE_MUSIC_HIGH_QUALITY_STEREO,
            agorartc.AUDIO_SCENARIO_GAME_STREAMING
        ) < 0:
        print("[-] Failed to set the high quality audio profile")
except ImportError:
    RTC = None

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-u', '--user_name', help='Get info by username')
parser.add_argument('-i', '--user_id', help='Get info by user id')
parser.add_argument('--followers', action='store_true', help='Get user followers')
parser.add_argument('--following',action='store_true', help='Get info about following users')
parser.add_argument('-I', '--invite', help='Invited by graph')
parser.add_argument('--followed_by', help='Get followers graph by username')
parser.add_argument('--invited_by', help='Invitation graph for username')
parser.add_argument('--inv_all', action='store_true', help='Show invitation graph for all users in local db')
parser.add_argument('--group', help='Get users from group by group id')
parser.add_argument('--find_by_bio', help='Find users with pattern in their bio')
parser.add_argument('-v', '--debug', action='store_true', help='Show debug info')
args = parser.parse_args()


def init_logger(logname, level):
    # generic log conf
    logger = logging.getLogger(logname)
    logger.setLevel(level)
    console_format = logging.Formatter("[%(levelname)-5s] %(message)s")
    # console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(console_format)
    logger.addHandler(ch)
    return logger

if args.debug:
    logger = init_logger("ch-bot", logging.DEBUG)
else:
    logger = init_logger("ch-bot", logging.INFO)


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        logger.info(e)
    return None

def create_db():
    logger.info("Creating new DB")
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.execute("CREATE TABLE {} ("
              "{} {} PRIMARY KEY,"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"              
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"              
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"
              "{} {},"                     
              ")".format("users",
                         "user_id", "INTEGER",
                         "name", "TEXT",
                         "displayname", "TEXT",
                         "photo_url", "TEXT",
                         "username", "TEXT",
                         "bio", "TEXT",
                         "twitter", "TEXT",
                         "instagram", "TEXT",
                         "num_followers", "INTEGER",
                         "num_following", "INTEGER",
                         "time_created", "TEXT",
                         "follows_me", "TEXT",
                         "is_blocked_by_network", "TEXT",
                         "invited_by", "INTEGER",
                         "invited_by_name", "TEXT",
                         "clubs", "TEXT",
                         "followers", "TEXT",
                         "following","TEXT"))
    conn.commit()
    conn.close()

if not os.path.isfile(sqlite_file):
    create_db()

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_user_from_db_by_id(user_id):
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return 0
    else:
        return row

def get_users_from_db_invided_by(user_id):
    logger.debug(f"[DBG] Looking for users invited by {user_id} in local DB...")
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("select * from users where invited_by == ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    if rows is None:
        return 0
    else:
        return rows

def get_user_from_db_by_username(username):
    logger.debug(f"[DBG] Looking for {username} in local DB...")
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return 0
    else:
        return row

def log_user_data_short(user_data_short):
    local_target_user = get_user_from_db_by_id(user_data_short['user_id'])
    if local_target_user:
        logger.debug(f"[DBG] Alredy have userid {user_data_short['user_id']} in local DB")
    else:
        conn = create_connection(sqlite_file)
        try:
            logger.debug(f"[DBG] Saving short info in DB username: {user_data_short['username']}")
            c = conn.cursor()
            user_rec = "INSERT INTO users (user_id,name,displayname,photo_url,username,bio,twitter,instagram,num_followers,num_following,time_created,follows_me,is_blocked_by_network) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
            c.execute(user_rec, (user_data_short["user_id"],
                                user_data_short["name"] if "name" in user_data_short  and user_data_short["name"] is not None else "",
                                user_data_short["displayname"] if "displayname" in user_data_short  and user_data_short["displayname"] is not None else "",
                                user_data_short["photo_url"] if "photo_url" in user_data_short  and user_data_short["photo_url"] is not None else "",
                                user_data_short["username"] if "username" in user_data_short  and user_data_short["username"] is not None else "",
                                user_data_short["bio"] if "bio" in user_data_short  and user_data_short["bio"] is not None else "",
                                user_data_short["twitter"] if "twitter" in user_data_short  and user_data_short["twitter"] is not None else "",
                                user_data_short["instagram"] if "instagram" in user_data_short  and user_data_short["instagram"] is not None else "",
                                user_data_short["num_followers"] if "num_followers" in user_data_short  and user_data_short["num_followers"] is not None else 0,
                                user_data_short["num_following"] if "num_following" in user_data_short  and user_data_short["num_following"] is not None else 0,
                                user_data_short["time_created"] if "time_created" in user_data_short  and user_data_short["time_created"] is not None else "",
                                user_data_short["follows_me"] if "follows_me" in user_data_short  and user_data_short["follows_me"] is not None else "",
                                user_data_short["is_blocked_by_network"] if "is_blocked_by_network" in user_data_short  and user_data_short["is_blocked_by_network"] is not None else "",
                                 ))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            print(f"Uh oh, an error occurred ...{e}")
            raise RuntimeError(f"Uh oh, an error occurred ...{e}")

def log_user_data(user_data):
    local_target_user = get_user_from_db_by_id(user_data['user_profile']['user_id'])
    if local_target_user and is_full_info(user_id=user_data['user_profile']['user_id']):
        print(f"Alredy have userid {user_data['user_profile']['user_id']} in local DB")
    elif local_target_user and not is_full_info(user_id=user_data['user_profile']['user_id']):
        conn = create_connection(sqlite_file)
        try:
            logger.debug(f'[DBG] Update info for user {user_data["user_profile"]["username"]}')
            c = conn.cursor()
            user_rec = "UPDATE users SET name=?, displayname=?,photo_url=?,username=?,bio=?,twitter=?,instagram=?,num_followers=?,num_following=?,time_created=?,follows_me=?,is_blocked_by_network=?,invited_by=?,invited_by_name=?,clubs=? WHERE user_id=?"
            c.execute(user_rec, (
                                user_data["user_profile"]["name"] if user_data["user_profile"]["name"] is not None else "",
                                user_data["user_profile"]["displayname"] if user_data["user_profile"]["displayname"] is not None else "",
                                user_data["user_profile"]["photo_url"] if user_data["user_profile"]["photo_url"] is not None else "",
                                user_data["user_profile"]["username"] if user_data["user_profile"]["username"] is not None else "",
                                user_data["user_profile"]["bio"] if user_data["user_profile"]["bio"] is not None else "",
                                user_data["user_profile"]["twitter"] if user_data["user_profile"]["twitter"] is not None else "",
                                user_data["user_profile"]["instagram"] if user_data["user_profile"]["instagram"] is not None else "",
                                user_data["user_profile"]["num_followers"] if user_data["user_profile"]["num_followers"] is not None else 0,
                                user_data["user_profile"]["num_following"] if user_data["user_profile"]["num_following"] is not None else 0,
                                user_data["user_profile"]["time_created"] if user_data["user_profile"]["time_created"] is not None else "",
                                user_data["user_profile"]["follows_me"] if user_data["user_profile"]["follows_me"] is not None else "",
                                user_data["user_profile"]["is_blocked_by_network"] if user_data["user_profile"]["is_blocked_by_network"] is not None else "",
                                user_data["user_profile"]["invited_by_user_profile"]["user_id"] if user_data["user_profile"]["invited_by_user_profile"] is not None else 1,
                                user_data["user_profile"]["invited_by_user_profile"]["name"] if user_data["user_profile"]["invited_by_user_profile"] is not None else "",
                                str(user_data["user_profile"]["clubs"]),
                                user_data["user_profile"]["user_id"],
            ))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            print(f"Uh oh, an error occurred ...{e}")
            raise RuntimeError(f"Uh oh, an error occurred ...{e}")
    else:
        conn = create_connection(sqlite_file)
        try:
            logger.debug(f"[DBG] Saving in DB userID: {user_data['user_profile']['username']}")
            c = conn.cursor()
            user_rec = "INSERT INTO users (user_id,name,displayname,photo_url,username,bio,twitter,instagram,num_followers,num_following,time_created,follows_me,is_blocked_by_network,invited_by,invited_by_name,clubs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            c.execute(user_rec, (user_data["user_profile"]["user_id"],
                                 user_data["user_profile"]["name"] if user_data["user_profile"][
                                                                          "name"] is not None else "",
                                 user_data["user_profile"]["displayname"] if user_data["user_profile"][
                                                                                 "displayname"] is not None else "",
                                 user_data["user_profile"]["photo_url"] if user_data["user_profile"][
                                                                               "photo_url"] is not None else "",
                                 user_data["user_profile"]["username"] if user_data["user_profile"][
                                                                              "username"] is not None else "",
                                 user_data["user_profile"]["bio"] if user_data["user_profile"][
                                                                         "bio"] is not None else "",
                                 user_data["user_profile"]["twitter"] if user_data["user_profile"][
                                                                             "twitter"] is not None else "",
                                 user_data["user_profile"]["instagram"] if user_data["user_profile"][
                                                                               "instagram"] is not None else "",
                                 user_data["user_profile"]["num_followers"] if user_data["user_profile"][
                                                                                   "num_followers"] is not None else 0,
                                 user_data["user_profile"]["num_following"] if user_data["user_profile"][
                                                                                   "num_following"] is not None else 0,
                                 user_data["user_profile"]["time_created"] if user_data["user_profile"][
                                                                                  "time_created"] is not None else "",
                                 user_data["user_profile"]["follows_me"] if user_data["user_profile"][
                                                                                "follows_me"] is not None else "",
                                 user_data["user_profile"]["is_blocked_by_network"] if user_data["user_profile"][
                                                                                           "is_blocked_by_network"] is not None else "",
                                 user_data["user_profile"]["invited_by_user_profile"]["user_id"] if
                                 user_data["user_profile"]["invited_by_user_profile"] is not None else 0,
                                 user_data["user_profile"]["invited_by_user_profile"]["name"] if
                                 user_data["user_profile"]["invited_by_user_profile"] is not None else 0,
                                 str(user_data["user_profile"]["clubs"]),))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            print(f"Uh oh, an error occurred ...{e}")
            raise RuntimeError(f"Uh oh, an error occurred ...{e}")

def get_user_info_by_id(client, user_id):
    x = PrettyTable()
    x.field_names = ["user_id", "name", "displayname", "photo_url", "username", "bio", "twitter", "instagram",
                     "followers", "following", "invited by", "invited by name"]
    user = get_user_from_db_by_id(user_id)
    if user and is_full_info(user_id=user_id):
        logger.debug(f"[DBG] Found user {user_id} in local DB...")
    else:
        logger.info(f"We have no user {user_id} in our DB. Let's have a call to CH API...")
        time.sleep(3)
        target_user = client.get_profile(user_id)
        if target_user["success"]:
            user = {"user_id":target_user["user_profile"]["user_id"],
                    "name":target_user["user_profile"]["name"] if target_user["user_profile"]["name"] is not None else "",
                    "displayname":target_user["user_profile"]["displayname"] if target_user["user_profile"]["displayname"] is not None else "",
                    "photo_url":target_user["user_profile"]["photo_url"] if target_user["user_profile"]["photo_url"] is not None else "",
                    "username":target_user["user_profile"]["username"] if target_user["user_profile"]["username"] is not None else "",
                    "bio":target_user["user_profile"]["bio"] if target_user["user_profile"]["bio"] is not None else "",
                    "twitter":target_user["user_profile"]["twitter"] if target_user["user_profile"]["twitter"] is not None else "",
                    "instagram":target_user["user_profile"]["instagram"] if target_user["user_profile"]["instagram"] is not None else "",
                    "num_followers":target_user["user_profile"]["num_followers"] if target_user["user_profile"]["num_followers"] is not None else 0,
                    "num_following":target_user["user_profile"]["num_following"] if target_user["user_profile"]["num_following"] is not None else 0,
                    "invited_by":target_user["user_profile"]["invited_by_user_profile"]["user_id"] if target_user["user_profile"]["invited_by_user_profile"] is not None else 1,
                    "invited_by_name": target_user["user_profile"]["invited_by_user_profile"]["name"] if target_user["user_profile"]["invited_by_user_profile"] is not None else ""
                    }
            log_user_data(target_user)
            time.sleep(3)
            followers = get_followers(client, user['user_id'])
            time.sleep(3)
            following = get_following(client, user['user_id'])
        # if args.graph:
        #     get_users_from_db_invided_by()
    x.add_row([user["user_id"],
               user["name"],
               user["displayname"],
               user["photo_url"],
               user["username"],
               user["bio"],
               user["twitter"],
               user["instagram"],
               user["num_followers"],
               user["num_following"],
               user["invited_by"],
               user["invited_by_name"]])
    return x,user

def get_user_info_by_username(client, username):
    x = PrettyTable()
    x.field_names = ["user_id", "name", "displayname", "photo_url", "username", "bio", "twitter", "instagram",
                     "followers", "following", "invited by", "invited by name"]
    user = get_user_from_db_by_username(username)
    if user and is_full_info(username=username):
        logger.debug(f"[DBG] Found user {username} in local DB...")
    else:
        target_user_id  = 0
        logger.debug(f"[DBG]Let's have a call to CH API...")
        time.sleep(3)
        user_lists = client.search_users(username)
        for user in user_lists['users']:
            log_user_data_short(user)
            if user['username'] == username:
                target_user_id = user['user_id']
        target_user = client.get_profile(target_user_id)
        user = {"user_id":target_user["user_profile"]["user_id"],
                "name":target_user["user_profile"]["name"],
                "displayname":target_user["user_profile"]["displayname"],
                "photo_url":target_user["user_profile"]["photo_url"],
                "username":target_user["user_profile"]["username"],
                "bio":target_user["user_profile"]["bio"],
                "twitter":target_user["user_profile"]["twitter"],
                "instagram":target_user["user_profile"]["instagram"],
                "num_followers":target_user["user_profile"]["num_followers"],
                "num_following":target_user["user_profile"]["num_following"],
                "invited_by":target_user["user_profile"]["invited_by_user_profile"]["user_id"] if target_user["user_profile"]["invited_by_user_profile"] is not None else 1,
                "invited_by_name": target_user["user_profile"]["invited_by_user_profile"]["name"] if target_user["user_profile"]["invited_by_user_profile"] is not None else ""
                }
        log_user_data(target_user)
        time.sleep(3)
        get_followers(client, user['user_id'])
        time.sleep(3)
        get_following(client, user['user_id'])
    x.add_row([user["user_id"],
               user["name"],
               user["displayname"],
               user["photo_url"],
               user["username"],
               user["bio"],
               user["twitter"],
               user["instagram"],
               user["num_followers"],
               user["num_following"],
               user["invited_by"],
               user["invited_by_name"]])
    return x,user

def collect_invite_chain(client, net, user_id):
    x, user_data = get_user_info_by_id(client, user_id)
    if user_data["invited_by"] == 1:
        net.show('ch-nodes.html')
        return 1
    else:
        net.add_node(user_data['user_id'], label=user_data['name'], title=f"username:{str(user_data['username'])}<br>"
                                                                        f"twitter:{user_data['twitter']}<br>"
                                                                        f"bio:{user_data['bio']}<br>"
                                                                        f"<img src=\"{user_data['photo_url']}\" width=\"100\" height=\"100\">")
        invited_by_user_data = get_user_from_db_by_id(user_data['invited_by'])
        net.add_node(invited_by_user_data['user_id'], label=invited_by_user_data['name'], title=f"username:{str(invited_by_user_data['username'])}<br>"
                                                                          f"twitter:{invited_by_user_data['twitter']}<br>"
                                                                          f"bio:{invited_by_user_data['bio']}<br>"
                                                                          f"<img src=\"{invited_by_user_data['photo_url']}\" width=\"100\" height=\"100\">")
        net.add_edge(user_data['user_id'], user_data['invited_by'], arrows="from")

        print(f"{user_data['name']}<--{user_data['invited_by_name']}")
        # time.sleep(3)
        return collect_invite_chain(client, net, user_data['invited_by'])

def get_invite_graph(client, net, username):
    logger.info(f"Getting invite graph for user {username}")
    x, user_data = get_user_info_by_username(client, username)
    collect_invite_chain(client, net, user_data["user_id"])

def write_config(user_id, user_token, user_device, filename='setting.ini'):
    """ (str, str, str, str) -> bool

    Write Config. return True on successful file write
    """
    config = configparser.ConfigParser()
    config["Account"] = {
        "user_device": user_device,
        "user_id": user_id,
        "user_token": user_token,
    }
    with open(filename, 'w') as config_file:
        config.write(config_file)
    return True

def read_config(filename='setting.ini'):
    """ (str) -> dict of str

    Read Config
    """
    config = configparser.ConfigParser()
    config.read(filename)
    if "Account" in config:
        return dict(config['Account'])
    return dict()

def process_onboarding(client):
    """ (Clubhouse) -> NoneType

    This is to process the initial setup for the first time user.
    """
    print("=" * 30)
    print("Welcome to Clubhouse!\n")
    print("The registration is not yet complete.")
    print("Finish the process by entering your legal name and your username.")
    print("WARNING: THIS FEATURE IS PURELY EXPERIMENTAL.")
    print("         YOU CAN GET BANNED FOR REGISTERING FROM THE CLI ACCOUNT.")
    print("=" * 30)

    while True:
        user_realname = input("[.] Enter your legal name (John Smith): ")
        user_username = input("[.] Enter your username (elonmusk1234): ")

        user_realname_split = user_realname.split(" ")

        if len(user_realname_split) != 2:
            print("[-] Please enter your legal name properly.")
            continue

        if not (user_realname_split[0].isalpha() and
                user_realname_split[1].isalpha()):
            print("[-] Your legal name is supposed to be written in alphabets only.")
            continue

        if len(user_username) > 16:
            print("[-] Your username exceeds above 16 characters.")
            continue

        if not user_username.isalnum():
            print("[-] Your username is supposed to be in alphanumerics only.")
            continue

        client.update_name(user_realname)
        result = client.update_username(user_username)
        if not result['success']:
            print(f"[-] You failed to update your username. ({result})")
            continue

        result = client.check_waitlist_status()
        if not result['success']:
            print("[-] Your registration failed.")
            print(f"    It's better to sign up from a real device. ({result})")
            continue

        print("[-] Registration Complete!")
        print("    Try registering by real device if this process pops again.")
        break

def is_full_info(user_id="", username=""):
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    if user_id:
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    elif username:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
    else:
        return False
    row = c.fetchone()
    conn.close()
    if row is None:
        logger.debug("[DBG] There is no such user in db")
        return False
    elif not row["invited_by"]:
        # logger.debug("[DBG] We have no full info about user in DB")
        return False
    else:
        logger.debug("[DBG] Found full info in db")
        return True

def log_followers(follower_ids, user_id):
    conn = create_connection(sqlite_file)
    try:
        c = conn.cursor()
        user_rec = "UPDATE users SET followers=? WHERE user_id=?"
        c.execute(user_rec, (",".join([str(id) for id in follower_ids]),user_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"Uh oh, an error occurred ...{e}")
        raise RuntimeError(f"Uh oh, an error occurred ...{e}")

def log_following(following_ids, user_id):
    conn = create_connection(sqlite_file)
    try:
        c = conn.cursor()
        user_rec = "UPDATE users SET following=? WHERE user_id=?"
        c.execute(user_rec, (",".join([str(id) for id in following_ids]),user_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        print(f"Uh oh, an error occurred ...{e}")
        raise RuntimeError(f"Uh oh, an error occurred ...{e}")

def get_followers(client, user_id=0, username=""):
    f_ids=[]
    followers=[]
    if user_id:
        logger.info(f"Collecting followers for user {user_id}")
        user = get_user_from_db_by_id(user_id)
        if user["followers"]:
            return list(map(int, user["followers"].split(',')))
        else:
            followers = client.get_followers(user_id, page_size=5000)
    if username:
        user = get_user_from_db_by_username(username)
        if user["followers"]:
            return list(map(int, user["following"].split(',')))
        else:
            followers = client.get_followers(user["user_id"], page_size=5000)
    if followers["success"]:
        for follower in followers["users"]:
            f_ids.append(follower["user_id"])
            log_user_data_short(follower)
        log_followers(f_ids, user_id)
        return f_ids
    else:
        logger.info("Something wrong with get_followers()")
        exit(1)

def search_in_bio(search_str):
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("SELECT * FROM users WHERE bio LIKE ?", (f"%{search_str}%",))
    rows = c.fetchall()
    conn.close()
    if rows is None:
        return 0
    else:
        return rows

def get_following(client, user_id=0, username=""):
    f_ids=[]
    following = []
    if user_id:
        logger.info(f"Collecting following users for user {user_id}")
        user = get_user_from_db_by_id(user_id)
        if user["following"]:
            return list(map(int, user["following"].split(',')))
        else:
            following = client.get_following(user_id, page_size=5000)
    if username:
        user = get_user_from_db_by_username(username)
        if user["following"]:
            return list(map(int, user["following"].split(',')))
        else:
            following = client.get_following(user["user_id"], page_size=5000)
    if following["success"]:
        for follower in following["users"]:
            f_ids.append(follower["user_id"])
            log_user_data_short(follower)
        log_following(f_ids, user_id)
        return f_ids
    else:
        logger.info("Something wrong with get_followers()")
        exit(1)

def check_edge(net,f_id,t_id):
    edges = net.get_edges()
    for edge in edges:
        if edge['from'] == f_id and edge['to']==t_id:
            return True
    return False

def followed_by_graph(client,net,user_id):
    user = get_user_from_db_by_id(user_id)
    if user and is_full_info(user_id=user_id):
        logger.info(f"Start generation of followed_by for user {user['username']}")
        net.add_node(user_id, label=user["name"], title=f"username:{str(user['username'])}<br>"
                                                        f"twitter:{user['twitter']}<br>"
                                                        f"bio:{user['bio']}<br>"
                                                        f"<img src=\"{user['photo_url']}\" width=\"100\" height=\"100\">")

        if len(user["followers"])>0:
            followers_list = list(map(int, user["followers"].split(',')))
            for follower_id in followers_list:
                f_user = get_user_from_db_by_id(follower_id)
                if f_user:
                    net.add_node(f_user['user_id'], label=f_user['name'], title=f"username:{str(f_user['username'])}<br>"
                                                                                    f"twitter:{f_user['twitter']}<br>"
                                                                                    f"bio:{f_user['bio']}<br>"
                                                                                    f"<img src=\"{f_user['photo_url']}\" width=\"100\" height=\"100\">")
                    net.add_edge(f_user['user_id'], user_id, arrows="from")
                    # if check_edge(net, user_id, f_user['user_id']):
                    #     continue
                    # else:
                    #     followed_by_graph(client, net, f_user['user_id'])
                else:
                    return
        else:
            return
    else:
        return

def invited_by_graph(client,net,user_id):
    user = get_user_from_db_by_id(user_id)
    logger.info(f"Start generation of invited_by for user {user['username']}")
    net.add_node(user_id, label=user["name"], title=f"username:{str(user['username'])}<br>"
                                                    f"twitter:{user['twitter']}<br>"
                                                    f"bio:{user['bio']}<br>"
                                                    f"<img src=\"{user['photo_url']}\" width=\"100\" height=\"100\">")
    invited_users = get_users_from_db_invided_by(user_id)
    if len(invited_users)>0:
        for inv_user in invited_users:
            net.add_node(inv_user['user_id'], label=inv_user['name'], title=f"username:{str(inv_user['username'])}<br>"
                                                                            f"twitter:{inv_user['twitter']}<br>"
                                                                            f"bio:{inv_user['bio']}<br>"
                                                                            f"<img src=\"{inv_user['photo_url']}\" width=\"100\" height=\"100\">")
            net.add_edge(inv_user['user_id'], inv_user['invited_by'], arrows="from")
            invited_by_graph(client, net, inv_user['user_id'])
    else:
        return

net = Network(height='100%', width='100%')

def get_user_by_follower(user_id):
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("select * from users where followers like ?", (f"%{user_id}%",))
    rows = c.fetchall()
    conn.close()
    if rows is None:
        return 0
    else:
        return rows

def get_user_by_following(user_id):
    conn = create_connection(sqlite_file)
    c = conn.cursor()
    c.row_factory = dict_factory
    c.execute("select * from users where following like ?", (f"%{user_id}%",))
    rows = c.fetchall()
    conn.close()
    if rows is None:
        return 0
    else:
        return rows

def parser_main(client):
   if args.user_name:
       #Get username info
        ch_user_name = args.user_name
        x,user_data = get_user_info_by_username(client, ch_user_name)
        print(x)
   if args.user_id:
       #Get user info by id
       x, user_data = get_user_info_by_id(client, args.user_id)
       print(x)
   if args.invite:
       #Get invite gpraph
       net = Network(height='100%', width='100%')
       get_invite_graph(client, net, args.invite)
       print(f"Done! Find graph in ch-invitechain-{args.invite}.html file")
       net.show(f'ch-invitechain-{args.invite}.html')
   if args.followers:
       # Get all followers
       followers = get_followers(client, user_id=args.user_id, username=args.user_name)
       i = 0
       for user_id in followers:
           logger.info(f"Parsed {i}/{len(followers)} followers")
           get_user_info_by_id(client, user_id)
           i = i+1
   if args.following:
       # Get all followers
       following = get_following(client, user_id=args.user_id, username=args.user_name)
       i = 0
       for user_id in following:
           logger.info(f"Parsed {i}/{len(following)} followings")
           get_user_info_by_id(client, user_id)
           i = i+1
   if args.invited_by:
       net = Network(height='100%', width='100%')
       user = get_user_from_db_by_username(args.invited_by)
       net.add_node(user['user_id'], label=user['name'])
       invited_by_graph(client,net, user['user_id'])
       print(f"Done!\nFind graph in ch-invited-by-{args.args.invited_by}.html file")
       net.show(f'ch-invited-by-{args.args.invited_by}.html')
   if args.inv_all:
       net = Network(height='100%', width='100%')
       conn = create_connection(sqlite_file)
       c = conn.cursor()
       c.row_factory = dict_factory
       c.execute("select user_id from users where invited_by IS NOT NULL")
       all_users = c.fetchall()
       conn.close()
       if all_users is None:
           return 0
       else:
           i = 0
           all = len(all_users)
           for user in all_users:
               logger.info(f"Added {i}/{all}")
               invited_by_graph(client, net, user["user_id"])
               i=i+1
       print(f"Done!\nFind graph in ch-inv-all.html file")
       net.show(f'ch-inv-all.html')
   if args.followed_by:
       net = Network(height='100%', width='100%', directed=True)
       net.set_options("""
                var options = {
                  "physics": {
                    "barnesHut": {
                      "gravitationalConstant": -16140,
                      "springLength": 230,
                      "avoidOverlap": 0.15
                    },
                    "minVelocity": 0.75
                  }
                }
       """)
       conn = create_connection(sqlite_file)
       c = conn.cursor()
       c.row_factory = dict_factory
       c.execute("select user_id from users where followers IS NOT NULL")
       all_users = c.fetchall()
       conn.close()
       if all_users is None:
           return 0
       else:
           user = get_user_from_db_by_username(args.followed_by)
           followed_by_graph(client, net, user["user_id"])
       print(f"Done!\nFind graph in ch-followed-by-{args.followed_by}.html file")
       net.show(f'ch-followed-by-{args.followed_by}.html')
   if args.group:
       net = Network(height='100%', width='100%')
       club = client.get_club(args.group)
       net.add_node(club['club']['club_id'],label = club['club']['name'], title= f"<img src=\"{club['club']['photo_url']}\" width=\"100\" height=\"100\">"
                                                                                 f"<br>Description:{club['club']['description']}")
       logger.info(f"Getting info about group {club['club']['name']}")
       club_members = client.get_club_members(club['club']['club_id'],page_size=5000)
       if club_members["success"]:
           i = 0
           for member in club_members["users"]:
               logger.info(f"Adding member: {i}/{len(club_members['users'])}")
               log_user_data_short(member)
               net.add_node(member['user_id'], label=member['name'], title=f"username:{str(member['username'])}<br>"
                                                                               f"bio:{member['bio']}<br>"
                                                                               f"<img src=\"{member['photo_url']}\" width=\"100\" height=\"100\">")
               net.add_edge(member['user_id'], club['club']['club_id'], arrows="to")
               i+=1
       net.set_options('''
            var options = {
              "physics": {
                "repulsion": {
                  "springConstant": 0
                },
                "minVelocity": 0.75,
                "solver": "repulsion"
              }
            }
       ''')
       # net.show_buttons(filter_=['physics'])
       print(f"Done!\nCheck file ch-group-{args.group}.html with group's users graph")
       net.show(f'ch-group-{args.group}.html')
   if args.find_by_bio:
       x = PrettyTable()
       x.field_names = ["user_id", "name", "displayname", "photo_url", "username", "bio", "twitter", "instagram",
                        "followers", "following", "invited by", "invited by name"]
       net = Network(height='100%', width='100%')
       users_id=[]
       logger.info(f"Searching users with {args.find_by_bio} in bio")
       users = search_in_bio(args.find_by_bio)
       i = 1
       for user in users:
           users_id.append(user['user_id'])
       for user in users:
           logger.info(f"Adding {i}/{len(users)}")
           i+=1
           net.add_node(user['user_id'], label=user['name'], title=f"username:{str(user['username'])}<br>"
                                                                           f"twitter:{user['twitter']}<br>"
                                                                           f"bio:{user['bio']}<br>"
                                                                           f"<img src=\"{user['photo_url']}\" width=\"100\" height=\"100\">")
           if not is_full_info(user_id = user['user_id']):
               get_user_info_by_id(client, user['user_id'])
           user_followers = get_user_by_following(user['user_id'])
           user_following = get_user_by_follower(user['user_id'])
           x.add_row([user["user_id"],
                      user["name"],
                      user["displayname"],
                      user["photo_url"],
                      user["username"],
                      user["bio"],
                      user["twitter"],
                      user["instagram"],
                      user["num_followers"],
                      user["num_following"],
                      user["invited_by"],
                      user["invited_by_name"]])
           for follower in user_followers:
               if follower['user_id'] in users_id:
                   net.add_node(follower['user_id'], label=follower['name'],
                                title=f"username:{str(follower['username'])}<br>"
                                      f"twitter:{follower['twitter']}<br>"
                                      f"bio:{follower['bio']}<br>"
                                      f"<img src=\"{follower['photo_url']}\" width=\"100\" height=\"100\">")
                   net.add_edge(user['user_id'], follower['user_id'], arrows="to")
                   x.add_row([follower["user_id"],
                              follower["name"],
                              follower["displayname"],
                              follower["photo_url"],
                              follower["username"],
                              follower["bio"],
                              follower["twitter"],
                              follower["instagram"],
                              follower["num_followers"],
                              follower["num_following"],
                              follower["invited_by"],
                              follower["invited_by_name"]])

           for following in user_following:
               if following['user_id'] in users_id:
                   net.add_node(following['user_id'], label=following['name'],
                            title=f"username:{str(following['username'])}<br>"
                                  f"twitter:{following['twitter']}<br>"
                                  f"bio:{following['bio']}<br>"
                                  f"<img src=\"{following['photo_url']}\" width=\"100\" height=\"100\">")
                   net.add_edge(user['user_id'], following['user_id'], arrows="to")
                   x.add_row([following["user_id"],
                              following["name"],
                              following["displayname"],
                              following["photo_url"],
                              following["username"],
                              following["bio"],
                              following["twitter"],
                              following["instagram"],
                              following["num_followers"],
                              following["num_following"],
                              following["invited_by"],
                              following["invited_by_name"]])
       net.set_options('''
            var options = {
              "physics": {
                "repulsion": {
                  "springConstant": 0
                },
                "minVelocity": 0.75,
                "solver": "repulsion"
              }
            }
       ''')
       # net.show_buttons(filter_=['physics'])
       net.show(f'ch-search-{args.find_by_bio}.html')
       print(x)
       print(f"Done!\nFind graph in ch-search-{args.find_by_bio}.html file")


def user_authentication(client):
    """ (Clubhouse) -> NoneType

    Just for authenticating the user.
    """

    result = None
    while True:
        user_phone_number = input("[.] Please enter your phone number. (+818043217654) > ")
        result = client.start_phone_number_auth(user_phone_number)
        if not result['success']:
            print(f"[-] Error occured during authentication. ({result['error_message']})")
            continue
        break

    result = None
    while True:
        verification_code = input("[.] Please enter the SMS verification code (1234, 0000, ...) > ")
        result = client.complete_phone_number_auth(user_phone_number, verification_code)
        if not result['success']:
            print(f"[-] Error occured during authentication. ({result['error_message']})")
            continue
        break

    user_id = result['user_profile']['user_id']
    user_token = result['auth_token']
    user_device = client.HEADERS.get("CH-DeviceId")
    write_config(user_id, user_token, user_device)

    print("[.] Writing configuration file complete.")

    if result['is_waitlisted']:
        print("[!] You're still on the waitlist. Find your friends to get yourself in.")
        return

    # Authenticate user first and start doing something
    client = Clubhouse(
        user_id=user_id,
        user_token=user_token,
        user_device=user_device
    )
    if result['is_onboarding']:
        process_onboarding(client)

    return

def main():
    """
    Initialize required configurations, start with some basic stuff.
    """
    # Initialize configuration
    client = None
    user_config = read_config()
    user_id = user_config.get('user_id')
    user_token = user_config.get('user_token')
    user_device = user_config.get('user_device')

    # Check if user is authenticated
    if user_id and user_token and user_device:
        client = Clubhouse(
            user_id=user_id,
            user_token=user_token,
            user_device=user_device
        )

        # Check if user is still on the waitlist
        _check = client.check_waitlist_status()
        if _check['is_waitlisted']:
            print("[!] You're still on the waitlist. Find your friends to get yourself in.")
            return

        # Check if user has not signed up yet.
        _check = client.me()
        if not _check['user_profile'].get("username"):
            process_onboarding(client)

        parser_main(client)
    else:
        client = Clubhouse()
        user_authentication(client)
        main()

if __name__ == "__main__":
    main()
