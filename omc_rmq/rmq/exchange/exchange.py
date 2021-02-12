import argparse
import json
import sys
import time

from omc_rmq.lib.formater import format_list
from omc.core import Resource
import argparse

from omc.core.decorator import filecache
from omc_rmq.utils import build_admin_params


class Exchange(Resource):
    @filecache(duration=60 * 5, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=False):
        results = []
        results.append(super()._completion(True))
        if not self._get_resource_values():
            # resource haven't filled yet
            client = self.context['common']['client']
            exchanges = json.loads(client.invoke_list('exchanges'))
            results = [(one['name'], "name is %(name)s, type is %(type)s | vhost is %(vhost)s" % one) for one in
                       exchanges]
            results.extend(self._get_completion(results, short_mode=True))

        return '\n'.join(results)

    def list(self):
        client = self.context['common']['client']
        exchanges = client.invoke_list('exchanges')
        format_list(exchanges)

    def delete(self):
        client = self.context['common']['client']
        name = self._get_resource_values()[0]
        client.invoke_delete('exchange', ['name=' + name])

    def declare(self):
        client = self.context['common']['client']
        if not self._have_resource_value():
            raise Exception("no exchange name provided")
        name = self._get_resource_values()[0]
        parser = argparse.ArgumentParser('exchange declare arguments')
        parser.add_argument('--type', nargs='?', default='direct')
        args = parser.parse_args(self._get_params())
        client.invoke_declare('exchange', ['name=' + name, "=".join(['type', args.type])])

    def publish(self):
        client = self.context['common']['client']
        name = self._get_resource_values()[0] if self._have_resource_value() else 'amq.default'
        parser = argparse.ArgumentParser()
        parser.add_argument('--routing-key', nargs='?', help='routing key')
        parser.add_argument('--payload', nargs='?', help='message payload')

        args = parser.parse_args(self._get_params())

        if args.routing_key is None:
            raise Exception("routing-key can't be empty")

        if args.payload is None:
            raise Exception("payload can't be empty")

        params = {
            'exchange': name,
            'routing_key': args.routing_key,
            'payload': args.payload

        }
        client.invoke_publish(build_admin_params(params))

    def listen(self):
        if 'completion' in self._get_params():
            params = self._get_params()[:-1]
            the_completion = ['--queue', '--key', '--ackmode', '--count', '--period']
            if params and params[-1].strip() == '--ackmode':
                the_completion.extend(['ack_requeue_true', 'ack_requeue_false', 'reject_requeue_true', 'reject_requeue_false'])
            self._print_completion(the_completion)
            return

        parser = argparse.ArgumentParser()
        parser.add_argument('--queue', nargs='?', help='queue name', default='_tmp_omc_queue')
        parser.add_argument('--key', nargs='?', help='routing key', default='#')
        parser.add_argument('--ackmode', nargs='?', help='routing key', default='ack_requeue_false')
        parser.add_argument('--count', nargs='?', help='message bulk size', default='1')
        parser.add_argument('--period', nargs='?', help='fetch peroid', default=5)

        args = parser.parse_args(self._get_params())

        queue_name = args.queue
        routing_key = args.key
        exchange_name = self._get_resource_values()[0] if self._have_resource_value() else 'amq.default'

        client = self.context['common']['client']

        try:

            # create temp queue
            client.invoke_declare('queue', ['name=' + queue_name])

            # create binding
            client.invoke_declare('binding', build_admin_params({
                'source': exchange_name,
                'destination': queue_name,
                'routing_key': routing_key
            }))

            while True:
                # fetch message periodically(no amqp support) with ui
                # ['queue=' + queue_name, 'count=' + args.count])
                messages = client.invoke_get(build_admin_params({
                    'queue': queue_name,
                    'count': args.count,
                    'ackmode': args.ackmode
                }))
                if json.loads(messages):
                    format_list(messages)
                time.sleep(args.period)
        except KeyboardInterrupt:
            # delete temp queue and routing key after listen exist
            # purge message
            print('purging message on queue %s' % queue_name)
            client.invoke_purge('queue', ['name=' + queue_name])

            # delete bindings
            print('deleting binding with source %s and destination %s' % (exchange_name, queue_name))
            client.invoke_delete('binding', build_admin_params({
                'source': exchange_name,
                'destination': queue_name,
                'destination_type': 'queue',
                'properties_key': routing_key
            }))

            # delete queue
            print('deleting queue %s' % queue_name)
            client.invoke_delete('queue', ['name=' + queue_name])
            sys.exit(0)
