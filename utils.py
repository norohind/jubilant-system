import os
import sqlite3
from typing import Union
import requests
import json
from EDMCLogging import get_main_logger
import hooks
import sql_requests

logger = get_main_logger()

BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'


class FAPIDownForMaintenance(Exception):
    pass


class FAPIUnknownStatusCode(Exception):
    pass


def authed_request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    """Makes request to any url with valid bearer token

    :param url: url to make request
    :param method: method to make request, case insensitive, get by default
    :param kwargs: will be passed to requests.request
    :return: requests.Response object
    """
    bearer: str = _get_bearer()

    logger.debug(f'Requesting {method.upper()} {url!r}, kwargs: {kwargs}')

    fapiRequest: requests.Response = requests.request(
        method=method,
        url=url,
        headers={'Authorization': f'Bearer {bearer}'},
        **kwargs
    )

    logger.debug(f'Request complete, code {fapiRequest.status_code!r}, len {len(fapiRequest.content)}')

    if fapiRequest.request == 418:  # it does it on maintenance
        logger.warning(f'{method.upper()} {fapiRequest.url} returned 418, content dump:\n{fapiRequest.content}')
        raise FAPIDownForMaintenance

    return fapiRequest


def _get_bearer() -> str:
    """Gets bearer token from capi.demb.design (companion-api project)

    :return: bearer token as str
    """
    bearer_request: requests.Response = requests.get(
        url='https://capi.demb.design/random_token', headers={'auth': os.environ['DEMB_CAPI_AUTH']})

    try:
        bearer: str = bearer_request.json()['access_token']

    except Exception as e:
        logger.exception(f'Unable to parse capi.demb.design answer\nrequested: {bearer_request.url!r}\n'
                         f'code: {bearer_request.status_code!r}\nresponse: {bearer_request.content!r}', exc_info=e)
        raise e

    return bearer


def fdev2people(hex_str: str) -> str:
    """Converts string with hex chars to string"""
    return bytes.fromhex(hex_str).decode('utf-8')


