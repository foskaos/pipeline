# Here we lay out the proposed interface for classifying flat tables

from typing import Callable
from abc import ABC, abstractmethod
from flattening import FlatTable, TableFlattener
import pandas as pd

ClassifierFunction = Callable[[set[str]], float]


class ParametricClassifier(ABC):
    """ Base class to provide a customized classification function """

    @staticmethod
    @abstractmethod
    def classifier_patterns(wizards) -> dict:
        pass

    @abstractmethod
    def make_function(self, wizards) -> Callable[[set[str]], float]:
        pass


class VisitClassifier(ParametricClassifier):

    @staticmethod
    def classifier_patterns(wizards) -> dict:
        """
        Scores a dimension as being a visit.

        This one is STRICT because the dimension MUST contain
            baseline
            endpoint

        """
        # dimension must contain these 2
        req_patterns = {
            "baseline": {'pattern': 'visit_1_regex'},
            "endpoint": {'pattern': 'visit_2_regex'},
        }
        return req_patterns

    def make_function(self, wizards) -> Callable[[set[str]], tuple[float, dict]]:
        """ returns a function which uses the pattern set up above"""

        def visit_classifier_function(dimension: set[str]) -> tuple[float, dict]:
            """ Score a dimension as being a visit. 1 or 0 since we have client inputs that full specify this"""
            return 0.0, {}

        return visit_classifier_function


class TreatmentClassifier(ParametricClassifier):

    @staticmethod
    def classifier_patterns(client_response: dict) -> dict:
        """
        Scores a dimension as being a treatment.

        This one is probabilistic because it must contain SOME of the client provided options

        """

        return {'treatment_group': {'pattern': 'treatment_regex'}}

    def make_function(self, client_response: dict) -> Callable[[set[str]], tuple[float, dict]]:
        """ returns a function which uses the pattern set up above"""

        def classifier_function(dimension: set[str]) -> tuple[float, dict]:
            """ Score a dimension as being a treatment group. 1 or 0 since we have client inputs that full specify this"""
            return 0.0, {}

        return classifier_function


def general_dimension_classifier(dimension: set[str]) -> float:
    """
        In general, we need a function for each section of a dimension to classify table dimensions
    """


def llm_classifier(dimension: set[str]) -> float:
    """

        use an llm to classify table dimensions if needed

        provide a parametric prompt eg:

        'Here is a list of labels, from the following categories, which category is this list most likely to be'

    """




class SectionClassifier:
    def __init__(self,
                 classifiers: dict[str, ClassifierFunction],
                 section_index: list[str],
                 section_columns: list[str]) -> None:
        """
        Initializes the ColumnClassifier.
        """
        self.classifiers: dict[str, ClassifierFunction] = classifiers
        self.section_index = section_index
        self.section_columns = section_columns

    def classify_dimensions(self, dimensions: set[str]) -> dict[int, str]:
        """
        Classifies each column in the flat table.

        dimensions are sets  of strings provided by the flat table.

        make a score and determine the best match. Perfect scores are first, conflicting or probablistic matches can be resolved.

        The ouput it a dictionary that maps the dimension's position to its meaning
        """

        return {0: 'treatment', 1: 'visit', 2: 'general'}

    def create_classified_dataframe(self, flattened_table: FlatTable) -> pd.DataFrame:
        """
            create a properly shapped dataframe from a flat table using the classification created above
            and the input shaping.

            At this stage we can check for section constraints as well. eg. do we have the set of dimensions
            we would expect. Do we have some dimensions that introduce ambiguity? report this back the user
            for refinement

        """


        # 1. get classifications (classify_dimensions)

        # 2. construct dataframe with n index levels (n = number of provided classifiers)

        # 3. verify that there is only one column of values -> resolve ambiguity

        # 4. reshape df according to section_index, section_columns

        return pd.DataFrame

tables = [] # list of tables

# sample section usage:
flat_tables = [TableFlattener.flatten(table) for table in tables]

client_responses = {}

treatment_classifier = TreatmentClassifier().make_function(client_responses)
visit_classifier = VisitClassifier().make_function(client_responses)
# Section classifier:

section_classifier = {
    'treatment': treatment_classifier,
    'visit': visit_classifier,
    'general': general_dimension_classifier
}

SECTION_INDEX = ['list of the labels used as an index']
SECTION_COLS = ['list of the labels used as column']

section_classifier = SectionClassifier(section_classifier, SECTION_INDEX, SECTION_COLS)

final_tables = [section_classifier.create_classified_dataframe(tbl) for tbl in flat_tables]


# perform section specific calculation with final_tables.


