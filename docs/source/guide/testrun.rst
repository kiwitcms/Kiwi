.. _testrun:

Test Runs
=========

This chapter explains how to create, search, edit, execute, and generate
reports for Test Runs in Kiwi TCMS. A Test Run in Kiwi TCMS contains the execution results
of selected test cases against particular product builds and environment.

To view Test Runs you have created or are assigned to you click **Main menu::DASHBOARD**
or alternatively click **Personal menu::My Test Runs**.

Searching for Test Runs
-----------------------

To search for Test Runs:

#. From the **Main menu** click **SEARCH::Search Test Runs**.

   |The Testing menu 2|

#. In the **Search Test Run** screen, enter the required search details.

   |The Search Test Run screen|

#. Click **Search** button and the results will appear.

   |Test Run search results|

.. _creating-testrun:

Creating a Test Run
-------------------

Test Runs are created for a specific Test Plan. Only Test Cases with a
status of **CONFIRMED** can be added to the Test Run. A Test Run can be
assigned to any user in Kiwi TCMS. To create a Test Run:

#. Open a Test Plan and click the **Cases** tab
#. From the **Run** sub-menu click on **Write new run**

   |The New Run button|

#. In the **Create New Test Run** screen, perform the following actions:

   -  Edit the **Summary**.
   -  Select the **Product**.
   -  Select the **Product Version**.
   -  Select the **Build**.
   -  Edit the **Run Manager**.
   -  Edit the **Default Tester**.
   -  If applicable, select the **Set Status Automatically** checkbox.
   -  Enter the **Estimated time**.
   -  Enter any **Notes**.
   -  Select **Environment** property values.

   |The Create New Test Run screen|

#. Test Cases will be shown under the above screen.
#. Click **Remove** action on any Test Cases that are not required for this Test Run.
#. Click **Save** button.

.. note::

    Kiwi TCMS notifies the default tester by email that they have been assigned a
    new Test Run!

Add Test Cases to an existing Test Run
--------------------------------------

To add a Test Case to an existing Test Run:

#. Open the Test Plan containing this Test Case.
#. Select Test Cases you want to add.
#. From **Run** sub-menu click **Add into Run** item.

   |The Add cases to run button|

#. Select the Test Run to which Test Cases will be added.
#. Click **Update** button.

   |The Update button|

.. note::

    Test Cases can be added via the Test Run view as well. While the Test Run is
    opened youmay use the **Cases** sub-menu to add/remove other Test Cases to this Test Run.


Cloning a Test Run
------------------

Test Runs can be cloned for easier creation of testing tasks between team members.
To clone a Test Run:

#. Open the Test Run.
#. Select which Test Case executions (aka test case-runs) to be cloned.
   Use a filter, if required, to help restrict the number of visible
   runs.
#. Click **Clone** button at the top of the page.

   |The Clone button 2|

#. Enter the details for the cloned Test Run. Details are auto-populated from the original.
#. Click **Save** button.

Editing a Test Run
------------------

The Edit function modifies fields in a Test Run.

#. Open the Test Run to be edited, and then click **Edit** button.
#. Edit the fields as required:

   -  Summary
   -  Product
   -  Product version
   -  Manager
   -  Default Tester
   -  Estimated Time
   -  Environment Property values
   -  Notes
   -  Finished

#. Click **Save** button.

Changing the status of a Test Run
---------------------------------

A Test Run's status can be changed from **Running** to **Finished** even
if all Test Cases have not been completed.

If the check box **Set Status Automatically** is selected in the test
run, when all the test cases in the run have a passed, failed or blocked
result the test run's status will be changed to **Finished**.

To change the status of a Test Run:

#. Open the Test Run.
#. Click **Set to Finished**.

   |The Set to finished button|

#. To re-activate a Test Run, click **Set to Running**.

   |The Set to running button|

.. note::

  It is also possible to change the status of a Test Run from the Edit
  Test Run menu.

Deleting a Test Run
-------------------

To delete a Test Run:

#. Open the Test Run to be deleted.
#. Click **Delete** button.
#. Click **Ok** to delete or **Cancel** to return.

   |The Delete confirmation screen.|

.. _executing-testrun:

Executing a Test Run
--------------------

Test Runs can be executed at any time. The user can execute any of the
Test Cases within a run, regardless of the order they appear. Use the
**Comment** field to make notes about a Test Case. All comments will be
displayed when a report is generated for a Test Run.

To execute a Test Run:

