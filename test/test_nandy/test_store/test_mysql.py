import unittest

import os
import time
import json
import pymysql

import nandy.store.mysql

class TestNandyMySQL(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        self.mysql = nandy.store.mysql.MySQL()
        nandy.store.mysql.create_database()
        nandy.store.mysql.Base.metadata.create_all(self.mysql.engine)

    def tearDown(self):

        self.mysql.session.close()

    def test_MySQL(self):

        self.assertEqual(str(self.mysql.session.get_bind().url), "mysql+pymysql://root@mysql:3306/nandy")

        mysql = nandy.store.mysql.MySQL("unit", 7)
        self.assertEqual(str(mysql.session.get_bind().url), "mysql+pymysql://root@unit:7/nandy")

    def test_Person(self):

        self.mysql.session.add(nandy.store.mysql.Person(name="unit", email="test"))
        self.mysql.session.commit()

        person = self.mysql.session.query(nandy.store.mysql.Person).one()
        self.assertEqual(str(person), "<Person(name='unit')>")
        self.assertEqual(person.name, "unit")
        self.assertEqual(person.email, "test")
        
    def test_Area(self):

        self.mysql.session.add(nandy.store.mysql.Area(
            name='Unit Test',
            status="messy",
            updated=8,
            data={"a": 1}
        ))
        self.mysql.session.commit()

        area = self.mysql.session.query(nandy.store.mysql.Area).one()
        self.assertEqual(str(area), "<Area(name='Unit Test')>")
        self.assertEqual(area.name, "Unit Test")
        self.assertEqual(area.status, "messy")
        self.assertEqual(area.updated, 8)
        self.assertEqual(area.data, {"a": 1})

        area.data["a"] = 2
        self.mysql.session.commit()
        area = self.mysql.session.query(nandy.store.mysql.Area).one()
        self.assertEqual(area.data, {"a": 2})

    def test_Template(self):

        self.mysql.session.add(nandy.store.mysql.Template(
            name='Unit Test',
            kind="chore",
            data={"a": 1}
        ))
        self.mysql.session.commit()

        template = self.mysql.session.query(nandy.store.mysql.Template).one()
        self.assertEqual(str(template), "<Template(name='Unit Test',kind='chore')>")
        self.assertEqual(template.name, "Unit Test")
        self.assertEqual(template.kind, "chore")
        self.assertEqual(template.data, {"a": 1})

        template.data["a"] = 2
        self.mysql.session.commit()
        template = self.mysql.session.query(nandy.store.mysql.Template).one()
        self.assertEqual(template.data, {"a": 2})

    def test_Chore(self):

        person = nandy.store.mysql.Person(name="unit", email="test")
        self.mysql.session.add(person)
        self.mysql.session.commit()

        self.mysql.session.add(nandy.store.mysql.Chore(
            person_id=person.person_id,
            name='Unit Test',
            status="started",
            created=7,
            updated=8,
            data={"a": 1}
        ))
        self.mysql.session.commit()

        chore = self.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(str(chore), "<Chore(name='Unit Test',person='unit',created=7)>")
        self.assertEqual(chore.person_id, person.person_id)
        self.assertEqual(chore.name, "Unit Test")
        self.assertEqual(chore.status, "started")
        self.assertEqual(chore.created, 7)
        self.assertEqual(chore.updated, 8)
        self.assertEqual(chore.data, {"a": 1})

        chore.data["a"] = 2
        self.mysql.session.commit()
        chore = self.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(chore.data, {"a": 2})

    def test_Act(self):

        person = nandy.store.mysql.Person(name="unit", email="test")
        self.mysql.session.add(person)
        self.mysql.session.commit()

        self.mysql.session.add(nandy.store.mysql.Act(
            person_id=person.person_id,
            name='Unit Test',
            value="positive",
            created=7,
            data={"a": 1}
        ))
        self.mysql.session.commit()

        act = self.mysql.session.query(nandy.store.mysql.Act).one()
        self.assertEqual(str(act), "<Act(name='Unit Test',person='unit',created=7)>")
        self.assertEqual(act.person_id, person.person_id)
        self.assertEqual(act.name, "Unit Test")
        self.assertEqual(act.value, "positive")
        self.assertEqual(act.created, 7)
        self.assertEqual(act.data, {"a": 1})

        act.data["a"] = 2
        self.mysql.session.commit()
        act = self.mysql.session.query(nandy.store.mysql.Act).one()
        self.assertEqual(act.data, {"a": 2})