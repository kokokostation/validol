import os

__all__ = ["platformsFile", "datesFile", "pricesFile", "patternsFile", "monetaryFile"]

platformsFile = "platforms"
datesFile = "dates"
pricesFolder = "prices"
pricesFile = os.path.join(pricesFolder, "pair_ids")
patternsFile = "patterns"
monetaryFile = "monetary"
parsed = "parsed"
activeIndex = "index"
atomsFile = "atoms"
tablesFile = "tables"