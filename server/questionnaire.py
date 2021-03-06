from mongoengine import *
from questionnaire_response import *
import random

class Questionnaire(EmbeddedDocument):
    """A class representing a stored questionnaire for a user
    
    :cvar perceived_usefulness_items: Responses to the perceived usefulness items from TAM
    :type perceived_usefulness_items: list(QuestionnaireResponse)
    :cvar perceived_ease_of_use_items: Responses to the perceived ease of use item from TAM
    :type perceived_ease_of_use_items: list(QuestionnaireResponse)
    :cvar good: A description of what was good about the software according to the user
    :type good: string
    :cvar can_be_improved: A description of what could be improved according to the user
    :type can_be_improved: string
    """
    
    perceived_usefulness_items  = ListField(EmbeddedDocumentField(QuestionnaireResponse))
    perceived_ease_of_use_items = ListField(EmbeddedDocumentField(QuestionnaireResponse))
    good = StringField()
    can_be_improved = StringField()

    def generate_questionnaire(self, pu_items, peou_items):
        """
        A method to set the questionnaire items based on two sets of items

        :param pu_items: The perceived usefulness items of TAM
        :type pu_items: list(QuestionnaireItem)
        :param pu_items: The perceived ease of use items of TAM
        :type pu_items: list(QuestionnaireItem)
        """
        pu1 = [QuestionnaireResponse(questionnaire_item = item, phrasing = random.choice([True, False])) for item in pu_items]
        pu2 = [QuestionnaireResponse(questionnaire_item = resp.questionnaire_item, phrasing = not resp.phrasing) for resp in pu1]
        peou1 = [QuestionnaireResponse(questionnaire_item = item, phrasing = random.choice([True, False])) for item in peou_items]
        peou2 = [QuestionnaireResponse(questionnaire_item = resp.questionnaire_item, phrasing = not resp.phrasing) for resp in peou1]
        random.shuffle(pu1)
        random.shuffle(pu2)
        random.shuffle(peou1)
        random.shuffle(peou2)
        self.perceived_usefulness_items = pu1 + pu2
        self.perceived_ease_of_use_items = peou1 + peou2

    def append_answer(self, item, phrasing, answer):
        """Appends an answer to an item within the questionnaire

        :param item: The item to which the answer refers
        :type item: QuestionnaireItem
        :param phrasing: Whether the item is positively (True) phrased or negatively (False)
        :type phrasing: bool
        :param answer: The answer to be appended
        :type answer: string
        """
        assert isinstance(item, QuestionnaireItem)
        assert isinstance(phrasing, bool)
        assert isinstance(answer, str)
        if (item.usefulness):
            for r in self.perceived_usefulness_items:
                if r.questionnaire_item is item and i.phrasing is phrasing:
                    r.answer = answer
                    break
        else:
            for r in self.perceived_ease_of_use_items:
                if r.questionnaire_item is item and i.phrasing is phrasing:
                    r.answer = answer
                    break
