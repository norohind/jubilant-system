import signal
import sqlite3
import sys
import time

import sql_requests
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()
db = sqlite3.connect('squads.sqlite')

with open('sql_schema.sql', 'r', encoding='utf-8') as schema_file:
    db.executescript(''.join(schema_file.readlines()))

shutting_down: bool = False
can_be_shutdown: bool = False

"""
TODO:
1. Hooks for update (done)
2. Tags resolver
3. Proper shutdown (done)
4. capi.demb.design special api
5. FID tracking system
6. Log level as argument

=========================DONT RELAY ON news_view=========================

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


def shutdown_callback(sig, frame) -> None:
    logger.info(f'Planning shutdown by {sig} signal')
    global shutting_down
    shutting_down = True

    if can_be_shutdown:
        logger.info('Can be shutdown')
        exit(0)


def discover(back_count: int = 0):
    """Discover new squads
    :param back_count: int how many squads back we should check, it is helpful to recheck newly created squads
    :return:
    """

    # id_to_try = utils.get_last_known_id(db)
    # id_to_try = utils.get_next_id_for_discover(db) - 1
    id_to_try = utils.get_next_hole_id_for_discover(db) - 1
    tries: int = 0
    failed: list = list()
    TRIES_LIMIT_RETROSPECTIVELY: int = 5000
    TRIES_LIMIT_ON_THE_TIME: int = 5

    def smart_tries_limit(_squad_id: int) -> int:  # something smarter but still have to be better

        if _squad_id < 65000:
            return TRIES_LIMIT_RETROSPECTIVELY

        else:
            return TRIES_LIMIT_ON_THE_TIME

    """
    tries_limit, probably, should be something more smart because on retrospectively scan we can
    have large spaces of dead squadrons but when we are discovering on real time, large value of tries_limit
    will just waste our time and, probable, confuses FDEV 
    *Outdated but it still can be more smart*
    """

    if back_count != 0:
        logger.debug(f'back_count = {back_count}')

        squad_id: list
        for squad_id in db.execute(sql_requests.select_new_squads_to_update, (back_count,)).fetchall():
            squad_id: int = squad_id[0]
            logger.debug(f'Back updating {squad_id}')
            utils.update_squad_info(squad_id, db)

    while True:

        if shutting_down:
            return

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


def update(squad_id: int = None, amount_to_update: int = 1, thursday_target: bool = False):
    """

    :param thursday_target: if we aiming to update all squads before thursday (FDEV scheduled maintenance)
    and we don't wanna update squads which already updated after previous thursday
    :param squad_id: update specified squad, updates only that squad
    :param amount_to_update: update specified amount, ignores when squad_id specified
    :return:
    """

    if isinstance(squad_id, int):
        logger.debug(f'Going to update one specified squadron: {squad_id} ID')
        utils.update_squad_info(squad_id, db, suppress_absence=True)
        # suppress_absence is required because if we updating squad with some high id it may just don't exists yet
        return

    logger.debug(f'Going to update {amount_to_update} squadrons with thursday_target = {thursday_target}')

    if thursday_target:
        prev_thursday = utils.get_previous_thursday_severs_reboot_datetime()
        squads_id_to_update: list = db.execute(
            sql_requests.select_squads_to_update_thursday_aimed, (prev_thursday, amount_to_update)).fetchall()

        if len(squads_id_to_update) == 0:
            logger.info(f'thursday_target and no squads to update')

    else:
        squads_id_to_update: list = db.execute(sql_requests.select_squads_to_update, (amount_to_update,)).fetchall()

    for single_squad_to_update in squads_id_to_update:  # if db is empty, then loop will not happen

        if shutting_down:
            return

        id_to_update: int = single_squad_to_update[0]
        logger.info(f'Updating {id_to_update} ID')
        utils.update_squad_info(id_to_update, db)


if __name__ == '__main__':

    signal.signal(signal.SIGTERM, shutdown_callback)
    signal.signal(signal.SIGINT, shutdown_callback)

    def help_cli() -> str:
        return """Possible arguments:
    main.py discover
    main.py update
    main.py update amount <amount: int>
    main.py update id <id: int>
    main.py daemon"""

    logger.debug(f'argv: {sys.argv}')

    if len(sys.argv) == 1:
        print(help_cli())
        exit(1)

    elif len(sys.argv) == 2:
        if sys.argv[1] == 'discover':
            # main.py discover
            logger.info(f'Entering discover mode')
            discover()
            exit(0)

        elif sys.argv[1] == 'update':
            # main.py update
            logger.info(f'Entering common update mode')
            update()
            exit(0)

        elif sys.argv[1] == 'daemon':
            # main.py daemon
            logger.info('Entering daemon mode')
            while True:
                can_be_shutdown = False

                update(amount_to_update=500, thursday_target=True)
                if shutting_down:
                    exit(0)

                logger.info('Updated, sleeping')
                can_be_shutdown = True
                time.sleep(30 * 60)
                can_be_shutdown = False
                logger.info('Discovering')

                discover(back_count=20)
                if shutting_down:
                    exit(0)

                logger.info('Discovered, sleeping')
                can_be_shutdown = True
                time.sleep(30 * 60)

        else:
            print(help_cli())
            exit(1)

    elif len(sys.argv) == 4:
        if sys.argv[1] == 'update':
            if sys.argv[2] == 'amount':
                # main.py update amount <amount: int>

                try:
                    amount: int = int(sys.argv[3])
                    logger.info(f'Entering update amount mode, amount: {amount}')
                    update(amount_to_update=amount)
                    exit(0)

                except ValueError:
                    print('Amount must be integer')
                    exit(1)

            elif sys.argv[2] == 'id':
                # main.py update id <id: int>
                try:
                    id_for_update: int = int(sys.argv[3])
                    logger.info(f'Entering update specified squad: {id_for_update} ID')
                    update(squad_id=id_for_update)
                    exit(0)

                except ValueError:
                    print('ID must be integer')
                    exit(1)

            else:
                logger.info(f'Unknown argument {sys.argv[2]}')

    else:
        print(help_cli())
        exit(1)




