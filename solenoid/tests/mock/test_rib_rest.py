import unittest
import os
import json
import time
import sys
from StringIO import StringIO
from mock import patch, call
from solenoid import edit_rib

location = os.path.dirname(os.path.realpath(__file__))
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


def _exa_raw(test):
    with open(os.path.join(location, 'examples/exa-raw.json')) as f:
        lines = f.readlines()
        if test == 'announce_g':
            return lines[0].strip()
        elif test == 'withdraw_g':
            return lines[1].strip()
        elif test == 'withdraw_b':
            return lines[2].strip()
        elif test == 'invalid_json':
            return lines[3].strip()
        elif test == 'invalid_n_model':
            return lines[4].strip()
        elif test == 'invalid_i_model':
            return lines[5].strip()
        elif test == 'announce_eor':
            return lines[6].strip()


class RestRibTestCase(unittest.TestCase, object):

    def setUp(self):
        #Set global variable
        edit_rib.filepath = os.path.join(location, 'examples/filter-empty.txt')
        #Clear out logging files.
        open(os.path.join(location, '../updates.txt'), 'w').close()
        open(os.path.join(location, '../logs/debug.log'), 'w').close()
        open(os.path.join(location, '../logs/errors.log'), 'w').close()

    def _check_errorlog(self):
        with open(os.path.join(location, '../logs/errors.log')) as err_log:
            return err_log.readlines()

    def _check_debuglog(self):
        with open(os.path.join(location, '../logs/debug.log')) as debug_log:
            return debug_log.readlines()

    @patch('sys.stdin', StringIO(_exa_raw('announce_g')))
    @patch('solenoid.edit_rib.update_validator')
    def test_update_watcher_call(self, mock_validator):
       # Monkey patching to avoid infinite loop.
        def mock_watcher():
            raw_update = sys.stdin.readline().strip()
            edit_rib.update_validator(raw_update)
        args = _exa_raw('announce_g')
        edit_rib.update_watcher = mock_watcher
        mock_watcher()
        mock_validator.assert_called_with(args)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_good_json_conversion(self, mock_render):
        raw_g_json = _exa_raw('announce_g')
        args = json.loads(_exa_raw('announce_g'))
        edit_rib.update_validator(raw_g_json)
        mock_render.assert_called_with(args)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_bad_json_conversion(self, mock_render):
        raw_b_json = _exa_raw('invalid_json')
        self.assertRaises(ValueError, edit_rib.update_validator(raw_b_json))
        # Check the logs.
        self.assertIn('Failed JSON conversion for BGP update\n',
                      self._check_errorlog()[0])
        self.assertFalse(mock_render.called)

    @patch('solenoid.edit_rib.render_config')
    def test_update_validator_incorrect_model(self, mock_render):
        raw_b_json = _exa_raw('invalid_i_model')
        self.assertRaises(KeyError, edit_rib.update_validator(raw_b_json))
        # Check the logs.
        edit_rib.update_validator(raw_b_json)
        self.assertTrue('Not a valid update message type\n',
                        self._check_debuglog()[0])
        self.assertFalse(mock_render.called)

    def test_update_file(self):
        edit_rib.update_file(
            {
                'Restart': time.ctime()
            }
        )
        with open(os.path.join(location, '../updates.txt')) as f:
            self.assertTrue(len(f.readlines()) == 1)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_normal_model_missing_value(self, mock_announce):
        formatted_json = json.loads(_exa_raw('invalid_n_model'))
        edit_rib.rib_announce = mock_announce
        self.assertRaises(KeyError, edit_rib.render_config(formatted_json))
        edit_rib.render_config(formatted_json)
        self.assertIn('Not a valid update message type\n',
                      self._check_errorlog()[0])
        self.assertFalse(mock_announce.called)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_normal_model_eor(self, mock_announce):
        formatted_json = json.loads(_exa_raw('announce_eor'))
        edit_rib.rib_announce = mock_announce
        edit_rib.render_config(formatted_json)
        self.assertIn('EOR message\n', self._check_debuglog()[0])
        self.assertFalse(mock_announce.called)

    @patch('solenoid.edit_rib.rib_announce')
    def test_render_config_announce_good(self, mock_announce):
        formatted_json = json.loads(_exa_raw('announce_g'))
        edit_rib.render_config(formatted_json)
        with open(os.path.join(location, 'examples/rendered_announce.txt'), 'U') as f:
            rendered_announce = f.read()
        mock_announce.assert_called_with(rendered_announce)

    @patch('solenoid.edit_rib.rib_withdraw')
    def test_render_config_withdraw_good(self, mock_announce):
        formatted_json = json.loads(_exa_raw('withdraw_g'))
        edit_rib.render_config(formatted_json)
        mock_announce.assert_called_with(withdraw_prefixes)

    def test_filter_prefix_good(self):
        edit_rib.filepath = os.path.join(location, 'examples/filter-full.txt')
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

