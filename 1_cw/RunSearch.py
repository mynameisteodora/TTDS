from InvertedIndex import InvertedIndex
from Term import Term
import re
from stemming.porter2 import stem


class RunSearch:

    def __init__(self, collection):
        self.inverted_index = InvertedIndex(collection)
        self.stopword_file = self.inverted_index.stopword_file

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

        words = phrase.split()

        if len(words) == 1:
            return self.process_word_query(phrase, negated)

        if len(words) > 2:
            return "This needs to be handled by TFIDF"

        for i in range(len(words)):
            words[i] = self.preprocess_word(words[i])

        stop_search = False

        # iterable_keys_word1 = iter(inverted_index_rlv[words[0]].keys())
        # iterable_keys_word2 = iter(inverted_index_rlv[words[1]].keys())
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
                # print("Found occurrence in the same document = " + str(next_doc_word1))
                # compare all the positions in these files
                # and see if you find two that are next to each other
                # these should be lists
                curr_doc_positions_word1 = self.inverted_index.get_word_positions_in_document(word1, next_doc_word1)
                curr_doc_positions_word2 = self.inverted_index.get_word_positions_in_document(word2, next_doc_word2)

                k = 0
                l = 0

                while k < len(curr_doc_positions_word1) and l < len(curr_doc_positions_word2):
                    # print("k = {0}, l = {1}".format(k,l))
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
            return document_list
        else:
            return self.process_not_query(document_list)

    def process_word_query(self, word, negated=False):

        word = self.preprocess_word(word)
        relevant_docs = self.inverted_index.get_word_documents(word)

        if negated == False:
            return relevant_docs
        else:
            return self.process_not_query(relevant_docs)

    def process_not_query(self, list_of_docs):
        # the way we process the NOT queries is
        # we take the relevant docs and return all keys
        # apart from the ones that contain the word/phrase

        relevant_docs = self.inverted_index.all_documents.difference(list_of_docs)

        return sorted(list(relevant_docs))

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

        return sorted(list(relevant_documents))

    def get_proxomity_query_elements(self, query):
        # get the proximity number
        # split between # and ( - this will give us the proximity number
        open_par_sign_idx = query.index('(')
        close_par_sign_idx = query.index(')')
        proximity_number = int(query[1:open_par_sign_idx])

        # get the words inside the paranthesis and treat them as a phrase
        q = query[open_par_sign_idx + 1:close_par_sign_idx]

        return q, proximity_number

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
                return self.process_word_query(original_term)

    def read_queries_from_file(self, query_file):
        with open(query_file, 'r') as f:
            queries = f.read().splitlines()
        f.close()

        for line in queries:
            query = line[4:]

            print(line[:4])
            print(self.read_query(query))

if __name__ == '__main__':
    r = RunSearch('./collections/trec.sample.xml')
    # print(r.inverted_index)
    # r.inverted_index.print_to_file('./index.txt')
    # print(r.all_documents)
    print(r.read_query('#10(income tax)'))
    print(r.read_queries_from_file('./queries.lab2.txt'))

    print("The special query:")
    print(r.read_query('NOT "middle east" AND NOT #10(income, taxes)'))
