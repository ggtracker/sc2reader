# -*- coding: UTF-8 -*-

# Newer unittest features aren't built in for python 2.6
import sys
if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import sc2reader
sc2reader.log_utils.log_to_console("INFO")


class TestSummaries(unittest.TestCase):

    def test_a_WoL_s2gs(self):
        summary = sc2reader.load_game_summary("test_s2gs/s2gs1.s2gs")
        self.assertEqual(summary.players[0].resource_collection_rate, 1276)
        self.assertEqual(summary.players[0].build_order[0].order, 'Probe')
        self.assertEqual(summary.expansion, 'WoL')

    def test_a_HotS_s2gs(self):
        summary = sc2reader.load_game_summary("test_s2gs/hots1.s2gs")
        self.assertEqual(summary.players[0].resource_collection_rate, 1599)
        self.assertEqual(summary.players[0].build_order[0].order, 'SCV')
        self.assertEqual(summary.expansion, 'HotS')

    def test_another_HotS_s2gs(self):
        summary = sc2reader.load_game_summary("test_s2gs/hots2.s2gs")
        self.assertEqual(summary.players[0].enemies_destroyed, 14575)
        self.assertEqual(summary.players[0].time_supply_capped, 50)
        self.assertEqual(summary.players[0].idle_production_time, 4438)
        self.assertEqual(summary.players[0].resources_spent, 25450)
        self.assertEqual(summary.players[0].apm, 204)
        self.assertEqual(summary.players[0].workers_active_graph.as_points()[8][1], 25)
        self.assertEqual(summary.players[0].upgrade_spending_graph.as_points()[8][1], 300)
        self.assertEqual(summary.expansion, 'HotS')

if __name__ == '__main__':
    unittest.main()
