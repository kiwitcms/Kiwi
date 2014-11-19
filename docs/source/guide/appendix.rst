.. _appendix:

Appendix: Writing a Test Case
=============================

What is a Test Case?
--------------------

A Test Case outlines a set of conditions, or variables, under which the
tester determines whether an application or software system meets the
specifications.

**Test Case details:**

-  The goals of the test.
-  The results the test should produce.
-  The circumstances in which the test should run.
-  How the test should be implemented.

**A sound Test Case is:**

-  **Accurate**: A Test Case assesses the summary points.
-  **Economical**: A Test Case has only the essential steps.
-  **Repeatable**: A Test Case is a controlled experiment. The test
   should produce the same results each time it is executed.
-  **Appropriate**: A Test Case has to be appropriate for the testers
   and the environment. This includes future maintenance and regression
   testing.
-  **Traceable**: The requirements of the Test Case must be outlined.
-  **Self Cleaning**: Returns the test environment to the pre-test
   state.

Components of a Test Case
-------------------------

A Test Case must include:

-  Summary
-  Action
-  Effect
-  Test Data (if required)

**Summary**

The Summary contains the essence of the Test Case including the
functional area and purpose of the test, and goals of the Test Case.

When writing the summary:

-  Use *Verb + Object Phrase* structure.
-  Use sentence case, that is, only the first word of the summary begins
   with a capital letter.
-  Be concise, the summary should be less than 60 characters.
-  Good examples:

   -  Summary: Launch Firefox by icon on the panel.
   -  Summary: Initiate chat from the conversation window.

-  Bad examples:

   -  Summary: Save attachments
   -  Summary: Compose Window -- Add Attach Files -- File Number
   -  Summary: Offline setting
   -  Summary: Send Unsent Messages

**Action**

The Action covers the circumstances in which the test will run and how
the test should be implemented. The first step is to define any
prerequisites for the test. For example, the testing environment, test
data, and the Test Cases. The second is to list the steps a tester must
follow to execute the test.

When writing the action:

-  Use plain English, keep the language simple and specific.
-  Write steps clearly and at a low level. Assume the tester has no
   experience and is executing the tests independently.
-  Keep to less than 15 steps per Test Case. If a Test Case requires
   more than 15 steps it may need to be separated into two or more Test
   Cases.

**Effect**

The Effect covers the results of the test. The Results are the expected
behaviour of the system following verification/validation of any Test
Case. For example, this could include: screen pop-ups, data updates,
display changes, or any other event or transaction on the system that is
expected to occur when the Test Case step is executed.

When writing the effect:

-  Use accurate terms to describe the expected behavior. Do not use
   vague descriptions such as, ‘works fine’, ‘works normally’, or ‘opens
   successfully’.
-  Write effects clearly, using a low level of language. Assume the
   tester has no experience and the effect is the only standard to pass
   or fail a test.
-  Break down the verification according to the steps outlined in
   Action.

Test Case review checklist
--------------------------

A Test Case should be executed by a tester in under 20 minutes. Refer to
the below checklist when reviewing a Test Case.

Does the Test Case have:

-  All the environment setup information
-  All the test data needed for the test
-  A clear and concise summary
-  A prerequisite section
-  Clear actions with less than 15 steps
-  Clear effects
