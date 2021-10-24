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

ruTag: int = 32
BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'


def update_squad(squad_id: int, db_conn: sqlite3.Connection) -> bool:
    r"""Update/insert information about squadron with specified id in our DB

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
        if squad in DB and isn't deleted
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


update_squad(65555, db)
update_squad(65555, db)
