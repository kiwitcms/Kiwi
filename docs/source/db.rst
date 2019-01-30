.. _db:

Database Schema
===============

.. note::

    The images in this chapter are generated automatically!
    They are very big so you may want opening each one of them in the browser
    and zooming into details.

    Here we show the most common models and their relations.
    To generate a full model diagram of all models used in Kiwi TCMS execute::

        ./manage.py graph_models --pydot -a -g -o all_models.png

Test Plans model diagram
------------------------

.. graphviz:: testplans.dot

Test Cases model diagram
------------------------

.. graphviz:: testcases.dot

Test Runs model diagram
-----------------------
.. graphviz:: testruns.dot
