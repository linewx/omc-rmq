import argparse
import json
import sys
import time

from omc.core.decorator import filecache
from omc_rmq.utils import build_admin_params

from omc.common import CompletionMixin
from omc_rmq.lib.formater import format_list
from omc.core import Resource


class Queue(Resource, CompletionMixin):
    @filecache(duration=60 * 5, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(False))

        if not self._have_resource_value():
            # completions for queue name
            client = self.context['common']['client']
            queues = json.loads(client.invoke_list('queues'))
            results = [(one['name'], "auto_delete is %(auto_delete)s | vhost is %(vhost)s" % one) for one in queues]
            results.extend(self._get_completion(results, short_mode=True))
        return '\n'.join(results)

    def list(self):
        client = self.context['common']['client']
        queues = client.invoke_list('queues')
        format_list(queues)

    def get(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--count', nargs="?", help='message count', type=str, default='100')
        args = parser.parse_args(self._get_params())
        client = self.context['common']['client']
        queue_name = self._get_resource_values()[0]
        messages = client.invoke_get(['queue=' + queue_name, 'count=' + args.count])
        format_list(messages)

    def delete(self):
        client = self.context['common']['client']
        queue_name = self._get_resource_values()[0]
        client.invoke_delete('queue', ['name=' + queue_name])

    def declare(self):
        # parser = argparse.ArgumentParser('exchange declare arguments')
        # parser.add_argument('--type', nargs='?', default='direct')

        client = self.context['common']['client']
        name = self._get_resource_values()[0]
        # args = parser.parse_args(self._get_params())

        client.invoke_declare('queue', ['name=' + name])

    def publish(self):
        '''Message will be published to the default exchange(amq.default) with routing key queue_name, routing it to this queue.'''
        client = self.context['common']['client']
        if not self._have_resource_value():
            raise Exception("no queue name provided")
        name = self._get_resource_values()[0]
        parser = argparse.ArgumentParser()
        parser.add_argument('--payload', nargs='?', help='message payload')

        args = parser.parse_args(self._get_params())

        if args.payload is None:
            raise Exception("payload can't be empty")

        params = {
            'exchange': 'amq.default',
            'routing_key': name,
            'payload': args.payload

        }
        client.invoke_publish(build_admin_params(params))

    def purge(self):
        client = self.context['common']['client']
        if not self._have_resource_value():
            raise Exception("no queue name provided")
        name = self._get_resource_values()[0]
        client.invoke_purge('queue', ['name=' + name])

    def listen(self):
        if 'completion' in self._get_params():
            params = self._get_params()[:-1]
            the_completion = ['--ackmode', '--count', '--period']
            if params and params[-1].strip() == '--ackmode':
                the_completion.extend(['ack_requeue_true', 'ack_requeue_false', 'reject_requeue_true', 'reject_requeue_false'])
            self._print_completion(the_completion)
            return

        parser = argparse.ArgumentParser()
        parser.add_argument('--ackmode', nargs='?', help='routing key', default='ack_requeue_false')
        parser.add_argument('--count', nargs='?', help='message bulk size', default='1')
        parser.add_argument('--period', nargs='?', help='fetch peroid', default=5)

        args = parser.parse_args(self._get_params())

        if not self._get_resource_values():
            raise Exception("no queue provided")

        queue_name = self._get_resource_values()[0]

        client = self.context['common']['client']

        try:
            print('star listening message on queue %s, press Ctrl-C to stop' % queue_name)
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
            print('stop listening')
            sys.exit(0)
