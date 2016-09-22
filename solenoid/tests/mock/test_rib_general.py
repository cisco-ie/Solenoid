import unittest
import json
import time
import sys
import os
import shutil

from StringIO import StringIO
from mock import patch
from solenoid import edit_rib
from solenoid.tests import tools


class GeneralRibTestCase(tools.TestBookends, object):

    def setUp(self):
        shutil.copy(
            tools.add_location('examples/config/restconf/restconf_good.config'),
            tools.add_location('../../solenoid.config')
        )
        self.transport = edit_rib.create_transport_object()
        #Set global variable.
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-empty.txt')
        #Clear out logging files.
        open(tools.add_location('../updates.txt'), 'w').close()
        open(tools.add_location('../logs/debug.log'), 'w').close()
        open(tools.add_location('../logs/errors.log'), 'w').close()

    @patch('sys.stdin', StringIO(tools.exa_raw('announce_g')))
    @patch('solenoid.edit_rib.update_validator')
    def test_update_watcher_call(self, mock_validator):
       # Monkey patching to avoid infinite loop.
        def mock_watcher():
            raw_update = sys.stdin.readline().strip()
            edit_rib.update_validator(raw_update, self.transport)
        args = tools.exa_raw('announce_g')
        edit_rib.update_watcher = mock_watcher
        mock_watcher()
        mock_validator.assert_called_with(args, self.transport)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_good_json_conversion(self, mock_render):
        raw_g_json = tools.exa_raw('announce_g')
        args = json.loads(tools.exa_raw('announce_g'))
        edit_rib.update_validator(raw_g_json, self.transport)
        mock_render.assert_called_with(args, self.transport)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_bad_json_conversion(self, mock_render):
        raw_b_json = tools.exa_raw('invalid_json')
        with self.assertRaises(ValueError):
            edit_rib.update_validator(raw_b_json, self.transport)
        # Check the logs.
        self.assertIn('Failed JSON conversion for BGP update\n',
                      tools.check_errorlog()[0])
        self.assertFalse(mock_render.called)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_incorrect_model(self, mock_render):
        raw_b_json = tools.exa_raw('invalid_i_model')
        with self.assertRaises(KeyError):
            edit_rib.update_validator(raw_b_json, self.transport)
        # Check the logs.
        self.assertTrue('Not a valid update message type\n',
                        tools.check_debuglog()[0])
        self.assertFalse(mock_render.called)

    def test_update_file(self):
        edit_rib.update_file(
            {
                'Test': time.ctime()
            }
        )
        with open(tools.add_location('../updates.txt')) as f:
            self.assertTrue(len(f.readlines()) == 1)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_normal_model_missing_value(self, mock_announce):
        formatted_json = json.loads(tools.exa_raw('invalid_n_model'))
        edit_rib.rib_announce = mock_announce
        with self.assertRaises(KeyError):
            edit_rib.render_config(formatted_json, self.transport)
        self.assertIn('Not a valid update message type\n',
                      tools.check_errorlog()[0])
        self.assertFalse(mock_announce.called)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_normal_model_eor(self, mock_announce):
        formatted_json = json.loads(tools.exa_raw('announce_eor'))
        #edit_rib.rib_announce = mock_announce
        edit_rib.render_config(formatted_json, self.transport)
        self.assertIn('EOR message\n', tools.check_debuglog()[0])
        self.assertFalse(mock_announce.called)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_announce_good(self, mock_announce):
        formatted_json = json.loads(tools.exa_raw('announce_g'))
        edit_rib.render_config(formatted_json, self.transport)
        with open(tools.add_location('examples/rendered_announce.txt'), 'U') as f:
            rendered_announce = f.read()
        mock_announce.assert_called_with(rendered_announce, self.transport)

    @patch('solenoid.edit_rib.rib_withdraw')
    def test_render_config_withdraw_good(self, mock_withdraw):
        withdraw_prefixes = ['1.1.1.8/32',
                             '1.1.1.5/32',
                             '1.1.1.7/32',
                             '1.1.1.9/32',
                             '1.1.1.2/32',
                             '1.1.1.1/32',
                             '1.1.1.6/32',
                             '1.1.1.3/32',
                             '1.1.1.10/32',
                             '1.1.1.4/32']
        formatted_json = json.loads(tools.exa_raw('withdraw_g'))
        edit_rib.render_config(formatted_json, self.transport)
        mock_withdraw.assert_called_with(withdraw_prefixes, self.transport)

    def test_filter_prefix_good(self):
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-full.txt')
        start_prefixes = ['1.1.1.9/32',
                          '192.168.3.1/28',
                          '1.1.1.2/32',
                          '1.1.1.1/32',
                          '10.1.1.1/32',
                          '1.1.1.10/32',
                          '10.1.6.1/24']
        filtered_list = edit_rib.filter_prefixes(start_prefixes)
        end_prefixes = ['1.1.1.9/32',
                        '1.1.1.2/32',
                        '1.1.1.1/32',
                        '1.1.1.10/32',
                        '10.1.1.1/32',
                        '10.1.6.1/24']
        self.assertEqual(filtered_list, end_prefixes)

    @patch('solenoid.edit_rib.filter_prefixes')
    @patch('solenoid.edit_rib.rib_withdraw')
    def test_filter_empty(self, mock_withdraw, mock_filter):
        # The Setup configures us to have an empty filter file
        formatted_json = json.loads(tools.exa_raw('withdraw_g'))
        edit_rib.render_config(formatted_json, self.transport)
        mock_filter.assert_not_called()

    def test_filter_all_prefixes(self):
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-all.txt')
        start_prefixes = ['2.2.2.0/32',
                          '10.2.1.1/24']
        filtered_list = edit_rib.filter_prefixes(start_prefixes)
        end_prefixes = []
        self.assertEqual(filtered_list, end_prefixes)

    @patch('solenoid.edit_rib.rib_withdraw')
    def test_render_config_prefixes_all_filtered_withdraw(self, mock_withdraw):
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-all.txt')
        formatted_json = json.loads(tools.exa_raw('withdraw_g'))
        edit_rib.render_config(formatted_json, self.transport)
        mock_withdraw.assert_not_called()

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_prefixes_all_filtered_announce(self, mock_announce):
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-all.txt')
        formatted_json = json.loads(tools.exa_raw('announce_g'))
        edit_rib.render_config(formatted_json, self.transport)
        mock_announce.assert_not_called()

    def test_filter_prefix_invalid(self):
        edit_rib.FILEPATH = tools.add_location('examples/filter/filter-invalid.txt')
        start_prefixes = ['1.1.1.9/32',
                          '192.168.3.1/28',
                          '1.1.1.2/32',
                          '1.1.1.1/32',
                          '10.1.1.1/32',
                          '1.1.1.10/32',
                          '10.1.6.1/24']
        from netaddr import AddrFormatError
        with self.assertRaises(AddrFormatError):
            edit_rib.filter_prefixes(start_prefixes)

    def test_create_transport_object_no_config_file(self):
        #Remove the config file
        if os.path.isfile(tools.add_location('../../solenoid.config')):
            os.remove(tools.add_location('../../solenoid.config'))
        with self.assertRaises(SystemExit):
            edit_rib.create_transport_object()
        self.assertIn('Something is wrong with your config file:',
                      tools.check_debuglog()[0])

if __name__ == '__main__':
    unittest.main()

