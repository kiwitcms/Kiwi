"""
    Kiwi TCMS supports internal bug tracking functionality and
    integration between external bug trackers and the rest of the system.
    The integration interface is defined in :mod:`tcms.issuetracker.base`
    and can be overridden in subsequent implementations if desired.

    The current scope is:

    - *1-click bug report* - by clicking a UI element inside TestExecution
      Kiwi TCMS will try to automatically report a new bug in the selected
      bug tracker. If this fails will fall back to opening a new browser
      window to manually enter the required information. Fields will be
      pre-filled with correct information when possible.

    - *automatic bug update* - when linking existing bug reports to TestExecution
      the bug report will be "linked" back to the TE. By default this is achieved
      by adding a comment to the bug report.

    - *show bug info* - on pages which display bugs the tester could
      see more contextual information by hovering the mouse over an info
      icon. A tooltip will appear. Default implementation is to display
      OpenGraph Protocol data for that URL. Information is cached.

    .. important::

        Kiwi TCMS' own internal bug tracker is a light-weight solution for small
        teams. You can disable it by defining ``KIWI_DISABLE_BUGTRACKER=yes``
        in your environment variables!

    .. important::

        Integration details for supported bug trackers can be found at
        :mod:`tcms.issuetracker.types`!
        Additional integrations are provided via add-ons. For more information
        see :mod:`trackers_integration.issuetracker`!
"""
