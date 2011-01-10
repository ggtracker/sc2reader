from eventParsers import EventParser,EventParser_16561
from detailParsers import DetailParser
from messageParsers import MessageParser
from attributeParsers import AttributeParser


def getDetailParser(build):
    return DetailParser()
    
def getAttributeParser(build):
    return AttributeParser()
    
def getEventParser(build):
    if build >= 16561:
        return EventParser_16561()
    else:
        return EventParser()
    
def getMessageParser(build):
    return MessageParser()