import re
import os
import math

class Eval:

    def __init__(self, input_path):
        self.input_path = input_path
        # dictionary with key = query, val = (rel_doc, score)
        self.relevant_docs = {}
        self.sys_results = {}

    def read_qrels(self, file_name):

        file_path = self.input_path + '/' + file_name

        with open(file_path, 'r') as f:
            lines = f.read().strip().split('\n')

        f.close()

        for line in lines:
            q_num, relevant_tuples = line.split(':')
            q_num = int(q_num)

            for rel_tup in relevant_tuples.split():

                # TODO make sure there will be no decimals here otherwise you will get many more numbers
                rel_doc, score = re.sub(r'[^0-9]', " ", rel_tup).split()
                rel_doc = int(rel_doc)
                score = int(score)

                if q_num in self.relevant_docs.keys():
                    self.relevant_docs[q_num].append((rel_doc, score))
                else:
                    self.relevant_docs[q_num] = [(rel_doc, score)]

        return self.relevant_docs

    def get_relevant_docs_for_query(self, q_num):
        try:
            q_num = int(q_num)
        except ValueError:
            return []

        if q_num not in self.relevant_docs.keys():
            return []
        return self.relevant_docs[q_num]

    def get_relevant_docs_for_query_no_score(self, q_num):
        rel_docs = self.get_relevant_docs_for_query(q_num)
        ans = []

        for elem in rel_docs:
            ans.append(elem[0])

        return ans

    def read_results(self, sys_file):
        file_path = self.input_path + '/' + sys_file

        with open(file_path, 'r') as f:
            lines = f.read().strip().split('\n')

        f.close()

        results = {}

        for line in lines:
            # query_number 0 doc_number rank_of_doc score 0
            q_num, _, doc_no, doc_rank, score, _ = line.split()
            q_num = int(q_num)
            doc_no = int(doc_no)
            score = float(score)

            # assume ranking is ordered
            if q_num in results.keys():
                results[q_num].append((doc_no, score))
            else:
                results[q_num] = [(doc_no, score)]

        sys_name = sys_file.split('.')[0]

        self.sys_results[sys_name] = results
        return results

    def read_all_results(self):
        # assumes files end with 'results'
        docs = os.listdir(self.input_path)
        for doc in docs:
            name, ext = doc.split('.')

            if ext == 'results':
                self.read_results(doc)

    def get_result_for_query(self, system, q_num):

        if system not in self.sys_results.keys():
            return []
        elif q_num not in self.sys_results[system].keys():
            return []
        else:
            return self.sys_results[system][q_num]

    def get_all_results_for_system(self, system):

        if system not in self.sys_results.keys():
            return []
        else:
            return self.sys_results[system]

    def get_num_queries_for_system(self, system):

        if system not in self.sys_results.keys():
            return 0
        else:
            return max(list(self.sys_results[system].keys()))


    def get_top_k_results_for_query(self, system, q_num, k):
        return self.get_result_for_query(system, q_num)[:k]

    def precision_at_k(self, system, k):

        # precision at k = relevant_documents_found_until_k / k

        if system not in self.sys_results.keys():
            return -1

        else:
            precisions = {}

            for q_num in range(1, self.get_num_queries_for_system(system)+1):
                top_k_results = self.get_top_k_results_for_query(system, q_num, k)

                rel_docs_found = 0
                for result in top_k_results:
                    doc_no = result[0]

                    if doc_no in self.get_relevant_docs_for_query_no_score(q_num):
                        rel_docs_found += 1

                precisions[q_num] = float("%0.3f" % (rel_docs_found / k))

            return precisions

    def recall_at_k(self, system, k):

        if system not in self.sys_results.keys():
            return -1

        else:
            recalls = {}

            for q_num in range(1, self.get_num_queries_for_system(system) + 1):
                top_k_results = self.get_top_k_results_for_query(system, q_num, k)

                rel_docs_found = 0
                for result in top_k_results:
                    doc_no = result[0]

                    if doc_no in self.get_relevant_docs_for_query_no_score(q_num):
                        rel_docs_found += 1

                # TODO keep only 3 decimal points
                recalls[q_num] = float("%0.3f" % (rel_docs_found / len(self.get_relevant_docs_for_query_no_score(q_num))))

            return recalls

    def r_precision(self, system):

        if system not in self.sys_results.keys():
            return -1

        else:

            r_prec = {}

            for q_num in range(1, self.get_num_queries_for_system(system) + 1):
                num_relevant_docs = len(self.get_relevant_docs_for_query_no_score(q_num))
                top_r_results = self.get_top_k_results_for_query(system, q_num, num_relevant_docs)

                rel_docs_found = 0
                for result in top_r_results:
                    doc_no = result[0]

                    if doc_no in self.get_relevant_docs_for_query_no_score(q_num):
                        rel_docs_found += 1
                r_prec[q_num] = float("%0.3f" % (rel_docs_found / num_relevant_docs))

            return r_prec

    def AP(self, system, q_num):

        if system not in self.sys_results.keys():
            return -1

        else:
            r = len(self.get_relevant_docs_for_query_no_score(q_num))
            n = len(self.sys_results[system])

            ap_sum = 0
            for k in range(1, n+1):
                prec = self.precision_at_k(system, k)
                if self.sys_results[system][q_num][k][0] in self.get_relevant_docs_for_query_no_score(q_num):
                    ap_sum += prec[q_num]

            return float("%0.3f" % ((ap_sum / r) * 1.0))

    def MAP(self, system):

        if system not in self.sys_results.keys():
            return -1

        else:
            Q = len(self.relevant_docs.keys())
            map_sum = 0

            for q_num in range(1, Q+1):
                map_sum += self.AP(system, q_num)

        return (map_sum / Q) * 1.0

    def get_doc_score_for_query(self, q_num, doc):
        rel_docs = self.get_relevant_docs_for_query(q_num)

        for elem in rel_docs:
            doc_no = elem[0]
            score = elem[1]

            if doc == doc_no:
                return score

        # if this is not in the relevant documents it should have a score of 0
        return 0

    # - nDCG@10: normalized discount cumulative gain at cutoff 10.
    def DCG_k(self, system, q_num, k):
        first_doc = self.sys_results[system][q_num][0][0]
        #print("rel docs for query = {0}".format(self.get_relevant_docs_for_query(q_num)))
        rel_1 = self.get_doc_score_for_query(q_num, first_doc)

        dcg_sum = 0
        for i in range(2, k):
            doc_at_i = self.sys_results[system][q_num][i-1][0]
            rel_i = self.get_doc_score_for_query(q_num, doc_at_i)
            dcg_sum += (rel_i / math.log2(i))

        return float("%0.3f" % (rel_1 + dcg_sum))

    def ideal_gain_k(self, q_num, k):
        if k > len(self.get_relevant_docs_for_query_no_score(q_num)):
            return 0
        else:
            return self.get_relevant_docs_for_query(q_num)[k-1][1]

    def ideal_DCG_k(self, q_num, k):
        first_doc = self.get_relevant_docs_for_query(q_num)[0][0]
        rel_1 = self.get_doc_score_for_query(q_num, first_doc)

        idcg_sum = 0
        for i in range(2, k):
            if i > len(self.get_relevant_docs_for_query(q_num)):
                rel_i = 0
            else:
                rel_i = self.get_relevant_docs_for_query(q_num)[i-1][1]
            idcg_sum += rel_i / math.log2(i)

        return float("%0.3f" % (rel_1+idcg_sum))

    def n_DCG_k(self, system, q_num, k):
        dcg_k = self.DCG_k(system, q_num, k)
        i_dcg_k = self.ideal_DCG_k(q_num, k)
        #print("ideal dcg at {0} = {1}".format(k, i_dcg_k))
        return float("%0.3f" % (dcg_k / i_dcg_k))




