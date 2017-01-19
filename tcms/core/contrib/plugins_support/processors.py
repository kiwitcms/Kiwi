# -*- coding: utf-8 -*-
import threading

from django.conf import settings
from django.utils.importlib import import_module


class NewThread(threading.Thread):
    def __init__(self, command, args):
        self.command = command
        self.args = args
        super(NewThread, self).__init__()

    def run(self):
        # The actual code we want to run
        return self.command(self.args)


class PushSignalToPlugins(object):
    def __init__(self):
        self.plugins = []

    def import_plugins(self):
        if not hasattr(settings,
                       'SIGNAL_PLUGINS') or not settings.SIGNAL_PLUGINS:
            return

        for p in settings.SIGNAL_PLUGINS:
            self.plugins.append(import_module(p))

    def push(self, model, instance, signal):
        for p in self.plugins:
            NewThread(p.receiver, {'model': model, 'instance': instance,
                                   'signal': signal}).start()


# Create the PushSignalToPlugins instance
pstp = PushSignalToPlugins()
pstp.import_plugins()
