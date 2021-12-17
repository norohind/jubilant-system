import sqlite3

import utils
from . import sqlite_sql_requests
import json
from typing import Union
from datetime import datetime


class SqliteModel:
    db: sqlite3.Connection

    def open_model(self) -> None:
        """
        This method must be called before any action on model
        :return:
        """

        self.db = sqlite3.connect('squads.sqlite', check_same_thread=False)
        self.db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        self.db.create_function('null_fdev', 1, self.null_fdev, deterministic=True)

    def close_model(self) -> None:
        """
        This method should be called before program exit
        :return:
        """

        self.db.close()

    @staticmethod
    def null_fdev(value):
        if value == '':
            return None

        elif value == 'None':
            return None

        else:
            return value

    def list_squads_by_tag(self, tag: str, pretty_keys=False, motd=False, resolve_tags=False, extended=False) -> list:
        """
        Take tag and return all squads with tag matches

        :param extended: if false, then we don't return tags and motd anyway
        :param motd: if we should return motd with information
        :param resolve_tags: if we should resolve tags or return it as plain list of IDs
        :param pretty_keys: if we should use pretty keys or raw column names from DB
        :param tag: tag to get info about squad
        :return:
        """

        squads = self.db.execute(sqlite_sql_requests.squads_by_tag_extended_raw_keys, {'tag': tag.upper()}).fetchall()
        squad: dict
        for squad in squads:
            squad['user_tags'] = json.loads(squad['user_tags'])

            """
            We have, according to arguments, to:
            include motd if extended
            try to resolve owner nickname for consoles
            delete owner_id
            resolve tags if extended
            remove tags if not extended
            make keys pretty
            """

            if extended:
                if motd:  # motd including
                    motd_dict: dict = self.motd_by_squad_id(squad['squad_id'])

                    if motd_dict is None:
                        # if no motd, then all motd related values will be None
                        motd_dict = dict()
                        squad['motd_date'] = None

                    else:
                        squad['motd_date'] = datetime.utcfromtimestamp(int(motd_dict.get('date')))\
                            .strftime('%Y-%m-%d %H:%M:%S')

                    squad['motd'] = motd_dict.get('motd')
                    squad['motd_author'] = motd_dict.get('author')

                if resolve_tags:  # tags resolving
                    squad['user_tags'] = utils.humanify_resolved_user_tags(utils.resolve_user_tags(squad['user_tags']))

            else:
                del squad['user_tags']  # remove user_tags for short

            if squad['platform'] != 'PC':  # then we have to try to resolve owner's nickname
                potential_owner_nickname = self.nickname_by_fid_news_based(squad['owner_id'])
                if potential_owner_nickname is not None:
                    squad['owner_name'] = potential_owner_nickname

            del squad['owner_id']  # delete fid anyway

            # prettify keys
            if pretty_keys:
                for key in list(squad.keys()):

                    pretty_key = utils.pretty_keys_mapping.get(key, key)
                    squad[pretty_key] = squad.pop(key)

        return squads

    def motd_by_squad_id(self, squad_id: int) -> Union[dict, None]:
        """
        Take squad_id and returns dict with last motd: motd, date, author keys. It also can return None if motd isn't
        set for squad

        :param squad_id:
        :return:
        """

        sql_req = self.db.execute(sqlite_sql_requests.select_latest_motd_by_id, {'squad_id': squad_id})

        return sql_req.fetchone()

    def nickname_by_fid_news_based(self, fid: str) -> Union[str, None]:
        sql_req = self.db.execute(sqlite_sql_requests.select_nickname_by_fid_news_based, {'fid': fid})

        sql_result = sql_req.fetchone()
        if sql_result is None:
            return None

        else:
            return sql_result['author']
