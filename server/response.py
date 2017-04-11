from mongoengine import *
from datetime import datetime

class Response(EmbeddedDocument):
    """A class representing a singular response to an :class:`Instance`.

    :cvar start: The moment the parent :class:`Instance` was sent to the client
    :type start: DateTimeField
    :cvar end: The moment the answer from the client was received
    :type end: DateTimeField
    :cvar correct: Whether the answer to the :class:`Instance` was correct (True) or incorrect (False)
    :type correct: BooleanField
    """
    
    start = DateTimeField(default = datetime.now)
    end = DateTimeField()
    correct = BooleanField()
