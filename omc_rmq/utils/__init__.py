def build_admin_params(params):
    return ['='.join([k, v]) for k, v in params.items()]
