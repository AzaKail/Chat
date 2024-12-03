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

    def get_messages(self, queue_name):
        """Получает все сообщения из указанной очереди."""
        messages = []
        try:
            while True:
                method_frame, properties, body = self.channel.basic_get(queue=queue_name, auto_ack=False)
                if not method_frame:
                    break
                data = json.loads(body.decode("utf-8"))
                messages.append(data)

                # Сообщение подтверждается вручную
                self.channel.basic_ack(method_frame.delivery_tag)
        except Exception as e:
            print(f"Ошибка получения сообщений: {e}")
        return messages

    def create_queue(self, queue_name):
        """Создаёт устойчивую очередь."""
        self.channel.queue_declare(
            queue=queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 86400000  # TTL 24 часа (миллисекунды)
            }
        )

    def send_message(self, queue_name, sender, message):
        """Отправляет сообщение в очередь."""
        if not self.channel:
            raise Exception("Канал не установлен")

        data = json.dumps({
            "sender": sender,
            "message": message,
            "timestamp": time.time(),
        })

        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=data,
            properties=pika.BasicProperties(
                delivery_mode=2  # Устойчивое сообщение
            )
        )

