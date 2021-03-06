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
from flashmap_instance import *
from flashcard_instance import *
from response import *

connect("test")

class TestFlashmapInstance(unittest.TestCase):

    def setUp(self):
        self.node_a = Node(label = "Node A")
        self.node_b = Node(label = "Node B")
        self.edge = Edge(label = "Edge", from_node = self.node_a, to_node = self.node_b)
        self.instance = FlashmapInstance(reference = self.edge)

        self.node_a.save()
        self.node_b.save()
        self.edge.save()

    def tearDown(self):
        self.edge.delete()
        self.node_b.delete()
        self.node_a.delete()

        del self.instance
        del self.edge
        del self.node_b
        del self.node_a

    def test_due(self):
        self.assertTrue(self.instance.check_due())

    def test_exponent_0(self):
        self.assertEqual(self.instance.get_exponent(), 0)

    def test_exponent_1(self):
        self.instance.start_response()
        self.instance.finalise_response(False)
        self.assertEqual(self.instance.get_exponent(), 1)

    def test_exponent_2(self):
        self.instance.start_response()
        self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 2)

    def test_exponent_3(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 4)

    def test_exponent_4(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.instance.start_response()
        self.instance.finalise_response(False)
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 4)

    def test_schedule_0(self):
        self.instance.schedule()
        self.assertEqual(self.instance.check_due(), True)

    def test_schedule_1(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.instance.schedule()
        self.assertEqual(self.instance.check_due(), False)
        self.assertAlmostEqual(self.instance.due_date.timestamp(), time.time() + 625, delta = 1)


class TestFlashcardInstance(unittest.TestCase):

    def setUp(self):
        self.node_a = Node(label = "Node A")
        self.node_b = Node(label = "Node B")
        self.edge = Edge(label = "Edge", from_node = self.node_a, to_node = self.node_b)
        self.flashcard = Flashcard(question = "Question", answer = "Answer", sources = [self.edge])
        self.instance = FlashcardInstance(reference = self.flashcard)

        self.node_a.save()
        self.node_b.save()
        self.edge.save()
        self.flashcard.save()

    def tearDown(self):
        self.flashcard.delete()
        self.edge.delete()
        self.node_b.delete()
        self.node_a.delete()
        
        del self.instance
        del self.flashcard
        del self.edge
        del self.node_b
        del self.node_a

    def test_due(self):
        self.assertTrue(self.instance.check_due())

    def test_exponent_0(self):
        self.assertEqual(self.instance.get_exponent(), 0)

    def test_exponent_1(self):
        self.instance.start_response()
        self.instance.finalise_response(False)
        self.assertEqual(self.instance.get_exponent(), 1)

    def test_exponent_2(self):
        self.instance.start_response()
        self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 2)

    def test_exponent_3(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 4)

    def test_exponent_4(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.instance.start_response()
        self.instance.finalise_response(False)
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.assertEqual(self.instance.get_exponent(), 4)

    def test_schedule_0(self):
        self.instance.schedule()
        self.assertEqual(self.instance.check_due(), True)

    def test_schedule_1(self):
        for i in range(3):
            self.instance.start_response()
            self.instance.finalise_response(True)
        self.instance.schedule()
        self.assertEqual(self.instance.check_due(), False)
        self.assertAlmostEqual(self.instance.due_date.timestamp(), time.time() + 625, delta = 1)

if __name__ == '__main__':
    f = open("test_output.txt", "w")
    runner = unittest.TextTestRunner(f)
    unittest.main(testRunner = runner, warnings = "ignore")
    f.close()
