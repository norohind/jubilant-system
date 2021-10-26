"""
for list of hooks refer to doc.txt, search by "hooks (don't mismatch with DB hooks)"
common structure:
1. Exists notify function for every hook type that calls from appropriate places
2. Notify function call every appropriate hook

Should we have separate triggers for update and insert cases?
"""
import sqlite3
import typing

import sql_requests
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()

properly_delete_hooks: list[typing.Callable] = list()
insert_data_hooks: list[typing.Callable] = list()


def notify_properly_delete(squad_id: int, db_conn: sqlite3.Connection) -> None:
    """Notifies all properly delete hooks, calls before deleting

    :param squad_id:
    :param db_conn:
    :return:
    """
    # logger.debug(f'Notifying properly delete squad hooks for {squad_id} ID')

    for hook in properly_delete_hooks:
        hook(squad_id, db_conn)


def notify_insert_data(squad_info: dict, db_conn: sqlite3.Connection) -> None:
    """Notifies all insert data hooks, calls after inserting

    :param squad_info:
    :param db_conn:
    :return:
    """

    # logger.debug(f'Notifying insert data hooks for {squad_info["id"]} ID')
    for hook in insert_data_hooks:
        hook(squad_info, db_conn)


def detect_new_ru_squads(squad_info: dict, db_conn: sqlite3.Connection) -> None:
    """Sends alert if it was firstly discovered ru squad with >5 members

    :param squad_info:
    :param db_conn:
    :return:
    """

    """
    Determine if we just discover squad, not updating it
    check if is 32 in tag (means russian squad)
    check if members count satisfies low threshold
    send alert  
    """
    MEMBERS_LOW_THRESHOLD: int = 5

    if db_conn.execute(sql_requests.check_if_squad_exists_in_db, (squad_info['id'],)).fetchone()[0] == 1:
        # squad has only one record, it means squad just discovered

        if 32 in squad_info['userTags']:
            # it's russian squad

            if squad_info['memberCount'] > MEMBERS_LOW_THRESHOLD:

                if len(squad_info['motd']) == 0:
                    motd = ''

                else:
                    motd = f"`{squad_info['motd']}`"
                previous_season_sum: int = squad_info['previous_season_trade_score'] + \
                                           squad_info['previous_season_combat_score'] + \
                                           squad_info['previous_season_exploration_score'] + \
                                           squad_info['previous_season_cqc_score'] + \
                                           squad_info['previous_season_bgs_score'] + \
                                           squad_info['previous_season_powerplay_score'] + \
                                           squad_info['previous_season_aegis_score']
                current_season_sum: int = squad_info['current_season_trade_score'] + \
                                          squad_info['current_season_combat_score'] + \
                                          squad_info['current_season_exploration_score'] + \
                                          squad_info['current_season_cqc_score'] + \
                                          squad_info['current_season_bgs_score'] + \
                                          squad_info['current_season_powerplay_score'] + \
                                          squad_info['current_season_aegis_score']
                message = f"""
New russian squad with more then {MEMBERS_LOW_THRESHOLD} members: {squad_info['name']}
members: {squad_info['memberCount']}
tag: {squad_info['tag']}
created: {squad_info['created']}
platform: {squad_info['platform']}
owner: {squad_info['ownerName']}
activity:
    previous season sum: {previous_season_sum}
    current season sum: {current_season_sum}
motd: {motd}"""

                utils.notify_discord(message)


insert_data_hooks.append(detect_new_ru_squads)
