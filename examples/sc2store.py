#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cPickle
import os
import shutil
import sys
import sqlite3
import time

import sc2reader

from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=2).pprint

from sqlalchemy import create_engine
from sqlalchemy import Column, ForeignKey, distinct, Table
from sqlalchemy import Integer, String, Sequence, DateTime
from sqlalchemy.orm import relationship, sessionmaker

from sqlalchemy.orm.exc import NoResultFound

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
Base = declarative_base()

party_member = Table('party_member', Base.metadata,
    Column('person_id', Integer, ForeignKey('person.id')),
    Column('party_id', Integer, ForeignKey('party.id')),
)

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, Sequence('person_id_seq'), primary_key=True)

    name = Column(String(50))
    url = Column(String(50))
    parties = relationship('Party', secondary=party_member)
    players = relationship('Player')


class Party(Base):
    __tablename__ = 'party'
    id = Column(Integer, Sequence('party_id_seq'), primary_key=True)

    player_names = Column(String(255))

    members = relationship('Person', secondary=party_member)
    teams = relationship('Team')

    def __init__(self, *players):
        self.player_names = ''
        self.members = list()
        self.add_players(*players)

    def add_players(self, *players):
        for player in players:
            self.player_names += '['+player.name+']'
            self.members.append(player.person)

    @classmethod
    def make_player_names(self, players):
        return ''.join(sorted('['+player.name+']' for player in players))


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, Sequence('game_id_seq'), primary_key=True)

    map = Column(String(255))
    file_name = Column(String(255))
    datetime = Column(DateTime)
    category = Column(String(50))
    type = Column(String(20))
    matchup = Column(String(100))
    length = Column(Integer)
    build = Column(String(25))
    release_string = Column(String(50))

    teams = relationship('Team')
    players = relationship('Player')

    def __init__(self, replay, db):
        self.map = replay.map
        self.file_name = replay.filename
        self.type = replay.type
        self.datetime = replay.date
        self.category = replay.category
        self.length = replay.length.seconds
        self.winner_known = replay.winner_known
        self.build = replay.build
        self.release_string = replay.release_string
        self.teams = [Team(team,db) for team in replay.teams]
        self.matchup = 'v'.join(sorted(team.lineup for team in self.teams))
        self.players = sum((team.players for team in self.teams), [])


class Team(Base):
    __tablename__ = 'team'
    id = Column(Integer, Sequence('team_id_seq'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'))
    party_id = Column(Integer, ForeignKey('party.id'))

    result = Column(String(50))
    number = Column(Integer)
    lineup = Column(String(10))

    players = relationship('Player')
    party = relationship('Party')
    game = relationship('Game')

    def __init__(self, team, db):
        self.number = team.number
        self.result = team.result
        self.players = [Player(player,db) for player in team.players]
        self.lineup = ''.join(sorted(player.play_race[0].upper() for player in self.players))

        try:
            player_names = Party.make_player_names(self.players)
            self.party = db.query(Party).filter(Party.player_names == player_names).one()
        except NoResultFound as e:
            self.party = Party(*self.players)


class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, Sequence('player_id_seq'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'))
    team_id = Column(Integer, ForeignKey('team.id'))
    person_id = Column(Integer, ForeignKey('person.id'))

    play_race = Column(String(20))
    pick_race = Column(String(20))
    color_str = Column(String(20))
    color_hex = Column(String(20))

    name = association_proxy('person','name')
    person = relationship('Person')
    team = relationship('Team')
    game = relationship('Game')

    def __init__(self, player, db):
        try:
            self.person = db.query(Person).filter(Person.name == player.name).one()
        except NoResultFound as e:
            self.person = Person()
            self.person.name = player.name
            self.person.url = player.url

        self.play_race = player.play_race
        self.pick_race = player.pick_race
        self.color_str = str(player.color)
        self.color_hex = player.color.hex


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, Sequence('message_id_seq'), primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Stores replay meta data into an SQL database')
    parser.add_argument('--storage', default='sqlite:///:memory:', type=str, help='Path to the sql storage file of choice')
    parser.add_argument('paths', metavar='PATH', type=str, nargs='+', help='Path to a replay file or a folder of replays')
    return parser.parse_args()

def main():
    args = parse_args()
    db = load_session(args)

    for path in args.paths:
        for file_name in sc2reader.utils.get_files(path, depth=0):
            print "CREATING: {0}".format(file_name)
            db.add(Game(sc2reader.read_file(file_name), db))

    db.commit()

    print list(db.query(distinct(Person.name)).all())

    #for row in db.query(distinct(Person.name)).all():
    #    print row


def load_session(args):
    engine = create_engine(args.storage, echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    main()
