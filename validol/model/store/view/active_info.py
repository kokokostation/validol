from marshmallow import Schema, fields, post_load, pre_dump


class ActiveInfo:
    def __init__(self, flavor, platform, active, active_flavor=None, price_url=None):
        self.flavor = flavor
        self.platform = platform
        self.active = active
        self.active_flavor = active_flavor
        self.price_url = price_url

    def __str__(self):
        return ActiveInfoSchema().dumps(self).data

    def active_only(self):
        return ActiveInfoActiveOnlySchema().dumps(self).data


class ActiveInfoSchema(Schema):
    class Meta:
        ordered = True

    flavor = fields.String()
    platform = fields.String()
    active = fields.String()
    active_flavor = fields.String(allow_none=True)
    price_url = fields.String(allow_none=True)

    @pre_dump
    def prepare(self, ai):
        return ActiveInfo(ai.flavor.name(), ai.platform, ai.active, ai.active_flavor, ai.price_url)

    @post_load
    def make(self, data):
        from validol.model.store.view.view_flavors import VIEW_FLAVORS_MAP

        return ActiveInfo(VIEW_FLAVORS_MAP[data['flavor']],
                          data['platform'],
                          data['active'],
                          data.get('active_flavor', None),
                          data.get('price_url', None))


class ActiveInfoActiveOnlySchema(ActiveInfoSchema):
    class Meta:
        exclude = ('active_flavor', 'price_url')