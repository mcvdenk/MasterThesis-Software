from mongoengine import *
from datetime import datetime

class Session(EmbeddedDocument):
    """A class representing a session the user was logged in

    :cvar start: The time that the user logged in
    :type start: datetime
    :cvar end: The time that the user logged out
    :type end: datetime
    :cvar source_prompted: Whether the user was asked to have read a certain source from SOURCES
    :type source_prompted: boolean
    :cvar browser: The type of browser used to log in
    :type browser: string
    """
    
    start = DateTimeField(default = datetime.now)
    end = DateTimeField()
    source_prompted = BooleanField(default = False)
    browser = StringField()

    def end_session(self):
        """Closes this session"""
        self.end = datetime.now()
