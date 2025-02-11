import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable
import pandas as pd

type TFLTable = list[list[str]]

type ColumnProcessor = Callable[[pd.DataFrame, TFLTable], pd.DataFrame]
type IndexProcessor = Callable[[pd.DataFrame], pd.DataFrame]
type TFLProcessor = Callable[[TFLTable], TFLTable]


@dataclass
class CellValue:
    """
    Represents a fully-labeled cell of a table after flattening.
    Includes the value and its corresponding dimensional labels.
    """
    value: Any
    dimensions: tuple[str, ...]
    row: int
    col: int


@dataclass
class FlatTable:
    """
    Effectively a list of "cellvalue' objects
    """

    table: list[CellValue]

    def filter(self):
        """filter table"""

    def get_dimension_as_columns(self):
        return [*zip(*[cell.dimensions for cell in self.table])]

    def get_dimension_sets(self):
        return {pos: set(col) for pos, col in enumerate(self.get_dimension_as_columns())}

    def find_degenerate_dimensions(self) -> list[int]:
        """
        """
        degenerate_dimensions = []
        return degenerate_dimensions

# Sample Processors
def explode_tfl_rows_and_columns(tfl:TFLTable) -> TFLTable:
    pass
def remove_summary_rows(tfl:TFLTable) -> TFLTable:
    pass
def forward_fill_column_labels(df: pd.DataFrame, tfl: TFLTable) -> pd.DataFrame:
    pass
def verify_columns_forward_fill(df: pd.DataFrame, tfl: TFLTable) -> pd.DataFrame:
    pass
def index_from_indentation(df: pd.DataFrame) -> pd.DataFrame:
    pass
def forward_fill_index(df: pd.DataFrame) -> pd.DataFrame:
    pass

class TableFlattener:
    TFL_PROCESSORS: list[TFLProcessor] = [
        explode_tfl_rows_and_columns,
        remove_summary_rows,
    ]
    COLUMN_PROCESSORS: list[ColumnProcessor] = [
        forward_fill_column_labels,
        verify_columns_forward_fill,
    ]
    INDEX_PROCESSORS: list[IndexProcessor] = [
        index_from_indentation,
        forward_fill_index,
    ]

    def __init__(self, tfl: TFLTable):
        self.tfl = tfl

    def flatten(self) -> FlatTable:
        """
        Takes a TFL through 3 levels of processing:

        1. Table Processing [TFL]
        2. Column Processing [DataFrame]
        3. Index Processing [DataFrame]

        We then convert the DataFrame back to native python with some cleanup steps
        We then extract any global dimensions that apply to ALL values

        We then create a list of CellValue objects and return a FlatTable
        """

        self.tfl = self.process_tfl()

        df = self.tfl.to_dataframe()
        df = self.process_columns(df)
        df = self.process_indexes(df)

        # Clean Ups
        out = df.to_dict(orient="split")

        # remove the word 'cont.' from dimensions that have row continuations
        index = self.remove_continuations(out["index"])

        # extract any dimensions hiding in the section header/title
        global_dimensions = self.extract_global_dimensions()

        # flatten the table
        flat = []
        # loop through rows and make tuple of cell value + dimensions

        return FlatTable(table=flat)

    def process_columns(self, df) -> pd.DataFrame:
        for processor in self.COLUMN_PROCESSORS:
            df = processor(df, self.tfl)
        return df

    def process_indexes(self, df) -> pd.DataFrame:
        for processor in self.INDEX_PROCESSORS:
            df = processor(df)
        return df

    def process_tfl(self) -> pd.DataFrame:
        for processor in self.TFL_PROCESSORS:
            self.tfl = processor(self.tfl)
        return self.tfl

    def extract_global_dimensions(self) -> tuple:
        """
        Searches peripheral Table data for Lab Test and treatment group

        Should also look for a section (eg. hematology)
        """
        return ()

    @staticmethod
    def remove_continuations(index: list[tuple]) -> list[tuple]:
        """ removes continuations from from a set of labels. eg. 'cont' """
        return [()]


