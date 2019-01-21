import unittest

import os
import time
import json
import pymysql

import nandy_mysql

def create_database():

    connection = pymysql.connect(host='mysql', user='root')

    try:

        with connection.cursor() as cursor:
            cursor.execute("DROP DATABASE IF EXISTS nandy")
            cursor.execute("CREATE DATABASE nandy")

        connection.commit()

    finally:

        connection.close()

class TestNandyMySQL(unittest.TestCase):

    maxDiff = None

    def setUp(self):

        create_database()

        self.nandy_mysql = nandy_mysql.MySQL()
        nandy_mysql.Base.metadata.create_all(self.nandy_mysql.engine)

    def tearDown(self):

        self.nandy_mysql.session.close()

    def test_MySQL(self):

        self.assertEqual(str(self.nandy_mysql.session.get_bind().url), "mysql+pymysql://root@mysql:3306/nandy")

        mysql = nandy_mysql.MySQL("unit", 7)
        self.assertEqual(str(mysql.session.get_bind().url), "mysql+pymysql://root@unit:7/nandy")

    def test_Person(self):

        self.nandy_mysql.session.add(nandy_mysql.Person(name="unit", email="test"))
        self.nandy_mysql.session.commit()

        person = self.nandy_mysql.session.query(nandy_mysql.Person).one()
        self.assertEqual(str(person), "<Person(name='unit')>")
        self.assertEqual(person.name, "unit")
        self.assertEqual(person.email, "test")
        
    def test_Area(self):

        self.nandy_mysql.session.add(nandy_mysql.Area(
            name='Unit Test',
            status="messy",
            updated=8,
            data={"a": 1}
        ))
        self.nandy_mysql.session.commit()

        area = self.nandy_mysql.session.query(nandy_mysql.Area).one()
        self.assertEqual(str(area), "<Area(name='Unit Test')>")
        self.assertEqual(area.name, "Unit Test")
        self.assertEqual(area.status, "messy")
        self.assertEqual(area.updated, 8)
        self.assertEqual(area.data, {"a": 1})

        area.data["a"] = 2
        self.nandy_mysql.session.commit()
        area = self.nandy_mysql.session.query(nandy_mysql.Area).one()
        self.assertEqual(area.data, {"a": 2})

    def test_Template(self):

        self.nandy_mysql.session.add(nandy_mysql.Template(
            name='Unit Test',
            kind="chore",
            data={"a": 1}
        ))
        self.nandy_mysql.session.commit()

        template = self.nandy_mysql.session.query(nandy_mysql.Template).one()
        self.assertEqual(str(template), "<Template(name='Unit Test',kind='chore')>")
        self.assertEqual(template.name, "Unit Test")
        self.assertEqual(template.kind, "chore")
        self.assertEqual(template.data, {"a": 1})

        template.data["a"] = 2
        self.nandy_mysql.session.commit()
        template = self.nandy_mysql.session.query(nandy_mysql.Template).one()
        self.assertEqual(template.data, {"a": 2})

    def test_Chore(self):

        person = nandy_mysql.Person(name="unit", email="test")
        self.nandy_mysql.session.add(person)
        self.nandy_mysql.session.commit()

        self.nandy_mysql.session.add(nandy_mysql.Chore(
            person_id=person.person_id,
            name='Unit Test',
            status="started",
            created=7,
            updated=8,
            data={"a": 1}
        ))
        self.nandy_mysql.session.commit()

        chore = self.nandy_mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(str(chore), "<Chore(name='Unit Test',person='unit',created=7)>")
        self.assertEqual(chore.person_id, person.person_id)
        self.assertEqual(chore.name, "Unit Test")
        self.assertEqual(chore.status, "started")
        self.assertEqual(chore.created, 7)
        self.assertEqual(chore.updated, 8)
        self.assertEqual(chore.data, {"a": 1})

        chore.data["a"] = 2
        self.nandy_mysql.session.commit()
        chore = self.nandy_mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(chore.data, {"a": 2})

    def test_Act(self):

        person = nandy_mysql.Person(name="unit", email="test")
        self.nandy_mysql.session.add(person)
        self.nandy_mysql.session.commit()

        self.nandy_mysql.session.add(nandy_mysql.Act(
            person_id=person.person_id,
            name='Unit Test',
            value="positive",
            created=7,
            data={"a": 1}
        ))
        self.nandy_mysql.session.commit()

        act = self.nandy_mysql.session.query(nandy_mysql.Act).one()
        self.assertEqual(str(act), "<Act(name='Unit Test',person='unit',created=7)>")
        self.assertEqual(act.person_id, person.person_id)
        self.assertEqual(act.name, "Unit Test")
        self.assertEqual(act.value, "positive")
        self.assertEqual(act.created, 7)
        self.assertEqual(act.data, {"a": 1})

        act.data["a"] = 2
        self.nandy_mysql.session.commit()
        act = self.nandy_mysql.session.query(nandy_mysql.Act).one()
        self.assertEqual(act.data, {"a": 2})