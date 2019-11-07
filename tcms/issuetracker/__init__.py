"""
    Kiwi TCMS supports internal bug tracking functionality and
    integration between bug tracker and the rest of the system.
    This behavior is defined in :mod:`tcms.issuetracker.base`.
    The integration interface provides default behavior which can be
    overridden in subsequent implementations if desired.

    The scope is also listed below:

    - *1-click bug report* - by clicking a UI element inside TestExecution
      Kiwi TCMS will try to automatically report a new bug in the selected
      bug tracker. If this fails will fall back to opening a new browser
      window to manually enter the required information. Fields will be
      pre-filled with correct information when possible.

    - *automatic bug update* - when linking existing bug reports to TestExecution
      the bug report will be "linked" back to the TE. By default this is achieved
      by adding a comment to the bug report.

    - *show bug info* - on pages which display bugs the tester could
      see more contextual information by hovering the mouse over the info
      icon. A tooltip will appear. Default implementation is to display
      OpenGraph Protocol data for that URL. Can be customized. Information
      is cached.
"""
