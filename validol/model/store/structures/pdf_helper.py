from sqlalchemy import Column, String
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import reconstructor
import pandas as pd
import os

from validol.model.store.structures.structure import Structure, Base, JSONCodec
from validol.model.store.view.active_info import ActiveInfoSchema
from validol.model.store.miners.daily_reports.expirations import Expirations
from validol.model.utils import pdf, TempFile


class PdfParser:
    def __init__(self, pdf_helper):
        self.pdf_helper = pdf_helper

    def pages(self, content):
        raise NotImplementedError

    def map_content(self, content):
        return content

    def process_df(self, df):
        raise NotImplementedError

    def read_expirations(self, expirations_file):
        return pd.DataFrame()

    def read_data(self, active_folder):
        return pd.DataFrame()


class Parser(TypeDecorator):
    impl = String

    def process_result_value(self, value, dialect):
        from validol.model.store.miners.daily_reports.pdf_helpers import PARSERS_MAP

        return PARSERS_MAP[value]


class ActiveInfoSchemaModified(ActiveInfoSchema):
    class Meta:
        exclude = ('active_flavor',)


class PdfHelper(Base):
    __tablename__ = 'pdf_helper'

    name = Column(JSONCodec(ActiveInfoSchemaModified()), primary_key=True)
    processor = Column(Parser())
    active_folder = Column(String)
    expirations_file = Column(String)
    other_info = Column(JSONCodec())

    @reconstructor
    def on_load(self):
        self.processor = self.processor(self)

    def initial(self, model_launcher):
        if os.path.isfile(self.expirations_file):
            exps = self.processor.read_expirations(self.expirations_file)
            for key, value in self.other_info['expirations'].items():
                exps[key] = value

            Expirations(model_launcher).write_df(exps)

        if os.path.isdir(self.active_folder):
            return self.processor.read_data(self.active_folder)
        else:
            return pd.DataFrame()

    def parse_file(self, filename, date):
        with open(filename, 'rb') as file:
            return self.parse_content(file.read(), date)

    def parse_content(self, content, date):
        content = self.processor.map_content(content)

        with TempFile() as file:
            file.write(content)

            pages, kwargs = self.processor.pages(content)

            try:
                df = pdf(file.name, pages, kwargs)
            except:
                return pd.DataFrame()

            df = self.processor.process_df(df)

            df['Date'] = date

            return df


class PdfHelpers(Structure):
    def __init__(self, model_launcher):
        Structure.__init__(self, PdfHelper, model_launcher)

    def write_helper(self, ai, info, other_info):
        self.write(PdfHelper(name=ai,
                             processor=info['processor'],
                             active_folder=info['active_folder'],
                             expirations_file=info['expirations_file'],
                             other_info=other_info))
