import sqlite3
from . import sqlite_sql_requests
import json


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

    def list_squads_by_tag_with_tags(self, tag: str, pretty_keys=False) -> list:
        """
        Take tag and return all squads with tag matches with user_tags

        :param pretty_keys:
        :param tag:
        :return:
        """

        if pretty_keys:
            sql_req = sqlite_sql_requests.squads_by_tag_extended_pretty_keys
            user_tags_key = 'User tags'

        else:
            sql_req = sqlite_sql_requests.squads_by_tag_extended_raw_keys
            user_tags_key = 'user_tags'

        squads = self.db.execute(sql_req, {'tag': tag.upper()}).fetchall()

        for squad in squads:
            squad[user_tags_key] = json.loads(squad[user_tags_key])

        return squads
