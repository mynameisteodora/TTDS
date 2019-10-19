import xml.etree.ElementTree as ElementTree
from Term import Term
import re
from stemming.porter2 import stem
import math
import pickle

class InvertedIndex:
    """A class for building and holding an inverted index.

    The inverted index is a dictionary of words and additional information about that word -
    the document frequency, the list of document IDs in which we can find the word, and a
    list of positions in the document where the word occurs.

    The positions of the word are counted after stopword removal.
    Tokenising is made with the use of regular expressions and hyphens are treated as separators.
    """

    def __init__(self, input_file, stopword_file='./englishST.txt'):
        """
        index is a dictionary
        key = word
        value = TermInfo object
                {name, number of appearances, postings dictionary}
        """

        self.index = dict()
        self.stopword_file = stopword_file
        self.build_inverted_index(input_file)
        self.all_documents = self.initialise_list_of_docs()
        self.number_of_documents = len(self.all_documents)

    def initialise_list_of_docs(self):
        all_docs = set()
        for word in self.index.keys():
            term = self.index[word]
            for docNo in term.postings.keys():
                all_docs.add(docNo)

        return all_docs

    def preprocess(self, text, document_number):
        """
        text = a long string from a document
        document_number = as extracted from the XML file
        :return: list of tuples = (word, document_number, position)
        """
        words = []

        # [^\w\s]|_ -> match a single character not present in the [\w\s] list
        # \w matches any word character (equal to [a-zA-Z0-9_]
        # \s matches any whitespace character (equal to [\r\n\t\f\v ]
        # 2nd alternative - match underscore
        # so this regex will look for any non-letter, non-digit character and replace it with a space
        text = re.sub(r"[^\w\s]|_", " ", text).split()

        if len(text) > 0:
            # add all the words to a list
            words.extend(text)

        # lowercase
        words = [word.lower() for word in words]

        # remove all english stopwords
        # read all the stopwords into a list
        with open(self.stopword_file) as f:
            stopwords = f.read().split()

        f.close()

        # remove all words that are in the stopwords list
        clean_words = []
        for word in words:
            if word not in stopwords:
                clean_words.append(word)

        # stemming
        stemmed_words = [stem(word) for word in clean_words]

        words_and_positions = list(
            zip(stemmed_words, [document_number] * len(stemmed_words), range(1, len(stemmed_words) + 1)))

        # stemmed_words is now a list of tuples
        # (word, docID, position)
        # where elem = word, docID
        return words_and_positions

    def build_inverted_index(self, input_file):
        """
        :param input_file: original XML file
        :return: dictionary of words and information about them, such as the document frequency and postings
        """

        with open(input_file, 'r') as f:  # Reading file
            xml = f.read()

            xml = '<ROOT>' + xml + '</ROOT>'  # Let's add a root tag

            root = ElementTree.fromstring(xml)
            word_list = []

            # Simple loop through each document
            for doc in root:
                for elem in doc:

                    if elem.tag.lower() == 'docno':
                        document_number = int(elem.text.strip())


                    elif elem.tag.lower() == 'headline':
                        headline = elem.text.strip()

                        # preprocess the headline
                        preprocessed_headline = self.preprocess(headline, document_number)
                        word_list.extend(preprocessed_headline)

                    elif elem.tag.lower() == 'text':
                        text = elem.text.strip()

                        # preprocess the text
                        # this returns a list of tuples
                        # (word, document_number, position)
                        # positions counted after stopword removal
                        preprocessed_text = self.preprocess(text, document_number)
                        word_list.extend(preprocessed_text)

        # sort the word list by word
        # then by document number
        # appearances should already be ordered
        word_list = sorted(word_list)

        # merge into postings list
        for elem in word_list:
            word = elem[0]
            document_number = elem[1]
            position = elem[2]

            new_term = Term(word)

            if word in self.index.keys():
                # the index has seen this word before
                # we update the number of occurrences
                # and the postings list
                term = self.index[word]
                #term.add_appearance()
                term.add_posting(document_number, position)

            else:
                # print("Word not in index!")
                new_term.add_posting(document_number, position)
                self.index[word] = new_term

        # print inverted index
        # for word in self.index.keys():
        #     print(word)
        #     term = self.index[word]
        #     print("Num appearances = " + str(term.document_frequency))
        #     print("\t" + str(term.postings))

        pickle.dump(self, open("index.p", "wb"))

        return self.index

    def print_to_file(self, output_file):

        with open(output_file, 'w+') as f:

            for word in self.index.keys():
                term = self.index[word]
                f.write("{0}:({1}) \n".format(word, term.document_frequency))
                for document_number in term.postings.keys():
                    f.write("\t {0}:({1}) {2} \n".format(document_number, term.term_frequency[document_number],
                                                         ", ".join(str(i) for i in term.postings[document_number])))
        f.close()

    """ 
    Some access functions to make item retrieval easier
    """

    def get_index(self):
        return self.index

    def get_word_postings(self, word):

        if word in self.index.keys():
            return self.index[word].postings
        else:
            return {}

    def get_word_documents(self, word):

        if word in self.index.keys():
            return list(self.index[word].postings.keys())
        else:
            return []

    def get_word_document_keys(self, word):

        if word in self.index.keys():
            return self.index[word].postings.keys()
        else:
            return None

    def get_word_positions_in_document(self, word, document):

        if word in self.index.keys():
            if document in self.index[word].postings.keys():
                return self.index[word].postings[document]

        return []

    def get_word_df(self, word):

        if word in self.index.keys():
            return self.index[word].document_frequency
        else:
            return -1

    def get_word_tf(self, word, document_number):

        if word in self.index.keys():
            if document_number in self.index[word].term_frequency.keys():
                return self.index[word].term_frequency[document_number]

        return -1

    def tfidf_weight_word_document(self, word, document_number):
        if word in self.index.keys():
            if document_number in self.index[word].postings.keys():
                ans = (1 + math.log10(self.get_word_tf(word, document_number))) \
                      * math.log10(self.number_of_documents / self.get_word_df(word))

                return ans
        else:
            return -1