if __name__ == '__main__':
    eval = Eval('./systems')
    eval.read_qrels('qrels.txt')
    eval.read_all_results()

    # print(eval.get_result_for_query('S1', 1))
    #
    # print(eval.get_top_k_results_for_query('S2', 4, 2))
    #
    # print(eval.precision_at_k('S1', 10))
    # print(eval.recall_at_k('S1', 10))
    # print(eval.r_precision('S1'))
    # print(eval.MAP('S1'))
    #
    # print("Ideal gain:")
    # print(eval.ideal_gain_k(1, 30))
    #
    # print("nDCG:")
    # print(eval.n_DCG_k('S1', 1, 4))

    for system in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']:
        with open('./{0}.results'.format(system), 'w') as f:
            print("-" * 80)
            print("Evaluating system {0}".format(system))
            print("-" * 80)

            p10 = eval.precision_at_k(system, 10)
            r50 = eval.recall_at_k(system, 50)
            r_prec = eval.r_precision(system)

            f.write('\tP@10\tR@50\tr-Precision\tAP\tnDCG@10\tnDCG@20\n')

            for q_num in range(1,11):
                ap = eval.AP(system, q_num)
                ndcg10 = eval.n_DCG_k(system, q_num, 10)
                ndcg20 = eval.n_DCG_k(system, q_num, 20)

                print("-" * 80)
                print("Query {0}".format(q_num))
                print("-" * 80)

                print("P@10 = {0}".format(p10[q_num]))
                print("R@50 = {0}".format(r50[q_num]))
                print("R-prec = {0}".format(r_prec[q_num]))
                print("AP = {0}".format(ap))
                print("nDCG@10 = {0}".format(ndcg10))
                print("nDCG@50 = {0}".format(ndcg20))

                f.write('{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\n'.format(q_num, p10[q_num], r50[q_num], r_prec[q_num], ap, ndcg10, ndcg20))