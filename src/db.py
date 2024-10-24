import sqlite3

from src.models import DBAPIFileHash

TABLES_DDL = (
    """
    CREATE TABLE IF NOT EXISTS file_hashes (
        filepath TEXT PRIMARY KEY,
        filehash TEXT,
        modelid INTEGER,
        modelversionid INTEGER
    );
    """,
    # """
    # # CREATE TABLE IF NOT EXISTS models (
    # #     id INTEGER PRIMARY KEY,
    # #     name TEXT,
    # #     description TEXT,
    # #     type TEXT,
    # #     nsfw INTEGER,
    # #     stats TEXT,
    # #     creator TEXT,
    # #     tags TEXT,
    # #     model_versions TEXT
    # # );
    # # """,
    # """
    # CREATE TABLE IF NOT EXISTS model_versions (
    #     id INTEGER PRIMARY KEY,
    #     name TEXT,
    #     description TEXT,
    #     type TEXT,
    #     nsfw INTEGER,
    #     stats TEXT,
    #     creator TEXT,
    #     tags TEXT,
    #     model_versions TEXT
    # );
    # """,
    # """
    # CREATE TABLE IF NOT EXISTS model_versions_files (
    #     id INTEGER PRIMARY KEY,
    #     name TEXT,
    #     size_kb INTEGER,
    #     format TEXT,
    #     fp TEXT,
    #     size INTEGER,
    #     download_url TEXT
    # );
    # """,
    # """
    # CREATE TABLE IF NOT EXISTS model_versions_file_hashes (
    #     id INTEGER PRIMARY KEY,
    #     hash TEXT
    # );
    # """,
    # """
    # CREATE TABLE IF NOT EXISTS model_versions_file_metadata (
    #     id INTEGER PRIMARY KEY,
    #     format TEXT,
    #     fp TEXT,
    #     size INTEGER
    # );
    # """,
)


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


class DBApi:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(
            self.db_path,
            autocommit=False,
        )
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()
        self.__init_tables()

    def __init_tables(self):
        for ddl in TABLES_DDL:
            self.cursor.execute(ddl)
        self.conn.commit()

    def get_filehashes(self) -> dict[str, DBAPIFileHash]:
        data = self.cursor.execute("SELECT * FROM file_hashes").fetchall()
        return {row["filepath"]: DBAPIFileHash(**row) for row in data}

    def update_data(self, filepath: str, model_id: int, model_version_id: int) -> None:
        self.cursor.execute(
            "UPDATE file_hashes SET modelid = ?, modelversionid = ? WHERE filepath = ?",
            (model_id, model_version_id, filepath),
        )
        self.conn.commit()

    def update_filehash(self, filepath: str, filehash: str) -> None:
        # sqlite insert if not exists
        self.cursor.execute("INSERT OR IGNORE INTO file_hashes (filepath) VALUES (?)", (filepath,))
        self.cursor.execute("UPDATE file_hashes SET filehash = ? WHERE filepath = ?", (filehash, filepath))
        self.conn.commit()

    def remove_filehash(self, filepath: str) -> None:
        self.cursor.execute("DELETE FROM file_hashes WHERE filepath = ?", (filepath,))
        self.conn.commit()
