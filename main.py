import sqlite3
import time

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
    update it
    if squad still exists
        process triggers
"""


def discover_triggers(squad_info: dict):
    print(squad_info.get('name'), squad_info.get('tag'), squad_info.get('ownerName'))


def discover():
    id_to_try = utils.get_last_known_id(db)
    tries: int = 0
    failed: list = list()
    tries_limit: int = 5000

    while True:
        id_to_try = id_to_try + 1
        logger.debug(f'Starting discover loop iteration, tries: {tries} of {tries_limit}, id to try {id_to_try}, '
                     f'failed list: {failed}')

        if tries == tries_limit:
            break

        squad_info = utils.update_squad_info(id_to_try, db, suppress_absence=True)

        if isinstance(squad_info, dict):  # success
            logger.debug(f'Success discover for {id_to_try} ID')
            discover_triggers(squad_info)
            tries = 0  # reset tries counter
            for failed_squad in failed:  # since we found an exists squad, then all previous failed wasn't exists
                utils.properly_delete_squadron(failed_squad, db)

            failed = list()

        else:  # should be only False
            logger.debug(f'Fail on discovery for {id_to_try} ID')
            failed.append(id_to_try)
            tries = tries + 1

        time.sleep(2)


discover()
