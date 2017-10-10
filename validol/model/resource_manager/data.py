from validol.view.utils.utils import showable_df


class Data:
    def __init__(self, df, info):
        self.df = df
        self.info = info
        self.show_df = showable_df(self.df)

    def empty(self):
        return self.df.empty
