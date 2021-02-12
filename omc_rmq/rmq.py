import os

from omc.core import Resource
import argparse
import json

from omc.core.decorator import filecache
from omc.utils import UrlUtils
from omc_rmq.lib.rabbitmq import Management
from omc.config import settings


class Rmq(Resource):
    def __init__(self, context={}, type='web'):
        super().__init__(context, type)
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--vhost', nargs='?', help='rabbitmq vhost')
        self.parser.add_argument('url', nargs='?', help='rabbitmq connection string', default='')

    def _description(self):
        return "Rabbitmq Management Command Line Tool"

    def _before_sub_resource(self):
        self.context['common'] = {
            'client': Management(self._build_configuration())
        }

    @filecache(duration=60 * 60 * 24, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(False))

        if not self._have_resource_value():
            # list rabbitmq connection instance from config file
            config_file_name = os.path.join(settings.RESOURCE_CONFIG_DIR, self.__class__.__name__.lower() + '.json')
            if (os.path.exists(config_file_name)):
                with open(config_file_name) as f:
                    instances = json.load(f)
                    results.extend(
                        self._get_completion([(key, 'instance=' + key) for key, value in instances.items()], False))

        return "\n".join(results)

    def _build_configuration(self):
        args = self.parser.parse_args(self._get_resource_values())
        config = {}
        if args.url:
            if 'http://' in args.url:
                # connection string: http://guest:guest@localhost:15672
                url_utils = UrlUtils(args.url)
                parsed = url_utils.parse()
                config = {
                    'hostname': parsed.hostname if parsed.hostname else 'localhost',
                    'port': parsed.port if parsed.port else 15672,
                    'username': parsed.username if parsed.username else 'guest',
                    'password': parsed.password if parsed.password else 'guest'
                }
            else:
                # parsed as instance, read from config file

                config_file_name = os.path.join(settings.RESOURCE_CONFIG_DIR, self.__class__.__name__.lower() + '.json')

                with open(config_file_name) as f:
                    instances = json.load(f)
                    if args.url in instances:
                        config = instances[args.url]
                pass
        else:
            # no url provided
            pass

        if args.vhost is not None:
            config['vhost'] = args.vhost
            config['declare_vhost'] = args.vhost
        return config


def publish():
    auth = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1', port=5672))
    channel = connection.channel()

    channel.queue_declare(queue='omc_test')

    channel.basic_publish(exchange='',
                          routing_key='omc_test',
                          body='Hello World!')
    print(" [x] Sent 'Hello World!'")
    connection.close()


def consume():
    auth = pika.PlainCredentials('guest', 'guest')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='127.0.0.1', port=5672))
    channel = connection.channel()

    channel.queue_declare(queue='omc_test')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(on_message_callback=callback,
                          queue='omc_test',
                          auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    import sys

    if 'consume' in sys.argv:
        consume()
    elif 'publish' in sys.argv:
        publish()
