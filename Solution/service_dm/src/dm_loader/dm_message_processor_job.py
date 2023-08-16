from datetime import datetime
from logging import Logger
from typing import Dict, List

from lib.kafka_connect import KafkaConsumer

from dm_loader.repository import DmRepository, OrderDmBuilder


class DmMessageProcessor:
    
    def __init__(self,
                 consumer: KafkaConsumer,
                 dm: DmRepository,
                 logger: Logger) -> None:
        self._consumer = consumer
        self._producer = producer
        self._repository = dm
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
            builder = OrderDmBuilder(order_dict)

            #Обработать значения builder для  h, l, s для postgresql DWH из самого себя (self)
            self._load_dm(builder)

    ############################################
    #Загрузка хабов в postgesql DWH на слой DDS#
    ############################################
    def _load_dm(self, builder: OrderDmBuilder) -> None:
        #user_category_counters
        self._repository.user_category_counters_insert(builder.user_category_counters())
        #user_product_counters
        self._repository.user_product_counters_insert(builder.user_product_counters())

