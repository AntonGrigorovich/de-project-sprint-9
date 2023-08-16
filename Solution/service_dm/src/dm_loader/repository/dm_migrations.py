from lib.pg import PgConnect
from psycopg import Cursor

#Создание всех DDL объектов
class DmMigrator:
    def __init__(self, db: PgConnect) -> None:
        self._db = db

    def up(self) -> None:

        with self._db.connection() as conn:
            with conn.cursor() as cur:
                self._schema(cur)
                self._user_category_counters_create(cur)
                self._user_product_counters_create(cur)


    def _schema(self, cursor: Cursor) -> None:
        cursor.execute(
            """
                CREATE SCHEMA IF NOT EXISTS dm;
            """
        )

    def _user_category_counters_create(self, cursor: Cursor) -> None:
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS cdm.user_category_counters (
                id int4 NOT NULL,
                category_id uuid NOT NULL,
                category_name varchar NOT NULL,
                order_cnt int4 NOT NULL,
                user_id uuid NOT NULL,
                CONSTRAINT ord_cnt_more_zero CHECK ((order_cnt > 0)),
                CONSTRAINT user_category_counters_pkey PRIMARY KEY (id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ix_cat_user_id ON cdm.user_category_counters USING btree (user_id, category_id);
            """
        )

    def _user_product_counters_create(self, cursor: Cursor) -> None:
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS cdm.user_product_counters (
                id int4 NOT NULL,
                product_id uuid NOT NULL,
                product_name varchar NOT NULL,
                order_cnt int4 NOT NULL,
                user_id uuid NOT NULL,
                CONSTRAINT ord_cnt_more_zero CHECK ((order_cnt > 0)),
                CONSTRAINT user_product_counters_pkey PRIMARY KEY (id)
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ix_user_id ON cdm.user_product_counters USING btree (user_id, product_id);
            """
        )
