from jsonmerge.descenders import AnyOfAllOf as CoreAnyOfAllOf,\
    Ref, OneOf
from jsonmerge import Walk, Merger

__all__ = ['Merger']


class AnyOfAllOf(CoreAnyOfAllOf):

    def descend(self, schema):
        # disable error message
        return None


# Update descendenrs
Walk.DESCENDERS = [Ref, OneOf, AnyOfAllOf]
