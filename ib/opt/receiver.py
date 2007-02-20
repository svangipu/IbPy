#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" ib.opt.receiver -> defines Receiver class to handle inbound data.

"""
from ib.aux.overloading import overloaded
from ib.opt.message import registry, wrapperMethods


def messageMethod(name, argnames):
    """ messageMethod -> creates method for dispatching messages

    @param name name of method as string
    @param argnames list of method argument names
    @return newly created method (as closure)
    """
    def inner(self, *args):
        params = dict(zip(argnames, args))
        self.dispatch(name, params)
    inner.__name__ = name
    return inner


class ReceiverType(type):
    """ ReceiverType -> metaclass that adds EWrapper methods to Receiver

    This metaclass creates dispatch methods for each method defined by
    EWrapper.
    """
    def __new__(cls, name, bases, namespace):
        for mname, margs in wrapperMethods():
            namespace[mname] = messageMethod(mname, margs)
        return type(name, bases, namespace)


class Receiver(object):
    """ Receiver -> dispatches messages to interested callables

    """
    __metaclass__ = ReceiverType


    def __init__(self, listeners=None, types=None):
        self.listeners = listeners if listeners else {}
        self.types = types if types else registry

    def dispatch(self, name, mapping):
        """ send message to each listener

        @param name method name
        @param mapping values for message instance
        @return None
        """
        try:
            mtype = self.types[name]
            listeners = self.listeners[self.key(mtype)]
        except (KeyError, ):
            pass
        else:
            message = mtype(**mapping)
            for listener in listeners:
                listener(message)

    def register(self, listener, *types):
        """ associate listener with message types created by this Receiver

        @param listener callable to receive messages
        @param *types zero or more message types to associate with listener
        @return None
        """
        for mtype in types:
            key = self.key(mtype)
            listeners = self.listeners.setdefault(key, [])
            if listener not in listeners:
                listeners.append(listener)


    def registerAll(self, listener):
        """ associate listener with all messages created by this Receiver

        @param listener callable to receive messages
        @return None
        """
        self.register(listener, *self.types.values())

    def unregister(self, listener, *types):
        """ disassociate listener with message types created by this Receiver

        @param listener callable to no longer receive messages
        @param *types zero or more message types to disassociate with listener
        @return None
        """
        for mtype in types:
            try:
                listeners = self.listeners[self.key(mtype)]
            except (KeyError, ):
                pass
            else:
                if listener in listeners:
                    listeners.remove(listener)

    def unregisterAll(self, listener):
        """ disassociate listener with all messages created by this Receiver

        @param listener callable to no longer receive messages
        @return None
        """
        self.unregister(listener, *self.types.values())

    @staticmethod
    def key(obj):
        """ lookup key for given object

        @param obj any object
        @return obj name or string representation
        """
        try:
            return obj.__name__
        except (AttributeError, ):
            return str(obj)

    @overloaded
    def error(self, e):
        """ error -> handle an error generated by the reader

        Error message types can't be associated in the default manner
        with this family of methods, so we define these three here
        by hand.

        @param e some error value
        @return None
        """
        self.dispatch('error', dict(errorMsg=e))

    @error.register(object, str)
    def error_0(self, strval):
        """ error -> handle an error given a string value

        @param strval some error value as string
        @return None
        """
        self.dispatch('error', dict(errorMsg=strval))

    @error.register(object, int, int, str)
    def error_1(self, id, errorCode, errorMsg):
        """ error -> handle an error given an id, code and message

        @param id error id
        @param errorCode error code
        @param errorMsg error message
        @return None
        """
        params = dict(id=id, errorCode=errorCode, errorMsg=errorMsg)
        self.dispatch('error', params)
