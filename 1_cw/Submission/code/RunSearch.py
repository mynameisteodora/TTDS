from InvertedIndex import InvertedIndex
from InvertedIndex import pickle_index
import re
from stemming.porter2 import stem
import operator
from os import path
import pickle


class RunSearch:
    """A class for parsing queries and returning appropriate results"""

    def __init__(self):
        self.inverted_index = None
        self.stopword_file = None

    def create_new_index(self, collection):
        self.inverted_index = InvertedIndex(collection)
        pickle_index(self.inverted_index)
        self.stopword_file = self.inverted_index.stopword_file

    def load_index_from_file(self, pickle_dump):
        self.inverted_index = pickle.load( open(pickle_dump, "rb"))
        self.stopword_file = './englishST.txt'

    def preprocess_word(self, word):

        # eliminate special characters
        word = re.sub(r"[^\w\s]|_", "", word)

        # lowercase
        word = word.lower()

        # stopwords
        # read stopword file
        with open(self.stopword_file) as f:
            stopwords = f.read().split()

        f.close()

        if word in stopwords:
            return ""

        word = stem(word)

        return word

    # now we process the query
    # when we encounter a phrase, we do a phrase search
    # here we receive an unprocessed phrase
    # do we only assume we have two words too?
    def process_phrase_query(self, phrase, prox=1, negated=False):
        words = re.sub(r"[^\w\s]|_", " ", phrase).split()

        if len(words) == 1:
            return self.process_word_query(phrase, negated)

        if len(words) > 2:
            return "This needs to be handled by TFIDF"

        for i in range(len(words)):
            words[i] = self.preprocess_word(words[i])

        stop_search = False

        iterable_keys_word1 = iter(self.inverted_index.get_word_document_keys(words[0]))
        iterable_keys_word2 = iter(self.inverted_index.get_word_document_keys(words[1]))

        document_list = list()

        next_doc_word1 = None
        next_doc_word2 = None

        try:
            next_doc_word1 = next(iterable_keys_word1)
            next_doc_word2 = next(iterable_keys_word2)
        except StopIteration:
            print("One of the words in your query is not in our database!")
            stop_search = True

        while not stop_search:

            word1 = words[0]
            word2 = words[1]

            if next_doc_word1 == next_doc_word2:
                # compare all the positions in these files
                # and see if you find two that are next to each other
                # these should be lists
                curr_doc_positions_word1 = self.inverted_index.get_word_positions_in_document(word1, next_doc_word1)
                curr_doc_positions_word2 = self.inverted_index.get_word_positions_in_document(word2, next_doc_word2)

                k = 0
                l = 0

                while k < len(curr_doc_positions_word1) and l < len(curr_doc_positions_word2):

                    if curr_doc_positions_word1[k] < curr_doc_positions_word2[l]:
                        if abs(curr_doc_positions_word1[k] - curr_doc_positions_word2[l]) <= prox:
                            # we have found a phrase!
                            # return this document
                            document_list.append(next_doc_word1)

                            # set k and l to the length of the postings
                            # once we find one occurrence in the document we add it to the results anyway
                            # so there is no need to check further into the document
                            k = len(curr_doc_positions_word1)
                            l = len(curr_doc_positions_word2)
                        else:
                            # the postings are sorted so we increase k
                            k += 1
                    elif curr_doc_positions_word1[k] > curr_doc_positions_word2[l]:
                        if abs(curr_doc_positions_word1[k] - curr_doc_positions_word2[l]) <= prox:
                            # we have found a phrase!
                            # return this document
                            document_list.append(next_doc_word1)
                            k = len(curr_doc_positions_word1)
                            l = len(curr_doc_positions_word2)
                        else:
                            l += 1
                    else:
                        # if both postings are the same (don't see how this could happen)
                        # increase both k and l
                        k += 1
                        l += 1

                try:
                    # update the document numbers
                    next_doc_word1 = next(iterable_keys_word1)
                    next_doc_word2 = next(iterable_keys_word2)
                except StopIteration:
                    stop_search = True

            elif next_doc_word1 < next_doc_word2:
                try:
                    next_doc_word1 = next(iterable_keys_word1)
                except StopIteration:
                    stop_search = True

            else:
                try:
                    next_doc_word2 = next(iterable_keys_word2)
                except StopIteration:
                    stop_search = True

        if negated == False:
            return list(zip(document_list, [1] * len(document_list)))
        else:
            return self.process_not_query(document_list)

    def process_word_query(self, word, negated=False):

        word = self.preprocess_word(word)
        relevant_docs = self.inverted_index.get_word_documents(word)

        if negated == False:
            return list(zip(relevant_docs, [1] * len(relevant_docs)))
        else:
            return self.process_not_query(relevant_docs)

    def process_not_query(self, list_of_docs):
        # the way we process the NOT queries is
        # we take the relevant docs and return all keys
        # apart from the ones that contain the word/phrase

        relevant_docs = self.inverted_index.all_documents.difference(list_of_docs)

        return list(zip(sorted(list(relevant_docs)), [1] * len(list(relevant_docs))))

    def process_boolean_query(self, term1, operator, term2):
        negated = False

        # term1 and term2 can be phrases or proximity searches too

        # check term1
        if term1[:3] == 'NOT':
            negated = True
            term1 = term1[4:]

        if term1[0] == '"':
            # then this is a phrase query
            documents_term1 = self.process_phrase_query(term1, prox=1, negated=negated)
        elif term1[0] == '#':
            # proximity search
            query, proximity_number = self.get_proxomity_query_elements(term1)
            documents_term1 = self.process_phrase_query(query, prox=proximity_number, negated=negated)
        else:
            # one word query
            documents_term1 = self.process_word_query(term1, negated=negated)

        # check term2
        if term2[:3] == 'NOT':
            negated = True
            term2 = term2[4:]

        if term2[0] == '"':
            # then this is a phrase query
            documents_term2 = self.process_phrase_query(term2, prox=1, negated=negated)
        elif term2[0] == '#':
            # proximity search
            query, proximity_number = self.get_proxomity_query_elements(term2)
            documents_term2 = self.process_phrase_query(query, prox=proximity_number, negated=negated)
        else:
            # one word query
            documents_term2 = self.process_word_query(term2, negated=negated)

        if operator == 'AND':
            relevant_documents = set(documents_term1).intersection(set(documents_term2))

        else:
            # operator is 'OR' so we return the union
            relevant_documents = set(documents_term1).union(set(documents_term2))

        ret_list = sorted(list(relevant_documents))

        return ret_list

    def process_ranked_query(self, query):
        words = query.split()

        for i in range(len(words)):
            words[i] = self.preprocess_word(words[i])

        scores = dict()

        for word in words:
            # fetch postings list for each term
            for document_number in self.inverted_index.get_word_documents(word):

                if document_number in scores.keys():
                    scores[document_number] += self.inverted_index.tfidf_weight_word_document(word, document_number)
                else:
                    scores[document_number] = self.inverted_index.tfidf_weight_word_document(word, document_number)

        sorted_scores = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)

        return sorted_scores

    def get_proxomity_query_elements(self, query):
        # get the proximity number
        # split between # and ( - this will give us the proximity number
        open_par_sign_idx = query.index('(')
        close_par_sign_idx = query.index(')')
        proximity_number = int(query[1:open_par_sign_idx])

        # get the words inside the paranthesis and treat them as a phrase
        q = query[open_par_sign_idx + 1:close_par_sign_idx]

        return q, proximity_number

    def read_ranked_query(self, query):
        return self.process_ranked_query(query)

    # Finally, we build a reader that decides what to do with the queries
    def read_query(self, query):
        """
        Reads a query and decides whether it is:
            1. A boolean query (AND, OR)
            2. A phrase search ("income tax")
            3. A proximity search(#10(income, tax))
            4. A free one-word search
            4. A ranked IR based of TFIDF
        """
        # first we split by AND/OR
        q = re.split(" +(AND|OR) +", query)
        negated = False

        if len(q) > 1:
            term1 = q[0]
            operator = q[1]
            term2 = q[2]

            if operator not in ['AND', 'OR']:
                print("Query {0} is ill-formed!".format(query))
                return

            return self.process_boolean_query(term1, operator, term2)

        else:
            original_term = q[0]
            if original_term[:3] == 'NOT':
                negated = True
                original_term = original_term[4:]

            if original_term[0] == '"':
                return self.process_phrase_query(original_term, prox=1, negated=negated)

            elif original_term[0] == '#':
                query, proximity_number = self.get_proxomity_query_elements(original_term)
                return self.process_phrase_query(query, proximity_number, negated)

            else:

                # this can either be a word query
                words = original_term.split()

                if len(words) == 1:
                    return self.process_word_query(original_term)

                else:
                    # this is a free word search
                    return self.process_ranked_query(original_term)

    def read_queries_from_file(self, query_file, output_file):
        with open(query_file, 'r') as f:
            queries = f.read().splitlines()
        f.close()

        with open(output_file, 'w+') as f:
            for line in queries:
                if line[1] != ' ':
                    # two-number query
                    query_number = line[0:2]
                    query = line[3:]
                else:
                    query_number = line[0]
                    query = line[2:]

                # query result should return
                # list of (docNo, score)
                # if query was anything but ranked, score = 1
                query_results = self.read_query(query)
                i = 0
                for result in query_results:
                    if i < 1000:
                        if isinstance(result[1], int):
                            f.write("{0} 0 {1} 0 {2} 0\n".format(query_number, result[0], result[1]))
                        else:
                            r = str("{:0.4f}".format(result[1]))
                            f.write("{0} 0 {1} 0 {2} 0\n".format(query_number, result[0], r))
                        i += 1
                    else:
                        break

        f.close()


