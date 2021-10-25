import sqlite3
import time

import sql_requests
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()
db = sqlite3.connect('squads.sqlite')

with open('sql_schema.sql', 'r', encoding='utf-8') as schema_file:
    db.executescript(''.join(schema_file.readlines()))

ruTag: id = 32

"""
Two modes:
1. Discover new squads
    get last_known_id
    tries = 0
    failed: list
    while True
        if tries = 2
            break

        id_to_try = last_known_id + 1
        update squad info with id_to_try and suppressing absence 
        
        if success
            process triggers
            tries = 0
            for failed_squad in failed
                delete(failed_squad)
                failed_squad = list()
        
        else (fail)
            failed.append(id_to_try)
            tries = tries + 1
            
        sleep(3)
            
            
2. Update exists
    get oldest updated existing squad
    
    if DB is empty
        return
        
    update it
    if squad still exists
        process triggers
"""


def discover():
    """Discover new squads

    :return:
    """

    id_to_try = utils.get_last_known_id(db)
    tries: int = 0
    failed: list = list()
    TRIES_LIMIT_RETROSPECTIVELY: int = 5000
    TRIES_LIMIT_ON_THE_TIME: int = 5

    def smart_tries_limit(squad_id: int) -> int:  # something smarter but still have to be better

        if id_to_try < 65000:
            return TRIES_LIMIT_RETROSPECTIVELY

        else:
            return TRIES_LIMIT_ON_THE_TIME

    """
    tries_limit, probably, should be something more smart because on retrospectively scan we can
    have large spaces of dead squadrons but when we are discovering on real time, large value of tries_limit
    will just waste our time and, probable, confuses FDEV
    """

    while True:
        id_to_try = id_to_try + 1
        # logger.debug(f'Starting discover loop iteration, tries: {tries} of {tries_limit}, id to try {id_to_try}, '
        #             f'failed list: {failed}')

        if tries == smart_tries_limit(id_to_try):
            break

        squad_info = utils.update_squad_info(id_to_try, db, suppress_absence=True)

        if isinstance(squad_info, dict):  # success
            logger.debug(f'Success discover for {id_to_try} ID')
            tries = 0  # reset tries counter

            for failed_squad in failed:  # since we found an exists squad, then all previous failed wasn't exists
                utils.properly_delete_squadron(failed_squad, db)

            failed = list()

        else:  # fail, should be only False
            logger.debug(f'Fail on discovery for {id_to_try} ID')
            failed.append(id_to_try)
            tries = tries + 1

        time.sleep(3)


def update(squad_id: int = None, amount_to_update: int = 1):
    """

    :param squad_id: update specified squad, updates only that squad
    :param amount_to_update: update specified amount, ignores when squad_id specified
    :return:
    """

    if isinstance(squad_id, int):
        logger.debug(f'Going to update one specified squadron: {squad_id} ID')
        utils.update_squad_info(squad_id, db)
        return

    logger.debug(f'Going to update {amount_to_update} squadrons')
    squads_id_to_update: list = db.execute(sql_requests.select_squads_to_update, (amount_to_update,)).fetchall()

    for single_squad_to_update in squads_id_to_update:  # if db is empty, then loop will not happen
        id_to_update: int = single_squad_to_update[0]
        logger.debug(f'Updating {id_to_update}')
        utils.update_squad_info(id_to_update, db)
        time.sleep(3)


discover()