#. From the Dashboard or a Test Runs list, click the Test Run to execute. The Test Run
   summary is displayed.  You are able to change Test Case statuses from this page. 

   |The Test Run summary|


#. After executing a Test Case expand its widget, enter a **Comment** and
   select the appropriate **Status** icon.

   |A Test Case|


+-------------+---------------------------------------------------------------------------------------------------------------------------+
| Icon        | Meaning                                                                                                                   |
+=============+===========================================================================================================================+
| |image78|   | Idle - Default value. The Test Case has not been examined.                                                                |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image79|   | Running - Test Case is in progress.                                                                                       |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image80|   | Paused - This status is used to denote a problem with the test case itself that prevents the test from being completed.   |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image81|   | Passed - Test Case met all the expected results.                                                                          |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image82|   | Failed - Test Case did not meet all the expected results, or produced an unhandled exception.                             |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image83|   | Blocked - Test Case has a dependency that has failed.                                                                     |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image84|   | Error - Test environment has problems that prevent Test Case     execution.                                               |
+-------------+---------------------------------------------------------------------------------------------------------------------------+
| |image85|   | Waived - Test Case is not suitable for this run or blocked by other cases.                                                |
+-------------+---------------------------------------------------------------------------------------------------------------------------+

Bulk update of Test Cases
~~~~~~~~~~~~~~~~~~~~~~~~~

Bulk operations include change case-runs status, add/remove bug by entering
bug ID, add comment to case-run.

#. Select the Test Cases to be updated.
#. Click on the sub-menu for the required operation:

    |Test Case-run bulk menu|

.. _generate-testrun-report:

Generating a Test Run report
----------------------------

Kiwi TCMS generates reports for Test Runs, regardless of their state. A
report provides the following information:

-  **Plan details:**

   -  Product 
   -  Product version
   -  Plan
   -  Plan version
   -  Platform
   -  Operating system
   -  Run summary
   -  Run notes
   -  Start date
   -  Stop date.

-  **Test Case details:**

   -  Closed at
   -  ID
   -  Summary
   -  Case ID
   -  Tested by
   -  Group
   -  Status

-  **Summary statistics:**

   -  Total number of Test Cases Run.
   -  Total number of Pending Test Cases.
   -  Test Run completed (%).

-  **Bug List:**

   -  Individual bugs
   -  View all bugs (if bug tracker allows it)

To generate a report for a Test Run:

#. Open the Test Run.
#. From the **Case Status** widget, click **Report**.

   |The Report button|

#. A printer friendly version displays.

.. |The New Run button| image:: ../_static/Click_Write_New_Run.png
.. |The Create New Test Run screen| image:: ../_static/Create_New_Test_Run.png
.. |The Add cases to run button| image:: ../_static/Click_Add_Cases_to_Run.png
.. |The Update button| image:: ../_static/Select_Plan_Click_Update.png
.. |The Testing menu 2| image:: ../_static/Click_Runs.png
.. |The Search Test Run screen| image:: ../_static/Runs_Home.png
.. |Test Run search results| image:: ../_static/Search_Results.png
.. |The Delete confirmation screen.| image:: ../_static/Ok_Delete.png
.. |The Clone button 2| image:: ../_static/Clone_Test_Run.png
.. |The Test Run summary| image:: ../_static/Runs_Details.png
.. |A Test Case| image:: ../_static/Enter_Test_Results.png
.. |image70| image:: ../_static/idle.png
.. |image71| image:: ../_static/running.png
.. |image72| image:: ../_static/paused.png
.. |image73| image:: ../_static/pass.png
.. |image74| image:: ../_static/failed.png
.. |image75| image:: ../_static/blocked.png
.. |image76| image:: ../_static/error.png
.. |image77| image:: ../_static/waived.png
.. |image78| image:: ../_static/idle.png
.. |image79| image:: ../_static/running.png
.. |image80| image:: ../_static/paused.png
.. |image81| image:: ../_static/pass.png
.. |image82| image:: ../_static/failed.png
.. |image83| image:: ../_static/blocked.png
.. |image84| image:: ../_static/error.png
.. |image85| image:: ../_static/waived.png
.. |The Set to finished button| image:: ../_static/Set_To_Finished.png
.. |The Set to running button| image:: ../_static/Set_To_Running.png
.. |The Report button| image:: ../_static/Click_Report.png
.. |Test Case-run bulk menu| image:: ../_static/Test_Run_Bulk_Update_Menu.png
