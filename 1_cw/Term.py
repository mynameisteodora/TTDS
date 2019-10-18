import bisect


class Term:
    """ A class for holding term information in an inverted index

    The Term class represents a word in the index. It holds information about
    the document frequency of the term and a dictionary of documents it appeared
    in and the positions in each of those documents.
    """

    def __init__(self, word, document_frequency=1):
        """
        postings: dictionary
        key = document_number
        values = list of positions in the document
        """
        self.word = word
        self.document_frequency = document_frequency
        self.postings = dict()
        self.term_frequency = dict()

    def __eq__(self, other):

        if isinstance(other, Term):
            return self.word == other.word and \
                   self.document_frequency == other.document_frequency and \
                   self.postings == other.postings

        # this is for later when we want to get a string from the index
        elif isinstance(other, str):
            return self.word == other

    def __hash__(self):
        return hash(self)

    # might have to modify a bit later
    def __str__(self):
        print_str = self.word + " : " + str(self.document_frequency)
        return print_str + str(self.postings)

    def add_appearance(self):
        self.document_frequency += 1

    def add_posting(self, document_number, position):

        if document_number in self.postings.keys():
            bisect.insort(self.postings[document_number], position)
            self.term_frequency[document_number] += 1
        else:
            self.postings[document_number] = [position]
            self.term_frequency[document_number] = 1
