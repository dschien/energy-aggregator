__author__ = 'schien'
# bind = "127.0.0.1:9000"  # Don't use port 80 becaue nginx occupied it already.
# errorlog = 'log/gunicorn/ep-access.log'  # Make sure you have the log folder create
# accesslog = 'log/gunicorn/ep-error.log'
# loglevel = 'debug'
# workers = 1  # the number of recommended workers is '2 * number of CPUs + 1'

import os


def numCPUs():
    if not hasattr(os, "sysconf"):
        raise RuntimeError("No sysconf detected.")
    return os.sysconf("SC_NPROCESSORS_ONLN")


# bind = "127.0.0.1:8002"
workers = numCPUs() * 2 + 1
