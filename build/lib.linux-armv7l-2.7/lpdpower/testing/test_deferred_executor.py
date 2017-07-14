"""Unit test cases for DeferredExecutor."""

import sys
if sys.version_info[0] == 3:  # pragma: no cover
    from unittest.mock import Mock, call
else:                         # pragma: no cover
    from mock import Mock, call

from nose.tools import *
from lpdpower.deferred_executor import DeferredCommand, DeferredExecutor

class TestDeferredCommand():

    @classmethod
    def setup_class(cls):

        cls.command = Mock()

    def test_deferred_command_no_args(self):

        dc = DeferredCommand(self.command, 1.0)
        dc.execute()
        self.command.assert_called_with()

    def test_deferred_command_with_args(self):

        dc_args = (1, 2, 3)
        dc_kwargs = {'test': 'value'}
        dc = DeferredCommand(self.command, 1.0, *dc_args, **dc_kwargs)
        dc.execute()
        self.command.assert_called_with(*dc_args, **dc_kwargs)

    def test_deferred_command_has_delay(self):

        delay = 1.234
        dc = DeferredCommand(self.command, delay)
        assert_equal(dc.delay, delay)

class TestDeferredExecutor():

    def setup(self):

        self.command = Mock()
        self.deferred_executor = DeferredExecutor()

    def test_empty_executor_has_no_pending(self):

        assert_equals(self.deferred_executor.pending(), 0)

    def test_executor_num_pending(self):

        num_commands = 10
        for i in range(num_commands):
            self.deferred_executor.enqueue(self.command, 1.0)

        assert_equals(self.deferred_executor.pending(), num_commands)

    def test_executor_process_queue(self):

        num_commands = 20
        for i in range(num_commands):
            self.deferred_executor.enqueue(self.command, 0.001, i)

        cmd_calls = [call(i) for i in range(num_commands)]

        while self.deferred_executor.pending():
            self.deferred_executor.process()

        assert_equal(self.command.call_count, num_commands)
        assert_equal(self.command.call_args_list, cmd_calls)

    def test_executor_clear(self):

        num_commands = 10
        for i in range(num_commands):
            self.deferred_executor.enqueue(self.command, 1.0)

        assert_equal(self.deferred_executor.pending(), num_commands)
        self.deferred_executor.clear()
        assert_equal(self.deferred_executor.pending(), 0)
