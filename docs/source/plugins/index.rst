Kiwi TCMS plugins
=================

You can design your own plugins which will be automatically
discovered and loaded by Kiwi TCMS. There is an example in
`tcms/telemetry/tests/plugin <https://github.com/kiwitcms/Kiwi/tree/master/tcms/telemetry/tests/plugin>`_
but these are not limited to telemetry! They can be anything!

Your plugin should be packaged as a stand-alone Django application that
can be installed *inside* Kiwi TCMS! This means to produce a pip package
containing your ``views.py``, ``urls.py``, ``templates/``, ``static/``,
etc files which are standard for Django applications.

There are 2 special pieces:

- a ``menu.py`` file defining the ``MENU_ITEMS`` variable.
  The format is the same as ``tcms.settings.common.MENU_ITEMS``
- inside ``setup.py`` you need to define an ``entry_point``::

    setup(
        ...
        entry_points={"kiwitcms.plugins": ["your_plugin_name = your_plugin_module"]},
    )


Kiwi TCMS will auto-discover plugins with the ``kiwitcms.plugins``
entry point and:

- append them to ``INSTALLED_APPS`` so that templates, static files and
  everything else can be discovered. This means models and migrations too;
- append their menu to ``MENU_ITEMS`` under the PLUGINS navigation item
  so that users can access the plugin via the web interface;
- include their URL config in ``urlpatterns``, using the plugin name as the
  URL path for inclusion!

After you have tested your plugin and packaged it as a pip package the only
thing you have to do is install the tarball inside the Docker image!