def notify_discord(message: str) -> None:
    """Just sends message to discord, without rate limits respect"""
    logger.debug('Sending discord message')

    # hookURL: str = 'https://discord.com/api/webhooks/896514472280211477/LIKgbgNIr9Nvuc-1-FfylAIY1YV-a7RMjBlyBsVDellMbnokXLYKyBztY1P9Q0mabI6o'  # noqa: E501  # FBSC
    hookURL: str = 'https://discord.com/api/webhooks/902216904507260958/EIUwZ05r0_U2oa_xz8aVVEJyTC6DVk4ENxGYSde8ZNU7aMWBsc3Bo_gBis1_yUxJc3CC'  # noqa: E501  # dev FBSC
    content: bytes = f'content={requests.utils.quote(message)}'.encode('utf-8')

    if len(content) >= 2000:  # discord limitation
        logger.warning(f'Refuse to send len={len(content)}, content dump:\n{content}')
        return

    discord_request: requests.Response = requests.post(
        url=hookURL,
        data=content,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    try:
        discord_request.raise_for_status()

    except Exception as e:
        logger.exception(f'Fail on sending message to discord ({"/".join(hookURL.split("/")[-2:])})'
                         f'\n{discord_request.content}', exc_info=e)
        return

    logger.debug('Sending successful')
    return


def _update_squad_news(squad_id: int, db_conn: sqlite3.Connection) -> Union[bool, str]:
    """Update news for squad with specified ID

    :param squad_id: id of squad to insert news
    :param db_conn: connection to sqlite DB
    :return: motd if squad exists, False if not
    :rtype: bool, str
    """

    """
    How it should works?
    Request news
    if squad doesn't exists
        return False
    
    else
        insert all news even if it already exist in DB
        return motd
    """

    news_request: requests.Response = authed_request(BASE_URL + NEWS_ENDPOINT, params={'squadronId': squad_id})
    if news_request.status_code != 200:  # must not happen
        logger.warning(f'Got not 200 status code on requesting news, content: {news_request.content}')
        # we will not break it, let next code break it by itself

    squad_news: dict = news_request.json()['squadron']

    if isinstance(squad_news, list):  # check squadron 2517 for example 0_0
        logger.info(f'squad_news is list for {squad_id}: {squad_news}')
        return False

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

        return next(iter(squad_news['public_statements']), dict()).get('motd', '')


def update_squad_info(squad_id: int, db_conn: sqlite3.Connection, suppress_absence: bool = False) -> Union[bool, dict]:
    """Update/insert information about squadron with specified id in our DB

    :param squad_id: id of squad to update/insert
    :param db_conn: connection to sqlite DB
    :param suppress_absence: if we shouldn't mark squad as deleted if we didn't found it by FDEV
    :return: squad dict if squad exists, False if not
    :rtype: bool, dict
    """

    """
    How it should works?
    *properly delete squad in our DB mean write to squads_states record with all null except ID 
    Request squad's info
    
    if squad is properly deleted in our DB
        return False

    if squad exists FDEV
        insert info in DB
        request news, insert to DB
        return squad dict
    
    if squad doesn't exists FDEV
        if squad in DB
            if isn't deleted in our DB
                 properly delete squad

        else if not suppress_absence
            properly delete squad
            
            
            
       return False
    *Should we return something more then just a bool, may be a message to notify_discord?
    """

    if db_conn.execute(sql_requests.check_if_we_already_deleted_squad_in_db, (squad_id,)).fetchone()[0] != 0:
        # we have it as properly deleted in our DB
        logger.debug(f'squad {squad_id} is marked as deleted in our DB, returning False')
        return False

    squad_request: requests.Response = authed_request(BASE_URL + INFO_ENDPOINT, params={'squadronId': squad_id})

    if squad_request.status_code == 200:  # squad exists FDEV
        squad_request_json: dict = squad_request.json()['squadron']
        squad_request_json['ownerName'] = fdev2people(squad_request_json['ownerName'])  # normalize value

        with db_conn:
            db_conn.execute(
                sql_requests.insert_squad_states,
                (
                    squad_id,
                    squad_request_json['name'],
                    squad_request_json['tag'],
                    squad_request_json['ownerName'],
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

            motd: str = _update_squad_news(squad_id, db_conn)  # yeah, it can return bool but never should does it
            squad_request_json.update(motd=motd)

            hooks.notify_insert_data(squad_request_json, db_conn)  # call hook

            return squad_request_json

    elif squad_request.status_code == 404:  # squad doesn't exists FDEV
        if db_conn.execute(
                sql_requests.check_if_squad_exists_in_db,
                (squad_id,)).fetchone()[0] > 0:  # we have it in DB

            if db_conn.execute(sql_requests.check_if_we_already_deleted_squad_in_db, (squad_id,)).fetchone()[0] == 0:
                # we don't have it deleted in DB, let's fix it
                properly_delete_squadron(squad_id, db_conn)

        elif not suppress_absence:
            # we don't have it in DB at all but let's mark it as deleted to avoid requests to FDEV about it in future
            properly_delete_squadron(squad_id, db_conn)

        return False  # squadron stop their existing or never exists... it doesn't exists anyway

    else:  # any other codes (except 418, that one handles in authed_request), never should happen
        logger.warning(f'Unknown squad info status_code: {squad_request.status_code}, content: {squad_request.content}')
        raise FAPIUnknownStatusCode(f'Status code: {squad_request.status_code}, content: {squad_request.content}')


def properly_delete_squadron(squad_id: int, db_conn: sqlite3.Connection) -> None:
    """Properly deletes squadron from our DB

    :param squad_id: squad id to delete
    :param db_conn: connection to DB
    :return:
    """
    logger.debug(f'Properly deleting {squad_id}')

    hooks.notify_properly_delete(squad_id, db_conn)

    with db_conn:
        db_conn.execute(sql_requests.properly_delete_squad, (squad_id,))


def get_last_known_id(db_conn: sqlite3.Connection) -> int:
    sql_request_result = db_conn.execute(sql_requests.select_last_known_id).fetchone()
    if sql_request_result is None:
        logger.debug(f"Can't get last know id from DB, defaulting to 0")
        return 0

    else:
        logger.debug(f'last know id from DB: {sql_request_result[0]}')
        return sql_request_result[0]


def get_next_hole_id_for_discover(db_conn: sqlite3.Connection) -> int:
    """Returns first unexisting id in DB
    :param db_conn:
    :return: last known id if we iterate from 1 to ...
    """

    sql_req = db_conn.execute(sql_requests.select_first_hole_id).fetchone()
    if sql_req is None:
        logger.debug(f"Can't get last know id from DB, defaulting to 1")
        return 1

    else:
        logger.debug(f'Next unknown id from DB: {sql_req[0]}')
        return sql_req[0]
