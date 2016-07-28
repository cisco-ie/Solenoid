import unittest
import json
from solenoid import edit_rib
from solenoid.tests import tools



class RestRibTestCase(unittest.TestCase, object):
    def setUp(self):
        #Set global variable
        edit_rib.FILEPATH = tools.add_location('examples/filter-empty.txt')
        #Clear out logging files.
        open(tools.add_location('../updates.txt'), 'w').close()
        open(tools.add_location('../logs/debug.log'), 'w').close()
        open(tools.add_location('../logs/errors.log'), 'w').close()

    def test_create_transport_object_correct_class_created(self):
        transport_object = edit_rib.create_transport_object()
        self.assertIsInstance(transport_object, edit_rib.JSONRestCalls)

    def test_rib_announce_rest(self):
        with open(tools.add_location('examples/integration/rendered_announce.txt')) as f:
            rendered_announce = f.read()
        edit_rib.rib_announce(rendered_announce)
        self.assertIn('| ANNOUNCE | ', tools.check_debuglog()[0])

    def test_rib_withdraw_rest(self):
        withdraw_prefixes = ['1.1.1.1/32',
                     '1.1.1.2/32',
                     '2.2.2.2/32',
                     '3.3.3.3/32']
        edit_rib.rib_withdraw(withdraw_prefixes)
        self.assertIn('| WITHDRAW | ', tools.check_debuglog()[0])

    def test_rib_announce_rest_json(self):
        with open(tools.add_location('examples/integration/exa-announce.json')) as f:
            exa_announce = f.read()
        edit_rib.render_config(json.loads(exa_announce))
        self.assertIn('| ANNOUNCE | ', tools.check_debuglog()[0])

    def test_rib_withdraw_rest_json(self):
        with open(tools.add_location('examples/integration/exa-withdraw.json')) as f:
            exa_withdraw = f.read()
        edit_rib.render_config(json.loads(exa_withdraw))
        self.assertIn('| WITHDRAW | ', tools.check_debuglog()[0])

if __name__ == '__main__':
    unittest.main(failfast=True)

