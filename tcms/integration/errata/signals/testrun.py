# -*- coding: utf-8 -*-


def testrun_created_handler(sender, *args, **kwargs):
    """Sending current TestRun newly created"""
    # TODO: Send message to message bus. Topic: testrun.created
    pass


def testrun_progress_handler(sender, *args, **kwargs):
    """Sending the progress of current TestRun"""
    # TODO: Send message to message bus.
    # Topic: testrun.progress, testrun.finished
    pass
