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
        #Preloading all sources from the different flashcards/-edges (the chapters from Laagland)
        self.concept_map = ConceptMap.objects().first()
        self.SOURCES = []
        self.user = None
        for edge in concept_map.edges:
            if (edge.source not in SOURCES): SOURCES.append(edge.source)
        self.SOURCES.sort()

    def consumer(keyword, data):
        """Pass data to the function corresponding to the provided keyword for the provided user

        :param keyword: the keyword for which function to use
        :type keyword: str
        :param data: the data necessary for executing the function
        :type data: dict(str, str or dict)
        :return: Contains the keyword and data to send over a websocket to a client
        :rtype: dict(str, str or dict)

        .. todo: Implement LEARNED_ITEMS-REQUEST
        """
        msg = {'keyword': "FAILURE", 'data': {}}
        if (keyword == "AUTHENTICATE-REQUEST"): 
            self.user = authenticate(data["name"])
            msg = check_prerequisites()
        elif (keyword == "DESCRIPTIVES-RESPONSE"):
            user.set_descriptives(
                    data['birthdate'],
                    data['gender'],
                    data['code'])
            msg = check_prerequisites()
        elif (keyword == "TEST-RESPONSE"):
            user.append_test(data['flashcard_responses'], data['item_responses'])
            msg = check_prerequisites()
        elif (keyword == "QUESTIONNAIRE-RESPONSE"):
            user.append_questionnaire(
                    data['responses'],
                    data['good'],
                    data['can_be_improved'])
            msg['keyword'] = check_prerequisites()
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
            recent_instance = user.retrieve_recent_instance()
            if recent_instance is not None:
                msg = learning_message(recent_instance)
        user.save(cascade = True)
        return msg

    def authenticate(name):
        """A function to either set self.user to an existing :class:`user.User` or to a new User based on the given name

        :param name: The username
        :type name: str
        """
        self.user = User.objects(name=name)
        if (not User):
            if [True, False][User.objects.count()%2]:
                self.user = FlashmapUser(name = name)
            else:
                self.user = FlashcardUser(name = name)
    
    def check_prerequisites():
        """Checks whether the user still has to fill in forms and returns the appropriate message

        :return: A dict containing the appropriate keyword and data for this user
        :rtype: dict
        """
        msg = {'keyword': "", 'data' : {}}
        if (user.code is None): msg['keyword'] = "DESCRIPTIVES-REQUEST"
        elif (len(user.tests) < 1):
            msg['keyword'] = "TEST-REQUEST"
            msg['data'] = create_test()
        elif (user.succesfull_days > 5):
            if (len(user.tests) < 2):
                msg['keyword'] = "TEST-REQUEST"
                msg['data'] = create_test()
            if (user.questionnaire is None):
                msg['keyword'] = "QUESTIONNAIRE-REQUEST"
                msg['data'] = create_questionnaire()
        else: msg['keyword'] = "AUTHENTICATE-RESPONSE"
        return msg

    def create_test():
        """Creates a test for this user (using user.create_test())

        :return: A dict object fit for sending to the user
        :rtype: dict
        """
        return user.create_test(Flashcard.objects(), TestItem.objects())

    def create_questionnaire():
        """Creates a questionnaire for this user (using user.create_questionnaire())

        :return: A dict object fit for sending to the user
        :rtype: dict
        """
        return user.create_questionnaire(
                QuestionnaireItem.objects(usefull = True),
                QuestionnaireItem.objects(usefull = False)
                )

    def provide_learning():
        """Provides a dict containing relevant information for learning
        
        Provides a dict containing the keyword "NO_MORE_INSTANCES", "READ_SOURCE-REQUEST", or "LEARNING-RESPONSE" and relevant data (the source string for "READ_SOURCE-REQUEST" or either the output of :func:`ConceptMap.to_dict()` with an added 'learning' entry or the output of :func:`Flashcard.to_dict()` for "LEARNING-RESPONSE" with an added condition entry)

        :return: A dict containing 'keyword' and the relevant 'data' described above
        :rtype: dict
        """
        msg = {'keyword': "", 'data': {}}
        instance = user.get_due_instance()
        if instance == None:
            instance = user.add_instance()
        if instance == None:
            msg['keyword'] = "NO_MORE_INSTANCES"
        elif instance.source not in user.sources:
            msg['keyword'] = "READ_SOURCE-REQUEST"
            msg['data'] = {'source': instance.source}
        else:
            msg = learning_message(instance)
        return msg

    def learning_message(instance):
        msg['keyword'] = "LEARNING-RESPONSE" 
        if user.condition is "FLASHMAP":
            cmap = concept_map.get_partial_map(item)
            dmap = cmap.to_dict()
            for i in concept_map.get_siblings(item).append(item):
                for edge in dmap['edges']:
                    if edge['id'] == str(i.id) and user.check_due(i):
                        edge['learning'] = True
                    else:
                        edge['learning'] = False
            msg['data'] = dmap
        elif user.condition is "FLASHCARD":
            msg['data'] = item.to_dict()
        msg['data']['condition'] = user.condition
        return msg


    def add_source(source):
        """Adds a read source to the active user

        :param source: The source to be added
        :type source: string
        """
        users.sources.append(source)

    def validate(responses):
        """Adds responses to certain instances

        :param responses: A list of responses containing an instance id and a boolean correctness value
        :type responses: list(dict)
        """
        for response in responses:
            user.validate(response['id'], response['correct'])

    def provide_learned_items():
        """Provides an overview of all learning

        :return: A partial concept map containing all instances for this user or a message containing progress information
        :rtype: dict
        """
        msg = {'keyword': "LEARNED_ITEMS-RESPONSE", 'data' : {}}
        if user.condition is "FLASHMAP":
            edges = [instance.reference for instance in user.instances]
            nodes = concept_map.find_nodes(edges)
            result_map = ConceptMap(nodes, edges)
            msg['data'] = result_map.to_dict()
        elif user.condition is "FLASHCARD":
            msg["data"] = {"due" : 0, "new": 0, "learning": 0, "learned": 0, "not_seen": 0}
            for flashcard in flashcards:
                seen = False
                for instance in user.instances:
                    if (instance.reference is flashcard):
                        seen = True
                        if (instance.check_due): msg["data"]["due"] += 1
                        if (instance.get_exponent() < 2): msg["data"]["new"] += 1
                        elif (instance.get_exponent() < 6): msg["data"]["learning"] += 1
                        else: msg["data"]["learned"] += 1
                if (not seen): msg["data"]["not_seen"] += 1
        msg['data']['condition'] = user.condition
        return msg
