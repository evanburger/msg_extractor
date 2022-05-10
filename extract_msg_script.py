"""This module can be used as a library or script to extract data from msg files and write them to a csv."""
import re # for regular expressions
import csv # for handling csv data
import sys # for getting CLI arguments

from extract_msg import Message as MessageExtractor # for extracting data from msg binary files 


class Message:
    """An object to access and manipulate data from a msg file."""
    # These are the pairs of strings (first and last)
    # that should have the respective data in between them.
    SEARCH_STRINGS: dict = {
        'date': None, # The date is None because it's not held in the body with the other data.
        'comment': ('Comment from .*: ', '\n'),
        'case_number': ('Case Number: ', '('),
        'account': ('Account: ', '\n'),
        'contact': ('Contact: ', '\n'),
    }

    def __init__(self, filepath: str):
        self.extractor: MessageExtractor = MessageExtractor(filepath) # This is the object to access the data.
        self.body: str = self.extractor.body
        self.date: str = self.extractor.date
        self._data: dict[str, str] = None # This field is "private" so that it can be populated by the data() method later.

    @staticmethod
    def extract(start: str, end: str, text: str):
        '''Return the stripped string between start and end strings from the given text.
        extract(' ', '!', 'Hello, World!')
        >>> 'World'
        '''
        start_full: str = re.search(start, text).group()
        start_i: int = text.find(start_full) + len(start_full)
        remaining_str: str = text[start_i:]
        end_i: int = remaining_str.find(end) + start_i
        return text[start_i:end_i].strip()

    @property
    def data(self):
        """Getter for _data"""
        if self._data is None:
            extracted_data: dict = {key: self.extract(value[0], value[1], self.body) \
                    for key, value in self.SEARCH_STRINGS.items() if value is not None}
            extracted_data['date'] = self.extractor.date
            self._data = extracted_data
            return extracted_data
        return self._data


class Dispatcher:
    """An object to process one or more input files and write the data to a given output file.
    It depends on a "processor" which can be any object that can take a filepath as input
    and expose the data in field called '.data'"""
    def __init__(self, processor, output_path):
        self.processor = processor
        self.output_path = output_path
    
    def execute_one(self, filepath: str, writer):
        """Process one file."""
        writer.writerow(self.processor(filepath).data)

    def execute_batch(self, filepaths: list, writer):
        """Process multiple files."""
        for filepath in filepaths:
            self.execute_one(filepath, writer)
    
    def execute(self, filepaths: list):
        """Process one or many files."""
        with open(self.output_path, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=(self.processor.SEARCH_STRINGS.keys()))
            writer.writeheader()
            if len(filepaths) == 1:
                self.execute_one(filepaths[0], writer)
            else:
                self.execute_batch(filepaths, writer)
            

if __name__ == '__main__':
    OUTPUT_FILEPATH: str = 'output.csv'
    filepaths: list = sys.argv[1:]
    dispatcher = Dispatcher(Message, OUTPUT_FILEPATH)
    dispatcher.execute(filepaths)
