from omc.core import Resource


class User(Resource):
    def list(self):
        client = self.context['common']['client']
        client.invoke_list('users')