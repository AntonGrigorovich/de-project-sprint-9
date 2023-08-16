from datetime import datetime
from logging import Logger
from typing import Dict, List

from lib.kafka_connect import KafkaConsumer, KafkaProducer

from dds_loader.repository import DdsRepository, OrderDdsBuilder


class DdsMessageProcessor:
    
    def __init__(self,
                 consumer: KafkaConsumer,
                 producer: KafkaProducer,
                 dds: DdsRepository,
                 logger: Logger) -> None:
        self._consumer = consumer
        self._producer = producer
        self._repository = dds
        self._logger = logger
        self._batch_size = 30


    def run() -> None:
        #Залогировать START
        self._logger.info(f"{datetime.utcnow()}: START")

        for _ in range(self._batch_size):
            #Прочитать сообщение из топика kafka
            msg = self._consumer.consume()
            if not msg:
                #Сообщение - нет данных
                self._logger.info(f"{datetime.utcnow()}: NO messages. Quitting.")
                break
            #Залогировать сообщение - о данных
            self._logger.info(f"{datetime.utcnow()}: {msg}")

            #Создать словарь order_dict из payload - это единственный объект, который создаёт мой stg-service и складвает в топик stg-service-orders
            order_dict = msg['payload']
            #Сбилдить из order_dict классом из dds_repository
            builder = OrderDdsBuilder(order_dict)

            #Обработать значения builder для  h, l, s для postgresql DWH из самого себя (self)
            self._load_hubs(builder)
            self._load_links(builder)
            self._load_sats(builder)

            ###################################
            #Отправить сообщения в топик kafka#
            ###################################
            
            #Сообщение
            dst_msg = {
                #id сообщения
                "object_id": str(builder.h_order().h_order_pk),
                #дата отправки сообщения
                "sent_dttm": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                #имя отправки сообщения
                "object_type": "order_report",
                #Содержимое сообщения
                "payload": {
                    #Получатель заказа
                    user_id: str(builder.h_user().h_user_pk),
                    #id заказа
                    "id": str(builder.h_order().h_order_pk),
                    #Продукт заказа
                    product_id: str(builder.h_product().h_product_pk),
                    product_name: builder.s_product().name,
                    #Категория
                    category_id: str(builder.h_category().h_category_pk),
                    category_name: builder.h_category().category_name,
                    #Продажи
                    order_id: builder.h_order().order_id
            }

            #Залогировать сообщение
            self._logger.info(f"{datetime.utcnow()}: {dst_msg}")
            #Отправить сообщение - продюсер отправляет
            self._producer.produce(dst_msg)
        
        #Залогировать финиш отправки сообщения в kafka топик
        self._logger.info(f"{datetime.utcnow()}: FINISH")


    ############################################
    #Загрузка хабов в postgesql DWH на слой DDS#
    ############################################
    def _load_hubs(self, builder: OrderDdsBuilder) -> None:
        #h_user
        self._repository.h_user_insert(builder.h_user())
        #h_product
        for p in builder.h_product():
            self._repository.h_product_insert(p)
        #h_category
        for c in builder.h_category():
            self._repository.h_category_insert(c)
        #h_restaurant
        self._repository.h_restaurant_insert(builder.h_restaurant())
        #h_order
        self._repository.h_order_insert(builder.h_order())

    #############################################
    #Загрузка линков в postgesql DWH на слой DDS#
    #############################################
    def _load_links(self, builder: OrderDdsBuilder) -> None:
        #l_order_user
        self._repository.l_order_user_insert(builder.l_order_user())
        #l_order_product
        for op_link in builder.l_order_product():
            self._repository.l_order_product_insert(op_link)
        #l_product_restaurant
        for pr_link in builder.l_product_restaurant():
            self._repository.l_product_restaurant_insert(pr_link)
        #l_product_category
        for pc_link in builder.l_product_category():
            self._repository.l_product_category_insert(pc_link)

    ################################################
    #Загрузка сателитов в postgesql DWH на слой DDS#
    ################################################
    def _load_sats(self, builder: OrderDdsBuilder) -> None:
        #s_order_cost
        self._repository.s_order_cost_insert(builder.s_order_cost())
        #s_order_status
        self._repository.s_order_status_insert(builder.s_order_status())
        #s_restaurant_names
        self._repository.s_restaurant_names_insert(builder.s_restaurant_names())
        #s_user_names
        self._repository.s_user_names_insert(builder.s_user_names())

    ################################################
    ################билдер для продуктов############
    ################################################

        for pn in builder.s_product_names():
            self._repository.s_product_names_insert(pn)

    def _format_products(self, builder: OrderDdsBuilder) -> List[Dict]:
        #массив products
        products = []

        p_names = {x.h_product_pk: x.name for x in builder.s_product_names()}

        cat_names = {x.h_category_pk: {"id": str(x.h_category_pk), "name": x.category_name} for x in builder.h_category()}
        prod_cats = {x.h_product_pk: cat_names[x.h_category_pk] for x in builder.l_product_category()}

        for p in builder.h_product():
            msg_prod = {
                "id": str(p.h_product_pk),
                "name": p_names[p.h_product_pk],
                "category": prod_cats[p.h_product_pk]
            }

            products.append(msg_prod)

        return products
