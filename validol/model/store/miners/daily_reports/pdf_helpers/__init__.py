from validol.model.store.miners.daily_reports.pdf_helpers.ice import IceParser
from validol.model.store.miners.daily_reports.pdf_helpers.cme import CmeParser


PARSERS_MAP = {parser.NAME: parser for parser in (IceParser, CmeParser)}