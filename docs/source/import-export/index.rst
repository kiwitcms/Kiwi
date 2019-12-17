Import-Export functionality
===========================


.. warning::

    Kiwi TCMS **does not** and **will not** support import and
    export functionality to/from Excel, XML, CSV or other formats!

.. important::

    Use the API to create your own import/export scripts!

When importing historical test data from other systems your input files
may contain arbitrary information, whose organization and meaning is known only
to you! There's no way Kiwi TCMS will be able to reliably guess what that
data may be and how to interpret it.

When exporting machine readable formats are used to facilitate integration
with other software. Again Kiwi TCMS has no idea what information and
organization behind the data is expected on the other end!

XML, CSV, JSON are machine redable file formats which are not designed for
human consumption so this is not a compelling reason to add support
for them!

Kiwi TCMS however exports a very powerful API. The same API is used by
our front-end interface via JavaScript! Using this API you can create
a script which will parse your input files, possibly reorganize them
and send the information to Kiwi TCMS. This gives you the ultimate control
over how to import and export data to/from Kiwi TCMS!

Example(s) how to use this API can be found
`here <https://github.com/kiwitcms/api-scripts>`_.

Further information can be found at :ref:`api` and
https://tcms-api.readthedocs.io/en/latest/modules/tcms_api.plugin_helpers.html.

.. important::

    Please be a good open source citizen and share your import/export scripts
    with the rest of the Kiwi TCMS community. You are welcome to do so by
    opening a pull request at https://github.com/kiwitcms/api-scripts.


Alternatively you can develop your customized import/export as a web
application and distribute it to your users as a Kiwi TCMS plugin.
