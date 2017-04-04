#!/usr/bin/env python

#Import of necessary libraries
import datetime
import time
import random
import math
from mongoengine import *

from user import *
from concept_map import *
from flashcard import *
from questionnaire import *
from test_item import *
from logentry import *

"""
@author: Micha van den Enk
"""

class Consumer():
    """
    This is the class from which the program is controlled. It can be used together with the :mod:`handler` module in order to communicate with an external client over a websocket 

    :cvar concept_map: The concept map object containing references to nodes and edges
    :type concept_map: ConceptMap
    :cvar SOURCES: All of the sources referenced to in the edges of the concept map
    :type SOURCES: list(str)
    :cvar user: The active user
    :type user: User
    """

    def __init__(self):
        connect('flashmap')
        self.concept_map = ConceptMap.objects().first()
        #Preloading all sources from the different flashcards/-edges (the chapters from Laagland)
        self.SOURCES = []
        self.user = None
        for edge in self.concept_map.edges:
            if (edge.source not in SOURCES): SOURCES.append(edge.source)
        self.SOURCES.sort()
        self.required_time = 60*15

    def consumer(self, keyword, data):
        """Pass data to the function corresponding to the provided keyword for the provided user

        :param keyword: the keyword for which function to use
        :type keyword: str
        :param data: the data necessary for executing the function
        :type data: dict(str, str or dict)
        :return: Contains the keyword and data to send over a websocket to a client
        :rtype: dict(str, str or dict)

        .. todo: Implement LEARNED_ITEMS-REQUEST
        """
        assert isinstance(keyword, str)
        assert isinstance(data, dict)
        incoming_msg = LogEntry(keyword = keyword, data = data, user = self.user)
        incoming_msg.save()
        msg = {'keyword': "FAILURE", 'data': {}}
        if (keyword == "AUTHENTICATE-REQUEST"): 
            self.user = authenticate(data["name"])
            msg = check_prerequisites()
        elif (keyword == "DESCRIPTIVES-RESPONSE"):
            self.user.set_descriptives(
                    datself, a['birthdate'],
                    data['gender'],
                    data['code'])
            msg = check_prerequisites()
        elif (keyword == "TEST-RESPONSE"):
            self.user.append_test(data['flashcard_responses'], data['item_responses'])
            msg = check_prerequisites()
        elif (keyword == "QUESTIONNAIRE-RESPONSE"):
            self.user.append_questionnaire(
                    data['responses'],
                    data['good'],
                    data['can_be_improved'])
            msg['keyword'] = "DEBRIEFING"
        elif (keyword == "LEARNED_ITEMS-REQUEST"):
            msg = provide_learned_items()
        elif (keyword == "LEARN-REQUEST"): 
            msg = provide_learning()
        elif (keyword == "READ_SOURCE-RESPONSE"):
            add_source(str(data['source']))
            msg = provide_learning()
        elif (keyword == "VALIDATE"):
            validate(data['responses'])
            msg = provide_learning()
        elif (keyword == "UNDO"): 
            recent_instance = self.user.retrieve_recent_instance()
            if recent_instance is not None:
                msg = learning_message(recent_instance)
        self.user.save(cascade = True)
        outgoing_msg = LogEntry(keyword = msg['keyword'], data = msg['data'], user = self.user)
        outgoing_msg.save()
        msg["succesfull_days"] = user.distinct_succesfull_days()
        return msg

    def authenticate(self, name):
        """A function to either set self.user to an existing :class:`user.User` or to a new User based on the given name

        :param name: The self.username
        :type name: str
        """
        assert  isinstance(name, str)
        self.user = User.objects(name=name)
        if (not User):
            condition = ["FLASHMAP", "FLASHCARD"][User.objects.count()%2]
            self.user = User(name = name, condition = condition)
    
    def check_prerequisites(self):
        """Checks whether the self.user still has to fill in forms and returns the appropriate message

        :return: A dict containing the appropriate keyword and data for this self.user
        :rtype: dict
        """
        msg = {'keyword': "", 'data' : {}}
        if (self.user.code is None): msg['keyword'] = "DESCRIPTIVES-REQUEST"
        elif (len(self.user.tests) < 1):
            msg['keyword'] = "TEST-REQUEST"
            msg['data'] = create_test()
        elif (self.user.succesfull_days > 5):
            if (len(self.user.tests) < 2):
                msg['keyword'] = "TEST-REQUEST"
                msg['data'] = create_test()
            if (self.user.questionnaire is None):
                msg['keyword'] = "QUESTIONNAIRE-REQUEST"
                msg['data'] = create_questionnaire()
        else: msg['keyword'] = "AUTHENTICATE-RESPONSE"
        return msg

    def create_test(self):
        """Creates a test for this self.user (using user.create_test())

        :return: A dict object fit for sending to the self.user
        :rtype: dict
        """
        return self.user.create_test(Flashcard.objects(), TestItem.objects())

    def create_questionnaire(self):
        """Creates a questionnaire for this self.user (using user.create_questionnaire())

        :return: A dict object fit for sending to the self.user
        :rtype: dict
        """
        return self.user.create_questionnaire(
                QuestionnaireItem.objects(usefull = True),
                QuestionnaireItem.objects(usefull = False)
                )

    def provide_learning(self):
        """Provides a dict containing relevant information for learning
        
        Provides a dict containing the keyword "NO_MORE_INSTANCES", "READ_SOURCE-REQUEST", or "LEARNING-RESPONSE" and relevant data (the source string for "READ_SOURCE-REQUEST" or either the output of :func:`ConceptMap.to_dict()` with an added 'learning' entry or the output of :func:`Flashcard.to_dict()` for "LEARNING-RESPONSE" with an added condition entry)

        :return: A dict containing 'keyword' and the relevant 'data' described above
        :rtype: dict
        """
        msg = {'keyword': "", 'data': {}}
        instance = self.user.get_due_instance()
        if instance == None:
            instance = self.user.add_instance()
        if instance == None:
            msg['keyword'] = "NO_MORE_INSTANCES"
        elif instance.source not in self.user.sources:
            if datetime.today() in self.user.source_requests:
                msg['keyword'] = "NO_MORE_INSTANCES"
            else:
                msg['keyword'] = "READ_SOURCE-REQUEST"
                msg['data'] = {'source': instance.source}
        else:
            msg = learning_message(instance)
        if msg['keyword'] is "NO_MORE_INSTANCES" or msg['time_up']:
            s_days = set(self.user.succesfull_days)
            s_days.append(datetime.today())
            self.user.succesfull_days = list(s_days)
        return msg

    def learning_message(self, instance):
        """Generates a learning message for the provided instance

        :param instance: The instance which has to be rehearsed
        :type instance: Instance
        :return: The message with keyword "LEARNING RESPONSE" and data containing the partial concept map or flashcard dict representation
        :rtype: dict
        """
        assert isinstance(instance, Instance)
        msg['keyword'] = "LEARNING-RESPONSE" 
        if self.user.condition is "FLASHMAP":
            cmap = self.concept_map.get_partial_map(item)
            dmap = cmap.to_dict()
            for i in self.concept_map.get_siblings(item).append(item):
                for edge in dmap['edges']:
                    if edge['id'] == str(i.id) and self.user.check_due(i):
                        edge['learning'] = True
                    else:
                        edge['learning'] = False
            msg['data'] = dmap
        elif self.user.condition is "FLASHCARD":
            msg['data'] = item.to_dict()
        msg['condition'] = self.user.condition
        msg['time_up'] = self.user.time_spend_today() > self.required_time
        return msg


    def add_source(self, source):
        """Adds a read source to the active self.user

        :param source: The source to be added
        :type source: string
        """
        assert isinstance(source, str)
        self.users.sources.append(source)

    def validate(self, responses):
        """Adds responses to certain instances

        :param responses: A list of responses containing an instance id and a boolean correctness value
        :type responses: list(dict)
        """
        assert isinstance(responses, list)
        assert all(isinstance(response, dict) for response in responses)
        for response in responses:
            self.user.validate(ObjectId(response['id']), response['correct'])

    def provide_learned_items(self):
        """Provides an overview of all learning

        :return: A partial concept map containing all instances for this self.user or a message containing progress information
        :rtype: dict
        """
        msg = {'keyword': "LEARNED_ITEMS-RESPONSE", 'data' : {}}
        if self.user.condition is "FLASHMAP":
            edges = [instance.reference for instance in self.user.instances]
            nodes = self.concept_map.find_nodes(edges)
            result_map = ConceptMap(nodes, edges)
            msg['data'] = result_map.to_dict()
        elif self.user.condition is "FLASHCARD":
            msg["data"] = {"due" : 0, "new": 0, "learning": 0, "learned": 0, "not_seen": 0}
            for flashcard in flashcards:
                seen = False
                for instance in self.user.instances:
                    if (instance.reference is flashcard):
                        seen = True
                        if (instance.check_due): msg["data"]["due"] += 1
                        if (instance.get_exponent() < 2): msg["data"]["new"] += 1
                        elif (instance.get_exponent() < 6): msg["data"]["learning"] += 1
                        else: msg["data"]["learned"] += 1
                if (not seen): msg["data"]["not_seen"] += 1
        msg['data']['condition'] = self.user.condition
        return msg
