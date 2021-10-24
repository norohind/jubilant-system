import json
import requests
import sqlite3
import time
import datetime
import utils
from EDMCLogging import get_main_logger
import sql_requests

logger = get_main_logger()
db = sqlite3.connect('squads.sqlite')

with open('sql_schema.sql', 'r', encoding='utf-8') as schema_file:
    db.executescript(''.join(schema_file.readlines()))

ruTag = 32
BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'


def update_squad_news(squad_id: int, db_conn: sqlite3.Connection) -> bool:
    """Update news for squad with specified ID

    :param squad_id: id of squad to insert news
    :param db_conn: connection to sqlite DB
    :return: True if squad exists, False if not
    :rtype: bool
    """

    """
    How it should works?
    Request news
    if squad doesn't exists
        return False
    
    else
        insert all news even if it already exist in DB
        return True
    """
    news_request: requests.Response = utils.authed_request(BASE_URL + NEWS_ENDPOINT, params={'squadronId': squad_id})
    if news_request.status_code != 200:  # must not happen
        logger.warning(f'Got not 200 status code on requesting news, content: {news_request.content}')
        # we will not break it, let next code break it by itself

    squad_news: dict = news_request.json()['squadron']

    if 'id' not in squad_news.keys():  # squadron doesn't FDEV
        return False

    else:  # squadron exists FDEV
        del squad_news['id']

        for type_of_news_key in squad_news:
            one_type_of_news: list = squad_news[type_of_news_key]

            news: dict
            for news in one_type_of_news:
                with db_conn:
                    db_conn.execute(
                        sql_requests.insert_news,
                        (
                            squad_id,
                            type_of_news_key,
                            news.get('id'),
                            news.get('date'),
                            news.get('category'),
                            news.get('activity'),
                            news.get('season'),
                            news.get('bookmark'),
                            news.get('motd'),
                            news.get('author'),
                            news.get('cmdr_id'),
                            news.get('user_id')
                        )
                    )

        return True


def update_squad_info(squad_id: int, db_conn: sqlite3.Connection) -> bool:
    """Update/insert information about squadron with specified id in our DB

    :param squad_id: id of squad to update/insert
    :param db_conn: connection to sqlite DB
    :return: True if squad exists, False if not
    :rtype: bool
    """

    """
    How it should works?
    Request squad's info
    if squad exists FDEV
        insert info in DB
        request news, insert to DB
        return True
    
    if squad doesn't exists FDEV
        if squad in DB and isn't deleted in our DB
            write to squads_states record with all null except ID (it will mean that squad was deleted)
            
       return False
    *Should we return something more then just a bool, may be a message to notify_discord?
    """

    squad_request: requests.Response = utils.authed_request(BASE_URL + INFO_ENDPOINT, params={'squadronId': squad_id})

    if squad_request.status_code == 200:  # squad exists FDEV
        squad_request_json: dict = squad_request.json()['squadron']
        with db_conn:
            db_conn.execute(
                sql_requests.insert_squad_states,
                (
                    squad_id,
                    squad_request_json['name'],
                    squad_request_json['tag'],
                    utils.fdev2people(squad_request_json['ownerName']),
                    squad_request_json['ownerId'],
                    squad_request_json['platform'],
                    squad_request_json['created'],
                    squad_request_json['created_ts'],
                    squad_request_json['acceptingNewMembers'],
                    squad_request_json['powerId'],
                    squad_request_json['powerName'],
                    squad_request_json['superpowerId'],
                    squad_request_json['superpowerName'],
                    squad_request_json['factionId'],
                    squad_request_json['factionName'],
                    json.dumps(squad_request_json['userTags']),
                    squad_request_json['memberCount'],
                    squad_request_json['pendingCount'],
                    squad_request_json['full'],
                    squad_request_json['publicComms'],
                    squad_request_json['publicCommsOverride'],
                    squad_request_json['publicCommsAvailable'],
                    squad_request_json['current_season_trade_score'],
                    squad_request_json['previous_season_trade_score'],
                    squad_request_json['current_season_combat_score'],
                    squad_request_json['previous_season_combat_score'],
                    squad_request_json['current_season_exploration_score'],
                    squad_request_json['previous_season_exploration_score'],
                    squad_request_json['current_season_cqc_score'],
                    squad_request_json['previous_season_cqc_score'],
                    squad_request_json['current_season_bgs_score'],
                    squad_request_json['previous_season_bgs_score'],
                    squad_request_json['current_season_powerplay_score'],
                    squad_request_json['previous_season_powerplay_score'],
                    squad_request_json['current_season_aegis_score'],
                    squad_request_json['previous_season_aegis_score']
                )
            )

            update_squad_news(squad_id, db_conn)
            return True

    elif squad_request.status_code == 404:  # squad doesn't exists FDEV
        if db_conn.execute(
                sql_requests.check_if_squad_exists_in_db,
                (squad_id,)).fetchone()[0] > 0:  # we have it in DB

            if db_conn.execute(sql_requests.check_if_we_already_deleted_squad_in_db, (squad_id,)).fetchone()[0] == 0:
                # we don't have it deleted in DB
                with db_conn:
                    db_conn.execute(sql_requests.properly_delete_squad, (squad_id,))

        return False  # squadron stop their existing or never exists... it doesn't exists anyway

    else:  # any other codes (except 418, that one handles in authed_request), never should happen
        logger.warning(f'Unknown squad info status_code: {squad_request.status_code}, content: {squad_request.content}')
        raise utils.FAPIUnknownStatusCode







update_squad_info(47999, db)
