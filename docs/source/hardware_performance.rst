Hardware and performance
========================

Kiwi TCMS is predominantly an I/O driven application where disk latency
is more important than CPU performance and memory speed. This chapter
documents our experiments and findings to establish a baseline against
which administrators can plan their deployments.


Hardware requirements
---------------------

In its default configuration Kiwi TCMS runs a web application and
a database server as containers on the same hardware.

- **Minimum**: 1 CPU, 1 GiB memory:
  `t2.micro <https://aws.amazon.com/ec2/instance-types/>`_ AWS instance
  works but runs at >90% memory utilization and risks unnecessary swapping
  and/or going out of memory! If you need to be on the low end use *t2.small*
  or *t3.small* instance
- **Recommended**: 2 CPU, 4 GiB memory: the Kiwi TCMS team has had positive
  experience running on
  `t2.medium and t3.medium <https://aws.amazon.com/ec2/instance-types/>`_
  AWS instances

.. note::

    We've seen satisfactory performance with the default disk volume settings for
    AWS instances:
    `EBS-optimized <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-optimized.html>`_,
    `General Purpose SSD (gp2) <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html#solid-state-drives>`_,
    `100/3000 IOPS <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-io-characteristics.html>`_
    block storage. This is without any Linux filesystem related tweaks or
    changes to the default storage configuration of Docker Engine!


Write APIs execution speed
--------------------------

The various API methods in Kiwi TCMS will have vastly different execution
speeds.
Telemetry and search for example query tons of information from the database
while browsing pages and reporting results uses less queries. A question that
we often hear is *How many test execution results can Kiwi TCMS deal with?*

.. important::

    The information below has been gathered by using the following environment:

    - Client: t2.micro in us-east-1a (same availability zone as server)
    - Server: t3.medium in use-east-1a, 30GB gp2 disk with 100/3000 IOPS
    - Kiwi TCMS v10.0 via ``docker-compose up``
    - Database is ``centos/mariadb-103-centos7`` with a persistent volume backed onto
      the host filesystem
    - Host OS - Amazon Linux, freshly provisioned, no changes from defaults
    - ``perf-script-ng`` version
      `13017d1 <https://github.com/kiwitcms/api-scripts/blob/13017d19263f7fc123776180f78336a59fd228f4/perf-script-ng>`_
      with ``RANGE_SIZE=100`` (called ``R`` below)
    - For each invocation ``perf-script-ng`` creates new *Product*, *Version*
      *Build* and *TestPlan*. Test plan contains ``R x test cases`` then
      ``R x test runs``, each containing the previous test cases and finally
      updating results for all of them. This simulates a huge test matrix against
      the same test plan/product/version/build, e.g. testing on multiple different
      platforms (browser versions + OS combinations for example)
    - The total number of test execution results is ``R^2``
    - The total number of API calls is ``10 + 3R + 2R^2``
    - Single client, no other server load in parallel

    For ``R=100`` we've got ``10000`` test execution results and
    ``20310`` API calls in a single script invocation!

The average results are:

- 35000 test execution results/hour
- 71500 API calls/hour
- 19 requests/second
- 50 ms/request

|t3.medium metrics|

.. note::

    - The first 3 bars in the metrics are from 3 invocations with ``R=30``.
      Best seen in the CPU usage chart. The rest are 3 invocations with ``R=100``.
    - The spike seen during the last invocation has been consistent across
      instance types. We think it could be due to a database re-indexing operation
      but haven't pinned the root cause yet!


.. |t3.medium metrics| image:: ./_static/t3.medium_gp2_r100.png
