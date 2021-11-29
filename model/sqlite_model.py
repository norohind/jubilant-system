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

    def list_squads_by_tag(self, tag: str) -> list:
        """
        Take tag or part of tag and return all squads with tag matches this pattern

        :param tag:
        :return:
        """

        squads = self.db.execute(sqlite_sql_requests.squads_by_tag, {'tag': tag.upper()}).fetchall()

        # for squad in squads:
        #     squad['User tags'] = json.loads(squad['User tags'])

        return squads
