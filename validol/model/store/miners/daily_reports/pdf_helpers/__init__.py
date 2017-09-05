from validol.model.store.miners.daily_reports.pdf_helpers.ice import IceFuturesParser, IceOptionsParser
from validol.model.store.miners.daily_reports.pdf_helpers.cme import CmeFuturesParser, CmeOptionsParser


PARSERS_MAP = {parser.NAME: parser for parser in (IceFuturesParser, IceOptionsParser,
                                                  CmeFuturesParser, CmeOptionsParser)}