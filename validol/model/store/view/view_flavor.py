class ViewFlavor:
    def platforms(self, model_launcher):
        raise NotImplementedError

    def actives(self, platform, model_aluncher):
        raise NotImplementedError

    def name(self):
        raise NotImplementedError

    def get_df(self, platform, active, model_launcher):
        raise NotImplementedError