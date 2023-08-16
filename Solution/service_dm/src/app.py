import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from app_config import AppConfig
from dm_loader.dm_message_processor_job import DmMessageProcessor
from dm_loader.repository import DmMigrator, DmRepository

# 
app = Flask(__name__)

# Инициализируем конфиг
config = AppConfig()

# Заводим endpoint для проверки, поднялся ли сервис
# Обратиться к нему можно будет GET-запросом по адресу localhost:5000/health
# Если в ответе будет healthy - сервис поднялся и работает
@app.get('/health')
def hello_world():
    return 'healthy'

#Точка входа - позволяет избежать лишнего срабатывания кода
if __name__ == '__main__':

     # Устанавливаем уровень логгирования в Debug
    app.logger.setLevel(logging.DEBUG)

    # Инициализируем мигратор - он выполнит DDL конструкции для недостающий объектов Слоя DM в DWH
    migrator = DmMigrator(config.pg_warehouse_db())
    migrator.up()

    # Инициализируем процессор сообщений.
    # Пока он пустой. Нужен для того, чтобы потом в нем писать логику обработки сообщений из Kafka.
    proc = DmMessageProcessor(
        config.kafka_consumer(),
        config.kafka_producer(),
        DmRepository(config.pg_warehouse_db()),
        app.logger
    )

    # Запускаем процессор в бэкграунде.
    # BackgroundScheduler будет по расписанию вызывать функцию run нашего обработчика(DmMessageProcessor).
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=proc.run, trigger="interval", seconds=25)
    scheduler.start()
    
    # стартуем Flask-приложение.
    app.run(debug=True, host='0.0.0.0', use_reloader=False)
