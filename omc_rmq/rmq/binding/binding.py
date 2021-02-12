import json

from omc_rmq.utils import build_admin_params

from omc.common import CompletionMixin
from omc_rmq.lib.formater import format_list
from omc.core import Resource
import argparse


class Binding(Resource, CompletionMixin):
    def __init__(self, context={}, type='web'):
        super().__init__(context, type)
        self.parser = argparse.ArgumentParser("binding arguments parser")
        self.parser.add_argument('--src', nargs='?', type=str, help='binding source')
        self.parser.add_argument('--dest', nargs='?', type=str, help='binding destination')
        self.parser.add_argument('--type', nargs='?', type=str, help='binding destination type', default='queue')
        self.parser.add_argument('--key', nargs='?', type=str, help='binding property key', default='')
        self.parser.add_argument('--force', nargs='?', type=bool, help='force to delete')

    def _default_columns(self):
        client = self.context['common']['client']
        bindings = client.invoke_list('bindings')
        format_list(bindings, ['source', 'destination', 'routing_key'], 'table')

    def list(self):
        client = self.context['common']['client']
        bindings = client.invoke_list('bindings')
        format_list(bindings)

    def delete(self):
        if 'completion' in self._get_params():
            params = self._get_params()[:-1]
            prompts = []
            if not params:
                # no params, omc rmq binding completion
                self.print_completion(['--src', '--dest'])

            elif params[-1].strip() == '--src':
                # list all exchanges
                client = self.context['common']['client']
                exchanges = json.loads(client.invoke_list('exchanges'))
                results = [(one['name'], "name is %(name)s, type is %(type)s | vhost is %(vhost)s" % one) for one in
                           exchanges]
                self._print_completion(results, short_mode=True)

            elif params[-1].strip() == '--dest':
                # list all queues
                client = self.context['common']['client']
                queues = json.loads(client.invoke_list('queues'))
                results = [(one['name'], "auto_delete is %(auto_delete)s | vhost is %(vhost)s" % one) for one in queues]
                self.print_completion(results, short_mode=True)

            elif params[-1].strip() == '--type':
                # list all queues
                self.print_completion(['exchange', 'queue'], short_mode=True)

            else:
                self.print_completion(['--src', '--dest', '--type', '--key'])
            return

        client = self.context['common']['client']

        args = self.parser.parse_args(self._get_action_params())

        if args.src is None and args.dest is None and args.type is None:
            raise Exception("src,dest and type at least one should be provided")

        client = self.context['common']['client']
        bindings = json.loads(client.invoke_list('bindings'))

        results = []
        for one_binding in bindings:
            if args.src:
                if one_binding['source'] != args.src:
                    continue
            if args.dest:
                if one_binding['destination'] != args.dest:
                    continue
            if args.type:
                if one_binding['destination_type'] != args.type:
                    continue
            if args.key:
                if one_binding['properties_key'] != args.key:
                    continue

            results.append(one_binding)

        if len(results) == 0:
            print('no items found')

        if len(results) > 1 and not args.force:

            print('more than 1 item found:')
            print(results)
            print('please narrow the filter conditions.')
            print('or you can use --force to force to delete all the records')
        else:
            for one in results:
                delete_args = build_admin_params({
                    'source': one['source'],
                    'destination': one['destination'],
                    'destination_type': one['destination_type'],
                    'properties_key': one['properties_key']
                })
                client.invoke_delete('binding', delete_args)

    def declare(self):
        if 'completion' in self._get_params():
            params = self._get_params()[:-1]
            prompts = []
            if not params:
                # no params, omc rmq binding completion
                self.print_completion(['--src', '--dest', '--key'])

            elif params[-1].strip() == '--src':
                # list all exchanges
                client = self.context['common']['client']
                exchanges = json.loads(client.invoke_list('exchanges'))
                results = [(one['name'], "name is %(name)s, type is %(type)s | vhost is %(vhost)s" % one) for one in
                           exchanges]
                self._print_completion(results, short_mode=True)

            elif params[-1].strip() == '--dest':
                # list all queues
                client = self.context['common']['client']
                queues = json.loads(client.invoke_list('queues'))
                results = [(one['name'], "auto_delete is %(auto_delete)s | vhost is %(vhost)s" % one) for one in queues]
                self.print_completion(results, short_mode=True)

            else:
                self.print_completion(['--src', '--dest', '--key'])

            return

        parser = argparse.ArgumentParser('exchange declare arguments')
        parser.add_argument('--src', nargs='?', type=str, help='binding source', required=True)
        parser.add_argument('--dest', nargs='?', type=str, help='binding destination', required=True)
        parser.add_argument('--type', nargs='?', type=str, help='binding destination type', default='queue')
        parser.add_argument('--key', nargs='?', type=str, help='binding property key', default='')

        client = self.context['common']['client']
        args = parser.parse_args(self._get_params())

        client.invoke_declare('binding', build_admin_params({
            'source': args.src,
            'destination': args.dest,
            'routing_key': args.key
        }))
