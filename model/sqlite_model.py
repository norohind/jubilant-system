import sqlite3
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

    def close_model(self) -> None:
        """
        This method should be called before program exit
        :return:
        """

        self.db.close()

    def list_squads_by_tag(self, tag: str, pretty_keys=False) -> list:
        """
        Take tag and return all squads with tag matches without user_tags

        :param pretty_keys:
        :param tag:
        :return:
        """

        if pretty_keys:
            sql_req = sqlite_sql_requests.squads_by_tag_short_pretty_keys

        else:
            sql_req = sqlite_sql_requests.squads_by_tag_short_raw_keys

        squads = self.db.execute(sql_req, {'tag': tag.upper()}).fetchall()

        return squads

    def list_squads_by_tag_with_tags(self, tag: str, pretty_keys=False, motd=False) -> list:
        # TODO: merge it with motd_by_squad_id, change keys names in this method, not in DBMS by a request
        """
        Take tag and return all squads with tag matches with user_tags

        :param motd: if we should return motd with information
        :param pretty_keys:
        :param tag:
        :return:
        """

        if pretty_keys:
            sql_req = sqlite_sql_requests.squads_by_tag_extended_pretty_keys
            user_tags_key = 'User tags'
            motd_key = 'Motd'
            motd_date_key = 'Motd Date'
            motd_author_key = 'Motd Author'
            owner_name_key = 'Owner'
            platform_key = 'Platform'

        else:
            sql_req = sqlite_sql_requests.squads_by_tag_extended_raw_keys
            user_tags_key = 'user_tags'
            motd_key = 'motd'
            motd_date_key = 'motd_date'
            motd_author_key = 'motd_author'
            owner_name_key = 'owner_name'
            platform_key = 'platform'

        squads = self.db.execute(sql_req, {'tag': tag.upper()}).fetchall()

        for squad in squads:
            squad[user_tags_key] = json.loads(squad[user_tags_key])

            if squad[platform_key] != 'PC':  # then we have to try to resolve owner's nickname
                potential_owner_nickname = self.nickname_by_fid_news_based(squad['owner_id'])
                if potential_owner_nickname is not None:
                    squad[owner_name_key] = potential_owner_nickname

                del squad['owner_id']  # delete fid anyway

            if motd:
                motd_dict: dict = self.motd_by_squad_id(squad['squad_id'])

                if motd_dict is None:
                    # if no motd, then all motd related values will be None
                    motd_dict = dict()
                    squad[motd_date_key] = None

                else:
                    squad[motd_date_key] = datetime.utcfromtimestamp(int(motd_dict.get('date'))).strftime('%Y-%m-%d '
                                                                                                          '%H:%M:%S')

                squad[motd_key] = motd_dict.get('motd')
                squad[motd_author_key] = motd_dict.get('author')

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
