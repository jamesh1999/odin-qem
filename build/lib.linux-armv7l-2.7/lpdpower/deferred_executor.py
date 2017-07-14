"""
deferred_executor.py - deferred executor class for ODIN adapters.

This module provides a deferred executor class that allows command execution to
be deferred by a programmable delay (e.g. to sequence turn-on of elements of a system).

Tim Nicholls, STFC Application Engineering Group
"""

import time
from functools import partial


class DeferredCommand(object):
    """Provides a simple container for a deferred executor."""

    def __init__(self, command, delay, *args, **kwargs):
        """Initialise a deferred command.

        Builds a function partial for the command and its arguments and stores the delay value.
        """
        self.partial = partial(command, *args, **kwargs)
        self.delay = delay

    def execute(self):
        """Execute the deferred command by calling the partial."""
        self.partial()


class DeferredExecutor(object):
    """Implements a deferred command executor."""

    def __init__(self):
        """Initialise the DeferredExecutor object."""
        self.execution_queue = []
        self.last_executed = 0.0

    def enqueue(self, command, delay, *args, **kwargs):
        """Enqueue a command for execution.

        This method enqueues a command for execution by the executor with a delay. Note that the
        delay is relative to the previous command in the queue, not absolute with respect to the
        time at which this function is called.
        :param command: command to execute
        :param delay: delay in seconds between queued commands
        :param args: positional argument list to pass to command
        :param kwarg: keyword argument list to pass to command
        """
        self.execution_queue.append(DeferredCommand(command, delay, *args, **kwargs))

    def pending(self):
        """Return number of pending commands on execution queue."""
        return len(self.execution_queue)

    def process(self):
        """Process the execution queue.

        This method should be called to process the execution queue. If any commands are currently
        queued, the first on the queue will be executed if the appropriate delay since the last
        command has been exceeded.
        """
        if len(self.execution_queue) > 0:
            now = time.time()
            next_command = self.execution_queue[0]
            if now >= (self.last_executed + next_command.delay):
                next_command.execute()
                self.execution_queue.pop(0)
                self.last_executed = now

    def clear(self):
        """Clear any pending commands off the execution queue."""
        del self.execution_queue[:]
