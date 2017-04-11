from mongoengine import *
from bson import objectid
import unittest
from datetime import datetime
import time
    
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from edge import *
from node import *
from concept_map import *
from flashcard import *
from test_item import *
from questionnaire_item import *
from user import *

connect("test")

class TestUser(unittest.TestCase):

    def setUp(self):

        self.maxDiff = None

        self.sources = [str(i) for i in range(10)]

        self.nodes = [Node(label = str(i)) for i in range(20)]
        for node in self.nodes:
            node.save()

        self.edges = [Edge(
                label = str(i) + " - " + str(i+1),
                from_node = self.nodes[i],
                to_node = self.nodes[i+1],
                sources = [self.sources[int(i/2)]]
                ) for i in range(19)]
        self.edges.append(Edge(
                label = "crosslink 2 - 7",
                from_node = self.nodes[2],
                to_node = self.nodes[7],
                sources = [self.sources[9]]))
        for edge in self.edges:
            edge.save()

        self.concept_map = ConceptMap(nodes = self.nodes, edges = self.edges)
        self.concept_map.save()

        self.flashcards = [Flashcard(
                question = edge.label + "?",
                answer = edge.label + "!",
                sources = [edge],
                response_model = [edge.label + "!"]
                ) for edge in self.edges]
        for flashcard in self.flashcards:
            flashcard.save() 

        self.test_items = [TestItem(
            question = "itm_question_"+str(i),
            sources = [self.sources[i]],
            response_model = ["itm_response_"+str(i)]
            ) for i in range(10)]
        for item in self.test_items:
            item.save() 
        
        self.pu_items = [QuestionnaireItem(
                usefulness = True,
                positive_phrasing = "pu_positive_" + str(i),
                negative_phrasing = "pu_negative_" + str(i)
                ) for i in range(10)]
        for item in self.pu_items:
            item.save() 

        self.peou_items = [QuestionnaireItem(
                usefulness = False,
                positive_phrasing = "peou_positive_" + str(i),
                negative_phrasing = "peou_negative_" + str(i)
                ) for i in range(10)]
        for item in self.peou_items:
            item.save() 

        self.fc_user = User(name = "flashcard user", condition = "FLASHCARD")
        self.fm_user = User(name = "flashmap user", condition = "FLASHMAP")

    def tearDown(self):
        for document in self.peou_items + self.pu_items + self.test_items + self.flashcards + self.edges + self.nodes:
            document.delete()

        del self.fc_user
        del self.fm_user
        del self.sources
        del self.peou_items
        del self.pu_items
        del self.test_items
        del self.flashcards
        del self.concept_map
        del self.edges
        del self.nodes

    def test_set_descriptives(self):
        self.assertEqual(self.fc_user.name, "flashcard user")
        self.assertEqual(self.fc_user.condition, "FLASHCARD")
        self.fc_user.set_descriptives(datetime(1990, 12, 25), "male", "CODE_FC")
        self.assertEqual(self.fc_user.birthdate, datetime(1990, 12, 25))
        self.assertEqual(self.fc_user.gender, "male")
        self.assertEqual(self.fc_user.code, "CODE_FC")

        self.assertEqual(self.fm_user.name, "flashmap user")
        self.assertEqual(self.fm_user.condition, "FLASHMAP")
        self.fm_user.set_descriptives(datetime(1992, 10, 5), "female", "CODE_FM")
        self.assertEqual(self.fm_user.birthdate, datetime(1992, 10, 5))
        self.assertEqual(self.fm_user.gender, "female")
        self.assertEqual(self.fm_user.code, "CODE_FM")

    def test_create_test(self):
        test_cards = self.flashcards[:10]
        pretest = self.fc_user.create_test(flashcards = test_cards, items = self.test_items)
        posttest = self.fc_user.create_test(flashcards = test_cards, items = self.test_items)

        self.assertCountEqual(pretest['flashcards'] + posttest['flashcards'],
                [flashcard.to_dict() for flashcard in test_cards])
        self.assertCountEqual(pretest['items'] + posttest['items'],
                [item.to_dict() for item in self.test_items])
        

    def test_append_test(self):
        pretest = self.fc_user.create_test(flashcards = self.flashcards, items = self.test_items)
        flashcard_responses = [{
                'flashcard': Flashcard.objects(id=card['id']).first(),
                'answer': card['question']
                } for card in pretest['flashcards']]
        item_responses = [{
                'item': TestItem.objects(id=item['id']).first(),
                'answer': item['question']
                } for item in pretest['items']]
        self.fc_user.append_test(flashcard_responses = flashcard_responses, item_responses = item_responses)

    def test_create_questionnaire(self):
        self.assertCountEqual(self.fc_user.create_questionnaire(
                pu_items = self.pu_items, peou_items = self.peou_items),
                [item.to_dict(False) for item in self.pu_items + self.peou_items] + 
                [item.to_dict(True) for item in self.pu_items + self.peou_items])

    def test_append_questionnaire(self):
        questionnaire = self.fc_user.create_questionnaire(
                pu_items = self.pu_items, peou_items = self.peou_items)
        questionnaire_responses = [{
                'item' : QuestionnaireItem.objects(id=item['id']).first(),
                'phrasing' : item['phrasing'],
                'answer' : item['question']
                } for item in questionnaire]
        self.fc_user.append_questionnaire(questionnaire_responses, "good", "can_be_improved", "test@test.com")
        self.assertEqual(self.fc_user.questionnaire.good, "good")
        self.assertEqual(self.fc_user.questionnaire.can_be_improved, "can_be_improved")
        self.assertEqual(self.fc_user.email, "test@test.com")

    def test_get_due_instance(self):
        pass

    def test_add_new_instance(self):
        pass

    def test_start_response(self):
        pass

    def test_validate(self):
        pass

    def test_get_instance_by_id(self):
        pass

    def retrieve_recent_instance(self):
        pass

    def test_time_spend_today(self):
        pass


if __name__ == '__main__':
    unittest.main()
