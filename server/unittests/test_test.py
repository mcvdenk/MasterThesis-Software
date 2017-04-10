from bson import objectid
import unittest
from datetime import datetime
import time

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from test import *
from test_item import *
from flashcard import *

from questionnaire import *
from questionnaire_item import *
from questionnaire_response import *

class TestTest(unittest.TestCase):
    
    def setUp(self):
        self.flashcards = set()
        for i in range(10):
            self.flashcards.add(Flashcard(
                question = "fc_Question_"+str(i),
                answer = "fc_Answer_"+str(i),
                sources = [],
                response_model = ["fc_Response_"+str(i)]
                ))
        self.items = set()
        for i in range(10):
            self.items.add(TestItem(
                question = "itm_Question_"+str(i),
                sources = [],
                response_model = ["itm_Response_"+str(i)]
                ))
        self.test_1 = Test(list(self.flashcards), list(self.items))
        self.test_2 = Test(list(self.flashcards), list(self.items),
            prev_flashcards = [response.flashcard for response in self.test_1.test_flashcard_responses],
            prev_items = [response.item for response in self.test_1.test_item_responses])

    def tearDown(self):
        del self.test_2
        del self.test_1
        del self.flashcards
        del self.items

    def test_pre_flashcards_superset(self):
        self.assertEqual({response.flashcard.question for response in
                self.test_1.test_flashcard_responses}
                .difference({flashcard.question for flashcard in
                self.flashcards}), set())

    def test_pre_items_superset(self):
        self.assertEqual({response.item.question for response in
                self.test_1.test_item_responses}
                .difference({item.question for item in
                self.items}), set())

    def test_post_flashcards_equalset_1(self):
        res_flashcards = self.flashcards.difference(
                {response.flashcard for response in
                    self.test_1.test_flashcard_responses})
        self.assertEqual({response.flashcard.question for response in
                self.test_2.test_flashcard_responses},
                {flashcard.question for flashcard in res_flashcards})

    def test_post_items_equalset_1(self):
        for response in self.test_1.test_item_responses:
            self.items.remove(response.item)
        self.assertEqual({response.item.question for response in
                self.test_2.test_item_responses},
                {item.question for item in self.items})

    def test_append_flashcard(self):
        flashcard = self.test_1.test_flashcard_responses[0].flashcard
        self.test_1.append_flashcard(flashcard, "answer")
        self.assertEqual(self.test_1.test_flashcard_responses[0].answer, "answer")

    def test_append_item(self):
        item = self.test_1.test_item_responses[0].item
        self.test_1.append_item(item, "answer")
        self.assertEqual(self.test_1.test_item_responses[0].answer, "answer")


class TestQuestionnaire(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.pu_items = set()
        self.pu_responses = []
        self.peou_items = set()
        self.peou_responses = []
        for i in range(10):
            pu_item = QuestionnaireItem(
                    usefullness = True,
                    positive_phrasing = "pu_positive_" + str(i),
                    negative_phrasing = "pu_negative_" + str(i)
                    )
            self.pu_items.add(pu_item)
            pu_response_posi = QuestionnaireResponse(
                    questionnaire_item = pu_item,
                    phrasing = True)
            self.pu_responses.append(pu_response_posi)
            pu_response_nega = QuestionnaireResponse(
                    questionnaire_item = pu_item,
                    phrasing = False)
            self.pu_responses.append(pu_response_nega)

            peou_item = QuestionnaireItem(
                    usefullness = False,
                    positive_phrasing = "peou_positive_" + str(i),
                    negative_phrasing = "peou_negative_" + str(i)
                    )
            self.peou_items.add(peou_item)
            peou_response_posi = QuestionnaireResponse(
                    questionnaire_item = peou_item,
                    phrasing = True)
            self.peou_responses.append(peou_response_posi)
            peou_response_nega = QuestionnaireResponse(
                    questionnaire_item = peou_item,
                    phrasing = False)
            self.peou_responses.append(peou_response_nega)

        self.questionnaire = \
                Questionnaire(pu_items = list(self.pu_items),
                        peou_items = list(self.peou_items))

    def tearDown(self):
        del self.questionnaire
        del self.peou_responses
        del self.peou_items
        del self.pu_responses
        del self.pu_items

    def test_completeness(self):
        pu_result = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing} for r in self.pu_responses]
        pu_test = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing} for r in self.questionnaire.perceived_usefulness_items]
        self.assertCountEqual(pu_result, pu_test)
                
        peou_result = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing} for r in self.peou_responses]
        peou_test = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing} for r in self.questionnaire.perceived_ease_of_use_items]
        self.assertCountEqual(peou_result, peou_test)

    def test_disjoint_pairs(self):
        pu = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing}
                for r in self.questionnaire.perceived_usefulness_items]
        self.assertCountEqual(pu[:int(len(pu)/2)],
                [{'item': resp['item'], 'phrasing': not resp['phrasing']} for resp in pu[int(len(pu)/2):]])

        peou = [{'item': r.questionnaire_item.positive_phrasing, 'phrasing': r.phrasing}
                for r in self.questionnaire.perceived_ease_of_use_items]
        self.assertCountEqual(peou[:int(len(peou)/2)],
                [{'item': resp['item'], 'phrasing': not resp['phrasing']} for resp in peou[int(len(peou)/2):]])

    def append_answer(self):
        self.questionnaire.append_answer(self.pu_items[7], True, "Positive pu item 7")
        pu_response = None
        for resp in self.questionnaire.perceived_usefulness_items:
            if resp.questionnaire_item is self.peou_items[7] and resp.phrasing is True:
                pu_response = resp
        self.questionnaire.append_answer(self.peou_items[5], False, "Negative peou item 5")
        for resp in self.questionnaire.perceived_ease_of_use_items:
            if resp.questionnaire_item is self.peou_items[5] and resp.phrasing is False:
                peou_response = resp

        self.assertEqual(pu_response, "Positive pu item 7")
        self.assertEqual(peou_response, "Negative peou item 5")


if __name__ == '__main__':
    unittest.main()