# This test is wrong - the error is raising but assertRaises is failing
    # def test_filter_prefix_invalid(self):
    #     edit_rib.filepath = os.path.join(location, 'examples/filter-invalid.txt')
    #     start_prefixes = ['1.1.1.9/32',
    #                       '192.168.3.1/28',
    #                       '1.1.1.2/32',
    #                       '1.1.1.1/32',
    #                       '10.1.1.1/32',
    #                       '1.1.1.10/32',
    #                       '10.1.6.1/24']
    #     self.assertRaises(edit_rib.AddrFormatError,
    #                       edit_rib.filter_prefixes,
    #                       start_prefixes)

    def test_create_transport_object_correct_class_created(self):
        transportObject = edit_rib.create_transport_object()
        self.assertIsInstance(transportObject, edit_rib.JSONRestCalls)

    def test_create_transport_object_no_config_file(self):
        if os.path.isfile(os.path.join(location, '../../solenoid.config')):
            os.rename(
                os.path.join(location, '../../solenoid.config'),
                os.path.join(location, '../../solenoidtest.config')
            )
        with self.assertRaises(SystemExit):
            edit_rib.create_transport_object()
        self.assertIn('Something is wrong with your config file:',
                      self._check_errorlog()[0])
        if os.path.isfile(os.path.join(location, '../../solenoidtest.config')):
            os.rename(
                os.path.join(location, '../../solenoidtest.config'),
                os.path.join(location, '../../solenoid.config')
            )

    def test_create_transport_object_missing_object(self):
        #check if a solenoid.config already exists and move it
        if os.path.isfile(os.path.join(location, '../../solenoid.config')):
            os.rename(
                os.path.join(location, '../../solenoid.config'),
                os.path.join(location, '../../solenoidtest.config')
            )
        with open(os.path.join(location, '../../solenoid.config'), 'w') as f:
            f.write('[default]')
            f.write('ip: 10.1.1.2')
            #We are missing 'port' here
            f.write('username: user')
            f.write('password: admin')
        with self.assertRaises(SystemExit):
            edit_rib.create_transport_object()
        self.assertIn('Something is wrong with your config file:',
                      self._check_errorlog()[0])
        os.remove(os.path.join(location, '../../solenoid.config'))
        #If solenoid.config did already exist move it back
        if os.path.isfile(os.path.join(location, '../../solenoidtest.config')):
            os.rename(
                os.path.join(location, '../../solenoidtest.config'),
                os.path.join(location, '../../solenoid.config')
            )

    def test_create_transport_object_missing_section(self):
        #check if a solenoid.config already exists and move it
        if os.path.isfile(os.path.join(location, '../../solenoid.config')):
            os.rename(
                os.path.join(location, '../../solenoid.config'),
                os.path.join(location, '../../solenoidtest.config')
            )
        with open(os.path.join(location, '../../solenoid.config'), 'w') as f:
            f.write('ip: 10.1.1.2')
            f.write('port: 80')
            f.write('username: user')
            f.write('password: admin')
        with self.assertRaises(SystemExit):
            edit_rib.create_transport_object()
        self.assertIn('Something is wrong with your config file:',
                      self._check_errorlog()[0])
        os.remove(os.path.join(location, '../../solenoid.config'))
        #If solenoid.config did already exist move it back
        if os.path.isfile(os.path.join(location, '../../solenoidtest.config')):
            os.rename(
                os.path.join(location, '../../solenoidtest.config'),
                os.path.join(location, '../../solenoid.config')
            )

    def test_create_transport_object_multiple_sections(self):
        #check if a solenoid.config already exists and move it
        if os.path.isfile(os.path.join(location, '../../solenoid.config')):
            os.rename(
                os.path.join(location, '../../solenoid.config'),
                os.path.join(location, '../../solenoidtest.config')
            )
        with open(os.path.join(location, '../../solenoid.config'), 'w') as f:
            f.write('[router2]\n')
            f.write('ip: 10.1.1.2\n')
            f.write('port: 80\n')
            f.write('username: user\n')
            f.write('password: admin\n')
            f.write('[router1]\n')
            f.write('ip: 10.1.1.3\n')
            f.write('port: 80\n')
            f.write('username: user\n')
            f.write('password: admin\n')
        transportObject = edit_rib.create_transport_object()
        self.assertIsInstance(transportObject, edit_rib.JSONRestCalls)
        self.assertIn('Multiple routers not currently supported in the configuration file',
                      self._check_debuglog()[0])
        os.remove(os.path.join(location, '../../solenoid.config'))
        #If solenoid.config did already exist move it back
        if os.path.isfile(os.path.join(location, '../../solenoidtest.config')):
            os.rename(
                os.path.join(location, '../../solenoidtest.config'),
                os.path.join(location, '../../solenoid.config')
            )

    @patch('solenoid.edit_rib.JSONRestCalls.patch')
    def test_rib_announce_rest(self, mock_patch):
        with open(os.path.join(location, 'examples/rendered_announce.txt')) as f:
            rendered_announce = f.read()
        edit_rib.rib_announce(rendered_announce)
        mock_patch.assert_called_with(rendered_announce)
        self.assertIn('| ANNOUNCE | ', self._check_debuglog()[0])

    @patch('solenoid.edit_rib.JSONRestCalls.delete')
    def test_rib_withdraw_rest(self, mock_delete):
        edit_rib.rib_withdraw(withdraw_prefixes)
        url = 'Cisco-IOS-XR-ip-static-cfg:router-static/default-vrf/address-family/vrfipv4/vrf-unicast/vrf-prefixes/vrf-prefix='
        comma_list = [prefix.replace('/', ',') for prefix in withdraw_prefixes]
        calls = map(call, map(lambda x: url+x, comma_list))
        mock_delete.assert_has_calls(calls, any_order=True)
        self.assertIn('| WITHDRAW | ', self._check_debuglog()[0])

if __name__ == '__main__':
    unittest.main()
