from pylint import checkers
from pylint import interfaces


class SimilarStringChecker(checkers.BaseChecker):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'similar-string-checker'

    msgs = {
        'R48XX': ('Eliminate Use of similar strings for translation'),
    }
    
    
    