if __name__ == '__main__':

    print("*"*100)
    print("\t\t\t Hello! Welcome to your new search engine!")
    print("*" * 100)

    print("\nYou can read the README file to learn how to use me.")

    r = RunSearch()

    load_or_create = input("Would you like to load an existing index [L], create a new index from a collection ["
                           "C] or load the default index[D]?\n[L]/[C]/[D]: ")

    while load_or_create.lower() not in ['c', 'l', 'd']:
        print("\nNot a valid option, try again!\n")
        load_or_create = input("Would you like to load an existing index [L], create a new index from a collection ["
                           "C] or load the default index[D]?\n[L]/[C]/[D]: ")

    if load_or_create.lower() == 'c':
        collection_path = input("\nPlease enter the path to the collection you want to use to build the index\nPath: ")

        while not path.exists(collection_path):
            print("\nFile doesn't exist, try again!\n")
            collection_path = input("\nPlease enter the path to the collection you want to use to build the "
                                    "index\nPath: ")

        index_print_output_path = input("\nWhere do you want to save your index?\nPath: ")

        print("\nCalculating index...")
        r.create_new_index(collection_path)
        r.inverted_index.print_to_file(index_print_output_path)
        print("Inverted index completed! You can find it here: {0}".format(index_print_output_path))
    elif load_or_create.lower() == 'l':
        import_path = input("\nPlease enter the path to the stored index\nPath: ")

        while not path.exists(import_path):
            print("\nFile doesn't exist, try again!\n")
            import_path = input("\nPlease enter the path to the stored index (pickle format)\nPath: ")

        r.load_index_from_file(import_path)
        print("Index loaded!")
    elif load_or_create.lower() == 'd':
        r.load_index_from_file('./inverted_index_pickle.p')

    loop = True
    while loop:
        query_type = input("\n\nDo you want to input queries manually [M] or read them from a file [F]?\n[M]/[F]: ")

        while query_type.lower() not in ['m', 'f']:
            print("\nNot a valid option, try again!\n")
            query_type = input("\nDo you want to input queries manually [M] or read them from a file [F]?\n[M]/[F]: ")

        if query_type.lower() == 'm':
            query = input("\nPlease input your query:\n")

            print("\n\nSearch result (first 1000 matching documents):")

            query_results = r.read_query(query)
            i = 0
            for result in query_results:
                if i < 1000:
                    if isinstance(result[1], int):
                        print("{0} 0 {1} 0 {2} 0".format(1, result[0], result[1]))
                    else:
                        res = str("{:0.4f}".format(result[1]))
                        print("{0} 0 {1} 0 {2} 0\n".format(1, result[0], res))
                    i += 1

        elif query_type.lower() == 'f':
            query_file_path = input("\nPlease enter the query file path:\nPath: ")

            while not path.exists(query_file_path):
                print("\nFile doesn't exist, try again!\n")
                query_file_path = input("\nPlease enter the query file path:\nPath: ")

            output_file_path = input("\nWhere do you want to save the results?\nPath: ")

            r.read_queries_from_file(query_file_path, output_file_path)

        q = input("\n\n\nDo you want to perform another search? [Y]/[N]\n")

        while q.lower() not in ['y', 'n']:
            print("\nNot a valid option, try again!\n")
            q = input("\nDo you want to perform another search? [Y]/[N]\n")

        if q.lower() == 'y':
            loop = True
        elif q.lower() == 'n':
            print("*" * 100)
            print("\t\t\tThank you for searching with me! Goodbye =)")
            print("*" * 100)
            loop = False
