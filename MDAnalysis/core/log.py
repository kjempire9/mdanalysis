# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# MDAnalysis --- http://mdanalysis.googlecode.com
# Copyright (c) 2006-2011 Naveen Michaud-Agrawal,
#               Elizabeth J. Denning, Oliver Beckstein,
#               and contributors (see website for details)
# Released under the GNU Public Licence, v2 or any higher version
#
# Please cite your use of MDAnalysis in published work:
#
#     N. Michaud-Agrawal, E. J. Denning, T. B. Woolf, and
#     O. Beckstein. MDAnalysis: A Toolkit for the Analysis of
#     Molecular Dynamics Simulations. J. Comput. Chem. 32 (2011), 2319--2327,
#     doi:10.1002/jcc.21787
#

"""
Setting up logging --- :mod:`MDAnalysis.core.log`
====================================================

Configure logging for MDAnalysis. Import this module if logging is
desired in application code.

Logging to a file and the console is set up by default as described
under `logging to multiple destinations`_.

The top level logger of the library is named *MDAnalysis* by
convention; a simple logger that writes to the console and logfile can
be created with the :func:`create` function. This only has to be done
*once*. For convenience, the default MDAnalysis logger can be created
with :func:`MDAnalysis.start_logger`::

 import MDAnalysis
 MDAnalysis.start_logger()

Once this has been done, MDAnalysis will write messages to the logfile
(named `MDAnalysis.log` by default but this can be changed with the
optional argument to :func:`~MDAnalysis.start_logger`).

Any code can log to the MDAnalysis logger by using ::

 import logging
 logger = logging.getLogger('MDAnalysis.MODULENAME')

 # use the logger, for example at info level:
 logger.info("Starting task ...")

The important point is that the name of the logger begins with
"MDAnalysis.".

.. _logging to multiple destinations:
   http://docs.python.org/library/logging.html?#logging-to-multiple-destinations

.. SeeAlso:: The :mod:`logging` module in the standard library contains
             in depth documentation about using logging.


Convenience functions
---------------------

Two convenience functions at the top level make it easy to start and
stop the default *MDAnalysis* logger.

.. autofunction:: MDAnalysis.start_logging
.. autofunction:: MDAnalysis.stop_logging


Other functions and classes for logging purposes
------------------------------------------------

.. autogenerated, see Online Docs
"""
from __future__ import division

import sys
import logging

def create(logger_name="MDAnalysis", logfile="MDAnalysis.log"):
    """Create a top level logger.

    - The file logger logs everything (including DEBUG).
    - The console logger only logs INFO and above.

    Logging to a file and the console as described under `logging to
    multiple destinations`_.

    The top level logger of MDAnalysis is named *MDAnalysis*.  Note
    that we are configuring this logger with console output. If a root
    logger also does this then we will get two output lines to the
    console.

    .. _logging to multiple destinations:
       http://docs.python.org/library/logging.html?#logging-to-multiple-destinations
    """

    logger = logging.getLogger(logger_name)

    logger.setLevel(logging.DEBUG)

    # handler that writes to logfile
    logfile_handler = logging.FileHandler(logfile)
    logfile_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    logfile_handler.setFormatter(logfile_formatter)
    logger.addHandler(logfile_handler)

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def clear_handlers(logger):
    """clean out handlers in the library top level logger

    (only important for reload/debug cycles...)
    """
    for h in logger.handlers:
        logger.removeHandler(h)

class NullHandler(logging.Handler):
    """Silent Handler.

    Useful as a default::

      h = NullHandler()
      logging.getLogger("MDAnalysis").addHandler(h)
      del h

    """
    def emit(self, record):
        pass


def echo(s=''):
    """Simple string output that immediately prints to the console."""
    sys.stderr.write(s)
    sys.stderr.flush()


class ProgressMeter(object):
    """Simple progress meter

    Usage::

       u = Universe(PSF, DCD)
       pm = ProgressMeter(u.trajectory.numframes, interval=100)
       for ts in u.trajectory:
           pm.print(ts.frame)
           ...

    Will produce for a trajectory with 10000 frames

       Step   100/10000 [  1.0%]
       Step   200/10000 [  2.0%]
       ...

    as generated by the default *format* string ::

      Step %(step)5d/%(numsteps)d [%(percentage)5.1%%]\r"

    """
    def __init__(self, numsteps, format=None, interval=10, offset=0):
        """Set up the ProgresMeter

        :Arguments:
           *numsteps*
              total number of steps
        :Keywords:
           *interval*
              only calculate progress every *interval* steps [10]
           *format*
              a format string with Python variable interpolation. Allowed
              values:

                * _step_: current step
                * _numsteps_: total number of steps as supplied in *numsteps*
                * _percentage_: percentage of total

              The last call to :meth:`ProgressMeter.print` will automatically
              issue a newline ``\\n`` if the last character is the carriage
              return ``\\r``.

              If *format* is ``None`` then the default is used.
              ["Step %(step)5d/%(numsteps)d [%(percentage)5.1%%]\\r"]
           *offset*
              number to add to *step*; e.g. if *step* is 0-based then one would
              set *offset* = 1 [0]

        """
        self.numsteps = numsteps
        self.interval = int(interval)
        self.offset = int(offset)
        if format is None:
            format = "Step %(step)5d/%(numsteps)d [%(percentage)5.1%%]\r"
        self.format = format
        if self.format.endswith('\r'):
            self.last_newline = '\n'
        else:
            self.last_newline = None
        self.step = 0
        self.percentage = 0.0
        assert numsteps > 0, "numsteps step must be >0"
        assert interval > 0, "interval step must be >0"

    def update(self, step):
        """Update the state of the ProgressMeter"""
        self.step = step + self.offset
        self.percentage = 100. * self.step/self.numsteps

    def echo(self, step):
        """Print the state to stderr, but only every *interval* steps.

        1) calls :meth:`~ProgressMeter.update`
        2) writes step and percentage to stderr with :func:`echo`,
           using the format string (in :attr:`ProgressMeter.format`)

        The last step is always shown, even if not on an *interval*, and a
        carriage return is replaced with a new line for a cleaner display.
        """
        self.update(step)
        format = self.format
        if self.step == self.numsteps:
            if self.last_newline:
                format = self.format[:-1] + self.last_newline
        elif self.step % self.interval == 0:
            pass
        else:
            return
        echo(format % vars(self))
