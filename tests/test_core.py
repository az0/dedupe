import unittest
import random
import sys

import numpy

import dedupe


class RandomPairsTest(unittest.TestCase):
    def test_random_pair(self):
        random.seed(123)

        if sys.version_info < (3, 0):
            target = [(0, 3), (0, 4), (2, 4), (0, 5), (6, 8)]
        else:
            target = [(0, 4), (2, 3), (0, 6), (3, 6), (0, 7)]

        random_pairs = list(dedupe.core.randomPairs(10, 5))
        assert random_pairs == target

        random.seed(123)
        if sys.version_info < (3, 0):
            target = [(265, 3429)]
        else:
            target = [(357, 8322)]

        random_pairs = list(dedupe.core.randomPairs(10**4, 1))
        assert random_pairs == target

        random_pairs = list(dedupe.core.randomPairs(10**10, 1))

    def test_random_pair_match(self):

        # test 3: sample size is greater than product of A and B
        # test 4: check for OverflowError
        tests = ((100, 100, 100, 100), (10, 10, 99, 99),
                 (5, 5, 100, 25), (100000, 20000, 15000, 15000))
        for (n_A, n_B, n_sample, expected_length) in tests:
            ret = dedupe.core.randomPairsMatch(n_A, n_B, n_sample)
            list_ret = list(ret)
            assert len(list_ret) == expected_length
            for (ret_a, ret_b) in list_ret:
                assert ret_a < n_A
                assert ret_a >= 0
                assert ret_b < n_B
                assert ret_b >= 0

        numpy.random.seed(123)
        target = [(6, 7), (9, 3), (9, 9), (1, 8), (8, 4),
                  (5, 8), (8, 7), (9, 8), (9, 7), (4, 8)]

        pairs = list(dedupe.core.randomPairsMatch(10, 10, 10))
        assert pairs == target

        pairs = list(dedupe.core.randomPairsMatch(10, 10, 0))
        assert pairs == []


class ScoreDuplicates(unittest.TestCase):
    def setUp(self):
        random.seed(123)
        empty_set = set([])

        long_string = 'asa;sasdfjasdio;fio;asdnfasdvnvao;asduifvnavjasdfasdfasfasasdfasdfasdfasdfasdfsdfasgnuavpidcvaspdivnaspdivninasduinguipghauipsdfnvaspfighapsdifnasdifnasdpighuignpaguinpgiasidfjasdfjsdofgiongag'  # noqa: E501

        self.records = iter([((long_string, {'name': 'Margret', 'age': '32'}, empty_set),
                              ('2', {'name': 'Marga', 'age': '33'}, empty_set)),
                             (('2', {'name': 'Marga', 'age': '33'}, empty_set),
                              ('3', {'name': 'Maria', 'age': '19'}, empty_set)),
                             (('4', {'name': 'Maria', 'age': '19'}, empty_set),
                              ('5', {'name': 'Monica', 'age': '39'}, empty_set)),
                             (('6', {'name': 'Monica', 'age': '39'}, empty_set),
                              ('7', {'name': 'Mira', 'age': '47'}, empty_set)),
                             (('8', {'name': 'Mira', 'age': '47'}, empty_set),
                              ('9', {'name': 'Mona', 'age': '9'}, empty_set)),
                             ])

        deduper = dedupe.Dedupe([{'field': "name", 'type': 'String'}])
        self.data_model = deduper.data_model
        self.classifier = deduper.classifier
        self.classifier.weights = [-1.0302742719650269]
        self.classifier.bias = 4.76

        score_dtype = [('pairs', '<U192', 2), ('score', 'f4', 1)]

        self.desired_scored_pairs = numpy.array([((long_string, '2'), 0.96),
                                                 (['2', '3'], 0.96),
                                                 (['4', '5'], 0.78),
                                                 (['6', '7'], 0.72),
                                                 (['8', '9'], 0.84)],
                                                dtype=score_dtype)

    def test_score_duplicates(self):
        scores = dedupe.core.scoreDuplicates(self.records,
                                             self.data_model,
                                             self.classifier,
                                             2)

        numpy.testing.assert_equal(scores['pairs'],
                                   self.desired_scored_pairs['pairs'])

        numpy.testing.assert_allclose(scores['score'],
                                      self.desired_scored_pairs['score'], 2)


class FieldDistances(unittest.TestCase):

    def test_exact_comparator(self):
        deduper = dedupe.Dedupe([{'field': 'name',
                                  'type': 'Exact'}
                                 ])

        record_pairs = (({'name': 'Shmoo'}, {'name': 'Shmee'}),
                        ({'name': 'Shmoo'}, {'name': 'Shmoo'}))

        numpy.testing.assert_array_almost_equal(deduper.data_model.distances(record_pairs),
                                                numpy.array([[0.0],
                                                             [1.0]]),
                                                3)

    def test_comparator(self):
        deduper = dedupe.Dedupe([{'field': 'type',
                                  'type': 'Categorical',

                                  'categories': ['a', 'b', 'c']}])

        record_pairs = (({'type': 'a'},
                         {'type': 'b'}),
                        ({'type': 'a'},
                         {'type': 'c'}))

        numpy.testing.assert_array_almost_equal(deduper.data_model.distances(record_pairs),
                                                numpy.array([[0, 0, 1, 0, 0],
                                                             [0, 0, 0, 1, 0]]),
                                                3)

    def test_comparator_interaction(self):
        deduper = dedupe.Dedupe([{'field': 'type',
                                  'variable name': 'type',
                                  'type': 'Categorical',
                                  'categories': ['a', 'b']},
                                 {'type': 'Interaction',
                                  'interaction variables': ['type', 'name']},
                                 {'field': 'name',
                                  'variable name': 'name',
                                  'type': 'Exact'}])

        record_pairs = (({'name': 'steven', 'type': 'a'},
                         {'name': 'steven', 'type': 'b'}),
                        ({'name': 'steven', 'type': 'b'},
                         {'name': 'steven', 'type': 'b'}))

        numpy.testing.assert_array_almost_equal(deduper.data_model.distances(record_pairs),
                                                numpy.array([[0, 1, 1, 0, 1],
                                                             [1, 0, 1, 1, 0]]), 3)


if __name__ == "__main__":
    unittest.main()
