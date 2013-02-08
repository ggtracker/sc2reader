# Encoding: UTF-8

# Run tests with "py.test" in the project root dir
import os, sys
import pytest
import datetime

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),"../")))

import sc2reader
from sc2reader.exceptions import ParseError

def test_a_WoL_s2gs():
    summary = sc2reader.load_game_summary("test_s2gs/s2gs1.s2gs")
    assert summary.players[0].resource_collection_rate == 1276
    assert summary.players[0].build_order[0].order == 'Probe'

def test_a_HotS_s2gs():
    summary = sc2reader.load_game_summary("test_s2gs/hots1.s2gs")
    assert summary.players[0].resource_collection_rate == 1599
    assert summary.players[0].build_order[0].order == 'SCV'

def test_another_HotS_s2gs():
    summary = sc2reader.load_game_summary("test_s2gs/hots2.s2gs")
    assert summary.players[0].enemies_destroyed == 14575
    assert summary.players[0].time_supply_capped == 50
    assert summary.players[0].idle_production_time == 4438
    assert summary.players[0].resources_spent == 25450
    assert summary.players[0].apm == 204
    assert summary.players[0].workers_active_graph.as_points()[8][1] == 25
    assert summary.players[0].upgrade_spending_graph.as_points()[8][1] == 300

