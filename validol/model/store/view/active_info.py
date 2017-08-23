from marshmallow import Schema, fields, post_load, pre_dump


class ActiveInfo:
    def __init__(self, flavor, platform, active, active_flavor=None):
        self.flavor = flavor
        self.platform = platform
        self.active = active
        self.active_flavor = active_flavor


class ActiveInfoSchema(Schema):
    class Meta:
        ordered = True

    flavor = fields.String()
    platform = fields.String()
    active = fields.String()
    active_flavor = fields.String(allow_none=True)

    @pre_dump
    def prepare(self, ai):
        return ActiveInfo(ai.flavor.name(), ai.platform, ai.active, ai.active_flavor)

    @post_load
    def make(self, data):
        from validol.model.store.view.view_flavors import VIEW_FLAVORS_MAP

        return ActiveInfo(VIEW_FLAVORS_MAP[data['flavor']],
                          data['platform'], data['active'], data.get('active_flavor', None))