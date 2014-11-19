.. _environment:

Environment Variables
=====================

TCMS uses environment variables to define the test hardware setup. The
Environment Group is the top level container object, it contains one or
more Properties, each having a range of values. Properties can belong to
more than one group.

+------------+----------------+-------------------------+
| Group      | Property       | Value                   |
+============+================+=========================+
| Desktops   | Architecture   | i386, x86\_64, PPC      |
+------------+----------------+-------------------------+
|            | Memory (MB)    | 512, 1024, 2048, 4096   |
+------------+----------------+-------------------------+

Managing environment groups
---------------------------

A group is the container object in an environment. It allows a Test Plan
to be targeted to a specific set of hardware and hence provides greater
repeatability in testing.

Searching environment groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Environment groups can be searched for by name.

Procedure: Searching environment groups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To search an environment group:

#. From the **ENVIRONMENT** tab, click **Groups**.

   |The Environment menu 1|

#. Enter the search parameters, and then click **Search Environment
   Group**.

   |image90|

Adding a new group
~~~~~~~~~~~~~~~~~~

Adding a group uses the **Edit Group** screen.

Procedure: Adding a new group.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **ENVIRONMENT**.
#. Click **Add New Group**.

   |The Add New Group button|

#. Enter **Group Name**.

   |The Environment Group name screen|

#. In the **Edit Environment Group** screen, perform the following
   actions:

   -  Select **Enabled**.
   -  In the **Available Properties** box, select the property to add,
      and then click **Add**. Repeat this process to add more
      properties. 

   |The Environment Group Edit screen|

#. Click **Save**.

 

.. note::

  To edit existing, or create new properties, click **Edit Properties**.

Editing an environment group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An environment group can only be edited by authenticated users.

Procedure: Edit an environment group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To edit an environment group:

#. Click **ENVIRONMENT**.
#. From the **Actions** column, click **Edit**.

   |The Edit link|

#. Edit the fields as required:

   -  Environment Group Name
   -  Enabled checkbox
   -  Properties list

#. Click **Save**.

Deleting a group
~~~~~~~~~~~~~~~~

Groups can not be deleted. A group that is no longer required must be
disabled.

Procedure: Disabling a group
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To disable a group:

#. From the **ENVIRONMENT** menu, click **Groups**.
#. From the Group list, click **Disable**.

   |The disable button|

   The group name will change to a strike through font.

   |Disabled group|

To re-activate a group, click **Enable**.

Managing environment properties
-------------------------------

Environment properties and their associated values can be used in
multiple environment groups. When creating values ensure that they are
discrete measurable properties. For example, screen resolution should be
'1920x1200' rather than '24 inch widescreen'.

Navigating property management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The **Environment Properties** screen provides the ability to edit,
create, enable, and disable properties.

-  To access the **Properties Management** screen, from the
   **ENVIRONMENT** tab, click **Properties**.

   |The Environment menu 2|

-  To display a property's values, click on the property.

   |The Environment Properties screen|

 

.. note::

  Due to auditing requirements, environment properties and values cannot
  be deleted. To disable unused properties and values, click **Disable**.

Add a property
~~~~~~~~~~~~~~

Procedure: Adding an environment property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To add an environment property:

#. From the **ENVIRONMENT** tab, click **Properties**.
#. Click **Add**.

   |The Add button|

#. Enter the **New Property Name** ensuring that the property name is
   descriptive, and then click **Ok**.
#. Select the new property. The row containing the property will become
   orange.
#. In the **Values** text box, enter the property value. Click **Add
   Value**.

   |The Add Value button|

   The new value is now displayed.

|Property with new value|

Editing a Property
~~~~~~~~~~~~~~~~~~

Procedure: Editing an environment property
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To edit an environment property:

#. From the **ENVIRONMENT** tab, click **Properties**.
#. Renaming:

   -  Click **Rename**.
   -  Enter the **New Property Name**, and then click **Ok**.

#. Edit values:

   -  In the row containing the value, click **Rename**.
   -  Enter the new **Value**, and then click **Ok**.

.. |The Environment menu 1| image:: ../_static/Click_Groups.png
.. |image90| image:: ../_static/Group_Home.png
.. |The Add New Group button| image:: ../_static/Add_New_Group.png
.. |The Environment Group name screen| image:: ../_static/Group_Enter_Name.png
.. |The Environment Group Edit screen| image:: ../_static/Group_Edit_Details.png
.. |The Edit link| image:: ../_static/Click_Edit.png
.. |The disable button| image:: ../_static/Groups_Disable.png
.. |Disabled group| image:: ../_static/Groups_Strikethrough.png
.. |The Environment menu 2| image:: ../_static/Click_Properties.png
.. |The Environment Properties screen| image:: ../_static/Properties_Management.png
.. |The Add button| image:: ../_static/Click_Add.png
.. |The Add Value button| image:: ../_static/New_Values.png
.. |Property with new value| image:: ../_static/New_Value_Added.png
