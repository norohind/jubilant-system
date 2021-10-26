"""
for list of hooks refer to doc.txt, search by "hooks (don't mismatch with DB hooks)"
common structure:
1. Exists notify function for every hook type that calls from appropriate places
2. Notify function call every appropriate hook

Should we have separate triggers for update and insert cases?
"""
import sqlite3
import typing
import json
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


def detect_important_changes_ru_squads(squad_info: dict, db_conn: sqlite3.Connection) -> None:
    """Alert if something important changed for a russian squad

    :param squad_info: FDEV authored dict
    :param db_conn:
    :return:
    """

    """
    how it should works?
    Works only with updated (not firstly inserted) squads
    1. Detect if squad just set/took ru tag
    2. Detect if squad changed members count
    3. Detect if squad changed motd
    4. Detect if squad changed ownership
    5. Notify discord
    """

    squad_id = squad_info['id']
    if db_conn.execute(sql_requests.check_if_squad_exists_in_db, (squad_id,)).fetchone()[0] == 1:
        # we just discover squad, not updating
        return

    new, old = old_new('user_tags', db_conn, squad_id)
    new_tags: list = json.loads(new)
    old_tags: list = json.loads(old)

    message: str = str()

    # let's find out situation with RU tag
    if 32 not in new_tags and 32 not in old_tags:
        # squadron wasn't russian, isn't russian
        return

    elif 32 in new_tags and 32 in old_tags:
        # squadron was russian, is russian
        pass

    elif 32 in new_tags and 32 not in old_tags:
        # squadron wasn't russian and is russian
        message = message + 'Squadron become russian\n'

    elif 32 not in new_tags and 32 in old_tags:
        # squadron was russian, isn't russian
        message = message + 'Squadron stop being russian\n'

    # let's clarify situation with members count
    new_members, old_members = old_new('member_count', db_conn, squad_id)

    if new_members == old_members:
        # count wasn't changed
        pass

    else:
        message = message + f'Members count changed {old_members} -> {new_members}\n'

    # let's check motd
    new_motd, old_motd = old_new_news('motd', db_conn, squad_id)  # TODO: make easier and better

    if new_motd == old_motd:
        # motd wasn't changed
        pass

    else:
        message = message + f'Motd changed, old:\n```\n{old_motd}\n```\nnew:\n```\n{new_motd}\n```\n'

    # let's check ownership
    new_owner, old_owner = old_new('owner_name', db_conn, squad_id)

    if new_owner == old_owner:
        # the same owner
        pass

    else:
        message = message + f'Ownership changed: {old_owner} -> {new_owner}\n'

    if len(message) != 0:
        utils.notify_discord(f'State changing for `{squad_info["name"]}`\n'
                             f'platform: {squad_info["platform"]}\n' + message)

    return


def detect_removing_ru_squads(squad_id: int, db_conn: sqlite3.Connection):
    """Send alert to discord if was removed russian squad

    :param squad_id:
    :param db_conn:
    :return:
    """

    """
    Detect if removing squad was russian
    send alert 
    """
    important = db_conn.execute(sql_requests.select_important_before_delete, (squad_id,)).fetchone()

    if important is None:
        return  # squad doesn't exists in our DB so we can't figure out anything about it

    name = important[0]
    platform = important[1]
    members = important[2]
    tag = important[3]
    user_tags = json.loads(important[4])

    if 32 in user_tags:
        # ru squad
        message = f'Deleted squad `{name}`\nplatform: {platform}, members: {members}, tag: {tag}'
        utils.notify_discord(message)

    return


# should I move it to utils?
def old_new(column: str, db_conn: sqlite3.Connection, squad_id: int) -> typing.Tuple[typing.Any, typing.Any]:
    """Returns last two record for squad_id for specified column

    :param column:
    :param db_conn:
    :param squad_id:
    :return:
    """
    sql_req: sqlite3.Cursor = db_conn.execute(sql_requests.select_old_new.format(column=column), (squad_id,))

    new = sql_req.fetchone()[0]
    old = sql_req.fetchone()[0]

    return new, old


def old_new_news(column: str, db_conn: sqlite3.Connection, squad_id: int) -> typing.Tuple[typing.Any, typing.Any]:
    """Returns last two record for squad_id for specified column

    :param column:
    :param db_conn:
    :param squad_id:
    :return:
    """
    sql_req: sqlite3.Cursor = db_conn.execute(sql_requests.select_old_new_news.format(column=column), (squad_id,))

    try:
        new = sql_req.fetchone()[0]

    except TypeError:
        new = None

    try:
        old = sql_req.fetchone()[0]

    except TypeError:
        old = None

    return new, old


insert_data_hooks.append(detect_new_ru_squads)
insert_data_hooks.append(detect_important_changes_ru_squads)