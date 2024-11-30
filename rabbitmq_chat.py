import pika
import json
import threading
import time


class RabbitMQChat:
    def __init__(self, host="localhost", username="guest", password="guest"):
        self.connection_params = pika.ConnectionParameters(
            host=host,
            credentials=pika.PlainCredentials(username, password)
        )
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()

    def create_queue(self, queue_name):
        """Создает очередь для чата."""
        self.channel.queue_declare(
            queue=queue_name,
            arguments={
                'x-message-ttl': 86400000  # 24 часа в миллисекундах
            }
        )
        return queue_name

    def send_message(self, queue_name, sender, message):
        """Отправляет сообщение в указанный чат."""
        msg_payload = json.dumps({
            "sender": sender,
            "message": message,
            "timestamp": time.time()
        })

        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=msg_payload,
            properties=pika.BasicProperties(
                delivery_mode=2  # Указывает, что сообщение устойчиво
            )
        )

    def start_consuming(self, queue_name, callback):
        """Начинает потребление сообщений из очереди."""
        def on_message(channel, method, properties, body):
            msg = json.loads(body)
            callback(msg)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=queue_name, on_message_callback=on_message)
        threading.Thread(target=self.channel.start_consuming, daemon=True).start()
