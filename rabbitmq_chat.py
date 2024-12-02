import pika
import json
import threading
import time


class RabbitMQChat:
    def __init__(self, amqp_url):
        try:
            self.connection_params = pika.URLParameters(amqp_url)
            self.connection = pika.BlockingConnection(self.connection_params)
            self.channel = self.connection.channel()
        except Exception as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            self.connection = None
            self.channel = None

    def create_queue(self, queue_name):
        """Создаёт устойчивую очередь."""
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,  # Устойчивая очередь
            arguments={'x-message-ttl': 86400000}  # Время жизни сообщений: 24 часа
        )

    def send_message(self, queue_name, sender, message):
        if self.channel is None:
            raise Exception("Ошибка: Нет соединения с RabbitMQ.")
        message_data = {
            "sender": sender,
            "message": message,
            "timestamp": time.time()
        }
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message_data),
            properties=pika.BasicProperties(delivery_mode=2)
        )

