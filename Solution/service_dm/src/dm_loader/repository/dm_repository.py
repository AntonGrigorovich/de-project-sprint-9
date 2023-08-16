import uuid
from datetime import datetime
from typing import Any, Dict, List

from lib.pg import PgConnect
from pydantic import BaseModel

#########################################################
############## Тут классы объектов DM ##################
#########################################################


class user_category_counters(BaseModel):
    id: int4
    category_id: uuid.UUID
    category_name: str
    order_cnt: int4
    user_id: uuid.UUID

class user_product_counters(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    order_cnt: int4
    user_id: uuid.UUID


#############################################################################################################
############ Тут OrderDdsBuilder, который обрабатывает данные в dds_message_processor_job  ##################
#############################################################################################################

    def user_category_counters(self) -> dm_user_category_counters:
        return user_category_counters(
            id = order_id,
            category_name = category_name,
            h_user_pk=self._uuid(user_id),
            order_cnt=1, 
            user_id = user_id
        )

    def user_product_counters(self) -> dm_user_product_counters:
        return user_category_counters(
            id = order_id,
            product_id = product_id,
            product_name=product_name,
            order_cnt=1, 
            user_id = user_id
        )


###################################################################################################################
############ Тут DmRepository, который обрабатывает данные для DWH в dm_message_processor_job  ####################
###################################################################################################################

class DmRepository:
    def __init__(self, db: PgConnect) -> None:
        self._db = db

    def dm_user_category_counters_insert(self, ucc: dm_user_category_counters) -> None:
        with self._db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                        INSERT INTO dm.user_category_counters(
                            id,
                            category_name,
                            h_user_pk,
                            order_cnt,
                            user_id
                        )
                        VALUES(
                            %(id)s,
                            %(category_name)s,
                            %(h_user_pk)s,
                            %(order_cnt)s,
                            %(user_id)s
                        )
                        ON CONFLICT (id) DO NOTHING;
                    """,
                    {
                        'id': ucc.id,
                        'category_name': ucc.category_name,
                        'h_user_pk': ucc.h_user_pk,
                        'order_cnt': ucc.order_cnt,
                        'user_id': ucc.user_id,
                        'order_cnt': ucc.order_cnt
                    }
                )

    def dm_user_product_counters_insert(self, upc: dm_user_product_counters) -> None:
        with self._db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                        INSERT INTO dm.user_product_counters(
                            id,
                            product_id,
                            product_name,
                            order_cnt,
                            user_id
                        )
                        VALUES(
                            %(id)s,
                            %(product_id)s,
                            %(product_name)s,
                            %(order_cnt)s,
                            %(user_id)s
                        )
                        ON CONFLICT (id) DO NOTHING;
                    """,
                    {
                        'id': upc.id,
                        'product_id': upc.product_id,
                        'h_user_pk': upc.h_user_pk,
                        'product_name': upc.product_name,
                        'order_cnt': upc.order_cnt,
                        'user_id': upc.user_id
                    }
                )