import unittest
import unittest.mock

import os
import json

import pymysql

import nandy_data
import nandy_mysql

import test_nandy_graphite
import test_nandy_redis
import test_nandy_mysql

class TestNandyData(unittest.TestCase):

    maxDiff = None

    @unittest.mock.patch("graphyte.Sender", test_nandy_graphite.MockGraphyteSender)
    @unittest.mock.patch("redis.StrictRedis", test_nandy_redis.MockRedis) 
    def setUp(self):

        test_nandy_mysql.create_database()

        self.nandy_data = nandy_data.NandyData()
        nandy_mysql.Base.metadata.create_all(self.nandy_data.mysql.engine)

    def tearDown(self):

        self.nandy_data.mysql.session.close()

    # Sample

    def sample_person(self, name, email=None):

        if email is None:
            email = name

        person = nandy_mysql.Person(name=name, email=email)
        self.nandy_data.mysql.session.add(person)
        self.nandy_data.mysql.session.commit()

        return person

    def sample_area(self, name, status=None, updated=7, data=None):

        if status is None:
            status = name

        if data is None:
            data = {}

        area = nandy_mysql.Area(name=name, status=status, updated=updated, data=data)
        self.nandy_data.mysql.session.add(area)
        self.nandy_data.mysql.session.commit()

        return area

    def sample_template(self, name, kind, data=None):

        if data is None:
            data = {}

        template = nandy_mysql.Template(name=name, kind=kind, data=data)
        self.nandy_data.mysql.session.add(template)
        self.nandy_data.mysql.session.commit()

        return template

    def sample_chore(self, person, name="Unit", status="started", created=7, updated=8, data=None, tasks=None):

        if data is None:
            data = {}

        base = {
            "text": "chore it",
            "language": "en-us"
        }

        base.update(data)

        if tasks is not None:
            base["tasks"] = tasks

        chore = nandy_mysql.Chore(
            person_id=self.sample_person(person).person_id,
            name=name,
            status=status,
            created=created,
            updated=updated,
            data=base
        )

        self.nandy_data.mysql.session.add(chore)
        self.nandy_data.mysql.session.commit()

        return chore

    def sample_act(self, person, name="Unit", value="positive", created=7, data=None):

        if data is None:
            data = {}

        act = nandy_mysql.Act(
            person_id=self.sample_person(person).person_id,
            name=name,
            value=value,
            created=created,
            data=data
        )
        self.nandy_data.mysql.session.add(act)
        self.nandy_data.mysql.session.commit()

        return act

    # Person

    def test_person_create(self):

        created = self.nandy_data.person_create({
            "name": "unit",
            "email": "test",
        })
        self.assertEqual(created.name, "unit")
        self.assertEqual(created.email, "test")

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Person).one()
        self.assertEqual(queried.name, "unit")
        self.assertEqual(queried.email, "test")

    def test_person_list(self):

        self.sample_person("unit")
        self.sample_person("test")

        persons = self.nandy_data.person_list()
        self.assertEqual(persons[0].name, "test")
        self.assertEqual(persons[1].name, "unit")
        
        persons = self.nandy_data.person_list({"name": "unit"})
        self.assertEqual(persons[0].name, "unit")
        
    def test_person_retrieve(self):

        sample = self.sample_person("unit", "test")

        retrieved = self.nandy_data.person_retrieve(sample.person_id)
        self.assertEqual(retrieved.name, "unit")

    def test_person_update(self):

        sample = self.sample_person("unit", "test")

        self.nandy_data.person_update(sample.person_id, {"email": "testy"})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Person).one()
        self.assertEqual(queried.email, "testy")

    def test_person_delete(self):

        sample = self.sample_person("unit", "test")

        self.assertEqual(self.nandy_data.person_delete(sample.person_id), 1)
        self.assertEqual(len(self.nandy_data.mysql.session.query(nandy_mysql.Person).all()), 0)

    # Area

    def test_area_create(self):

        created = self.nandy_data.area_create({
            "name": "unit",
            "status": "test",
            "updated": 7,
            "data": {"a": 1}
        })
        self.assertEqual(created.name, "unit")
        self.assertEqual(created.status, "test")
        self.assertEqual(created.updated, 7)
        self.assertEqual(created.data, {"a": 1})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Area).one()
        self.assertEqual(queried.name, "unit")
        self.assertEqual(queried.status, "test")
        self.assertEqual(queried.updated, 7)
        self.assertEqual(queried.data, {"a": 1})

    def test_area_list(self):

        self.sample_area("unit")
        self.sample_area("test")

        areas = self.nandy_data.area_list()
        self.assertEqual(areas[0].name, "test")
        self.assertEqual(areas[1].name, "unit")
        
        areas = self.nandy_data.area_list({"name": "unit"})
        self.assertEqual(areas[0].name, "unit")
        
    def test_area_retrieve(self):

        sample = self.sample_area(name="unit", status="test", updated=7, data={"a": 1})

        retrieved = self.nandy_data.area_retrieve(sample.area_id)
        self.assertEqual(retrieved.name, "unit")
        self.assertEqual(retrieved.data, {"a": 1})

    def test_area_update(self):

        sample = self.sample_area(name="unit", status="test")

        self.nandy_data.area_update(sample.area_id, {"status": "testy"})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Area).one()
        self.assertEqual(queried.status, "testy")

    @unittest.mock.patch("nandy_data.time.time")
    def test_area_status(self, mock_time):

        mock_time.return_value = 7

        person = self.sample_person("kid")
        area = self.sample_area(
            name="changing", 
            status="test", 
            updated=7, 
            data={
                "statuses": [
                    {
                        "value": "test",
                        "chore": {
                            "person": "kid",
                            "name": 'nope',
                            "node": "test",
                            "text": "chore it",
                            "language": "en-us",
                            "tasks": [
                                {
                                    "text": "do it"
                                }
                            ]
                        }
                    },
                    {
                        "value": "unit",
                        "chore": {
                            "person": "kid",
                            "name": 'yep',
                            "node": "test",
                            "text": "chore it",
                            "language": "en-us",
                            "tasks": [
                                {
                                    "text": "do it"
                                }
                            ]
                        }
                    }
                ]
            }
        )
        self.nandy_data.mysql.session.add(area)
        self.nandy_data.mysql.session.commit()

        self.assertFalse(self.nandy_data.area_status(area, "test"))
        self.assertEqual(len(self.nandy_data.graphite.sender.messages), 0)

        self.assertTrue(self.nandy_data.area_status(area, "unit"))

        self.assertEqual(area.status, "unit")
        self.assertEqual(area.updated, 7)

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Area).one()
        self.assertEqual(updated.status, "unit")
        self.assertEqual(updated.updated, 7)

        chore = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(chore.name, "yep")

        self.assertEqual(self.nandy_data.graphite.sender.messages, [{
                "name": "area.changing.status.test",
                "value": 0,
                "timestamp": 7
            },
            {
                "name": "area.changing.status.unit",
                "value": 1,
                "timestamp": 7
            }
        ])

    def test_area_delete(self):

        sample = self.sample_area("unit")

        self.assertEqual(self.nandy_data.area_delete(sample.area_id), 1)
        self.assertEqual(len(self.nandy_data.mysql.session.query(nandy_mysql.Area).all()), 0)

    # Template

    def test_template_create(self):

        created = self.nandy_data.template_create({
            "name": "unit",
            "kind": "chore",
            "data": {"a": 1}
        })
        self.assertEqual(created.name, "unit")
        self.assertEqual(created.kind, "chore")
        self.assertEqual(created.data, {"a": 1})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Template).one()
        self.assertEqual(queried.name, "unit")
        self.assertEqual(queried.kind, "chore")
        self.assertEqual(queried.data, {"a": 1})

    def test_template_list(self):

        self.sample_template(name="unit", kind="chore")
        self.sample_template(name="test", kind="act")

        templates = self.nandy_data.template_list()
        self.assertEqual(templates[0].name, "test")
        self.assertEqual(templates[1].name, "unit")
        
        templates = self.nandy_data.template_list({"name": "unit"})
        self.assertEqual(templates[0].name, "unit")
        
    def test_template_retrieve(self):

        sample = self.sample_template(name="unit", kind="chore", data={"a": 1})

        retrieved = self.nandy_data.template_retrieve(sample.template_id)
        self.assertEqual(retrieved.name, "unit")
        self.assertEqual(retrieved.data, {"a": 1})

    def test_template_update(self):

        sample = self.sample_template(name="unit", kind="chore")

        self.nandy_data.template_update(sample.template_id, {"kind": "act"})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Template).one()
        self.assertEqual(queried.kind, "act")

    def test_template_delete(self):

        sample = self.sample_template(name="unit", kind="chore")

        self.assertEqual(self.nandy_data.template_delete(sample.template_id), 1)
        self.assertEqual(len(self.nandy_data.mysql.session.query(nandy_mysql.Template).all()), 0)

    # Speak

    @unittest.mock.patch("nandy_data.time.time")
    def test_speak_chore(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", data={"node": "unit", "language": "test"})

        self.nandy_data.speak_chore("hi", chore)

        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "node": "unit",
            "text": "kid, hi",
            "language": "test"
        })
        self.assertEqual(dict(chore.data)["notified"], 7)
        self.assertEqual(dict(chore.data)["updated"], 7)

    @unittest.mock.patch("nandy_data.time.time")
    def test_speak_task(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", data={"node": "unit", "language": "test"}, tasks=[{}])

        self.nandy_data.speak_task("hi", chore.data["tasks"][0], chore)

        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "node": "unit",
            "text": "kid, hi",
            "language": "test"
        })
        self.assertEqual(dict(chore.data)["tasks"][0]["notified"], 7)
        self.assertEqual(dict(chore.data)["notified"], 7)
        self.assertEqual(dict(chore.data)["updated"], 7)

    # Remind

    @unittest.mock.patch("nandy_data.time.time")
    def test_remind(self, mock_time):

        mock_time.return_value = 7

        self.assertFalse(self.nandy_data.remind({
            "start": 1,
            "delay": 7
        }))

        self.assertFalse(self.nandy_data.remind({
            "paused": True
        }))

        self.assertTrue(self.nandy_data.remind({
            "interval": 5,
            "notified": 1
        }))

        self.assertFalse(self.nandy_data.remind({
            "interval": 5,
            "notified": 2
        }))

    @unittest.mock.patch("nandy_data.time.time")
    def test_remind_task(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", tasks=[
            {
                "start": 0,
                "end": 0,
                "text": "no it",
                "interval": 5,
                "notified": 0
            },
            {
                "start": 0,
                "text": "do it",
                "interval": 5,
                "notified": 0
            },
            {
                "start": 0,
                "text": "to it",
                "interval": 5,
                "notified": 0
            }
        ])

        self.nandy_data.mysql.session.add(chore)
        self.nandy_data.mysql.session.commit()

        self.nandy_data.remind_task(chore)
        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 0,
                    "end": 0,
                    "text": "no it",
                    "interval": 5,
                    "notified": 0
                },
                {
                    "start": 0,
                    "text": "do it",
                    "interval": 5,
                    "notified": 7
                },
                {
                    "start": 0,
                    "text": "to it",
                    "interval": 5,
                    "notified": 0
                }
            ]
        })
        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, please do it",
            "language": "en-us"
        })

    @unittest.mock.patch("nandy_data.time.time")
    def test_remind_chore(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", data={
            "interval": 5,
            "notified": 0,
            "tasks": [
                {
                    "start": 0,
                    "text": "do it",
                    "interval": 5,
                    "notified": 0
                }
            ]
        })

        self.nandy_data.remind_chore()
        queried = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(queried.data), {
            "text": "chore it",
            "language": "en-us",
            "interval": 5,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 0,
                    "text": "do it",
                    "interval": 5,
                    "notified": 7
                }
            ]
        })
        self.assertEqual(len(self.nandy_data.speech.redis.messages), 2)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you still have to chore it",
            "language": "en-us"
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, please do it",
            "language": "en-us"
        })

    # Chore

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_create(self, mock_time):

        mock_time.return_value = 7

        person = self.sample_person("kid")

        created = self.nandy_data.chore_create(template={
            "person": "kid",
            "name": 'Unit',
            "node": "test",
            "text": "chore it",
            "language": "en-us",
            "tasks": [
                {
                    "text": "do it"
                }
            ]
        })
        self.nandy_data.mysql.session.add(created)
        self.nandy_data.mysql.session.commit()

        self.assertEqual(created.person_id, person.person_id)
        self.assertEqual(created.name, "Unit")
        self.assertEqual(created.status, "started")
        self.assertEqual(created.created, 7)
        self.assertEqual(created.updated, 7)
        self.assertEqual(created.data, {
            "person": "kid",
            "name": 'Unit',
            "node": "test",
            "text": "chore it",
            "language": "en-us",
            "start": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "id": 0,
                    "text": "do it",
                    "start": 7,
                    "notified": 7
                }
            ]
        })

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(queried.person_id, person.person_id)
        self.assertEqual(queried.name, "Unit")
        self.assertEqual(queried.status, "started")
        self.assertEqual(queried.created, 7)
        self.assertEqual(queried.updated, 7)
        self.assertEqual(queried.data, {
            "person": "kid",
            "name": 'Unit',
            "node": "test",
            "text": "chore it",
            "language": "en-us",
            "start": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "id": 0,
                    "text": "do it",
                    "start": 7,
                    "notified": 7
                }
            ]
        })
 
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "node": "test",
            "text": "kid, time to chore it",
            "language": "en-us"
        })

        # No template or tasks

        fielded = self.nandy_data.chore_create(fields={
            "person_id": person.person_id,
            "name": 'Test',
            "data": {
                "node": "test",
                "text": "chore it"
            }
        })
        self.nandy_data.mysql.session.add(fielded)
        self.nandy_data.mysql.session.commit()

        self.assertEqual(fielded.person_id, person.person_id)
        self.assertEqual(fielded.name, "Test")
        self.assertEqual(fielded.status, "started")
        self.assertEqual(fielded.created, 7)
        self.assertEqual(fielded.updated, 7)
        self.assertEqual(fielded.data, {
            "node": "test",
            "text": "chore it",
            "language": "en-us",
            "start": 7,
            "notified": 7,
            "updated": 7
        })

    def test_chore_list(self):

        self.sample_chore(person="unit", name="Unit", created=7)
        self.sample_chore(person="test", name="Test", created=8)

        chores = self.nandy_data.chore_list()
        self.assertEqual(chores[0].name, "Test")
        self.assertEqual(chores[1].name, "Unit")
        
        chores = self.nandy_data.chore_list({"name": "Unit"})
        self.assertEqual(chores[0].name, "Unit")

    def test_chore_retrieve(self):

        sample = self.sample_chore(person="unit", name="Unit", data={
            "language": "en-us",
            "text": "Test"
        })

        retrieved = self.nandy_data.chore_retrieve(sample.chore_id)
        self.assertEqual(sample.name, "Unit")
        self.assertEqual(dict(sample.data), {
            "language": "en-us",
            "text": "Test"
        })

    def test_chore_update(self):

        sample = self.sample_chore(person="unit", name="Test")

        self.nandy_data.chore_update(sample.chore_id, {"name": "Unit"})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(queried.name, "Unit")

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_check(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Test", data={"start": 1})

        self.nandy_data.chore_check(chore)

        chore.data["tasks"] = [
            {
                "id": 0,
                "start": 0
            },
            {
                "id": 1,
                "text": "wait it",
                "paused": True
            },
            {
                "id": 2,
                "text": "do it"
            }
        ]
        self.nandy_data.chore_check(chore)

        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "tasks": [
                {
                    "id": 0,
                    "start": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True
                },
                {
                    "id": 2,
                    "text": "do it"
                }
            ]
        })

        chore.data["tasks"][0]["end"] = 0

        self.nandy_data.chore_check(chore)

        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7
                },
                {
                    "id": 2,
                    "text": "do it"
                }
            ]
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do not have to wait it yet",
            "language": "en-us"
        })

        chore.data["tasks"][1]["end"] = 0

        self.nandy_data.chore_check(chore)

        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "id": 0,
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7,
                    "end": 0
                },
                {
                    "id": 2,
                    "text": "do it",
                    "start": 7,
                    "notified": 7
                }
            ]
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, please do it",
            "language": "en-us"
        })

        chore.data["tasks"][2]["end"] = 0

        self.nandy_data.chore_check(chore)

        self.assertEqual(chore.status, "ended")
        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "end": 7,
            "tasks": [
                {
                    "id": 0,   
                    "start": 0,
                    "end": 0
                },
                {
                    "id": 1,
                    "text": "wait it",
                    "paused": True,
                    "start": 7,
                    "notified": 7,
                    "end": 0
                },
                {
                    "id": 2,   
                    "text": "do it",
                    "start": 7,
                    "notified": 7,
                    "end": 0
                }
            ]
        })

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_next(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", data={"start": 1}, tasks=[
            {
                "start": 2,                        
                "text": "do it"
            }
        ])

        self.assertTrue(self.nandy_data.chore_next(chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                }
            ]
        })

        self.assertFalse(self.nandy_data.chore_next(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_pause(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", data={"start": 1})

        self.assertTrue(self.nandy_data.chore_pause(chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": True
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do not have to chore it yet",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.chore_pause(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_unpause(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", data={"start": 1, "paused": True})

        self.assertTrue(self.nandy_data.chore_unpause(chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": False
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do have to chore it now",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.chore_unpause(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_skip(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", data={"start": 1})

        self.assertTrue(self.nandy_data.chore_skip(chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(updated.status, "ended")
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "end": 7,
            "skipped": True
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do not have to chore it",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.chore_skip(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_unskip(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", status="ended", data={
            "start": 1, 
            "end": 7, 
            "skipped": True
        })

        self.assertTrue(self.nandy_data.chore_unskip(chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(updated.status, "started")
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "skipped": False
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do have to chore it",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.chore_unskip(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_complete(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", data={"start": 1})

        self.assertTrue(self.nandy_data.chore_complete(chore))

        self.assertEqual(chore.status, "ended")
        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "end": 7
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, thank you. You did chore it",
            "language": "en-us"
        })

        self.assertEqual(len(self.nandy_data.graphite.sender.messages), 1)
        self.assertEqual(self.nandy_data.graphite.sender.messages[0], {
            "name": "person.kid.chore.chore_it.duration",
            "value": 6,
            "timestamp": 1
        })

        self.assertFalse(self.nandy_data.chore_complete(chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_chore_incomplete(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", name="Unit", status="ended", data={
            "start": 1, 
            "end": 1
        })

        self.assertTrue(self.nandy_data.chore_incomplete(chore))

        self.assertEqual(chore.status, "started")
        self.assertEqual(dict(chore.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, I'm sorry but you did not chore it yet",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.chore_incomplete(chore))

    def test_chore_delete(self):

        sample = self.sample_chore(person="kid")

        self.assertEqual(self.nandy_data.chore_delete(sample.chore_id), 1)
        self.assertEqual(len(self.nandy_data.mysql.session.query(nandy_mysql.Chore).all()), 0)

    # Task

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_pause(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", tasks=[{"text": "do it"}])

        self.assertTrue(self.nandy_data.task_pause(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "notified": 7,
                    "text": "do it",
                    "paused": True
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do not have to do it yet",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.task_pause(chore.data["tasks"][0], chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_unpause(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", tasks=[{"text": "do it", "paused": True}])

        self.assertTrue(self.nandy_data.task_unpause(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "notified": 7,
                    "text": "do it",
                    "paused": False
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 1)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do have to do it now",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.task_unpause(chore.data["tasks"][0], chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_skip(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", data={"start": 1}, tasks=[{"text": "do it"}])

        self.assertTrue(self.nandy_data.task_skip(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 7,
                    "end": 7,
                    "notified": 7,
                    "text": "do it",
                    "skipped": True
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 2)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do not have to do it",
            "language": "en-us"
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, thank you. You did chore it",
            "language": "en-us"
        })

        self.assertEqual(len(self.nandy_data.graphite.sender.messages), 1)
        self.assertEqual(self.nandy_data.graphite.sender.messages[0], {
            "name": "person.kid.chore.chore_it.duration",
            "value": 6,
            "timestamp": 1
        })

        self.assertFalse(self.nandy_data.task_skip(chore.data["tasks"][0], chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_unskip(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", status="ended", data={"start": 1, "end": 1}, tasks=[{
            "text": "do it", "end": 1, "skipped": True
        }])

        self.assertTrue(self.nandy_data.task_unskip(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(updated.status, "started")
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "notified": 7,
                    "text": "do it",
                    "skipped": False
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 2)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you do have to do it",
            "language": "en-us"
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, I'm sorry but you did not chore it yet",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.task_unskip(chore.data["tasks"][0], chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_complete(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", data={"start": 1}, tasks=[{"text": "do it"}])

        self.assertTrue(self.nandy_data.task_complete(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(updated.status, "ended")
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 7,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 2)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, you did do it",
            "language": "en-us"
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, thank you. You did chore it",
            "language": "en-us"
        })

        self.assertEqual(len(self.nandy_data.graphite.sender.messages), 2)
        self.assertEqual(self.nandy_data.graphite.sender.messages[0], {
            "name": "person.kid.chore.chore_it.task.do_it.duration",
            "value": 0,
            "timestamp": 7
        })
        self.assertEqual(self.nandy_data.graphite.sender.messages[1], {
            "name": "person.kid.chore.chore_it.duration",
            "value": 6,
            "timestamp": 1
        })

        self.assertFalse(self.nandy_data.task_complete(chore.data["tasks"][0], chore))

    @unittest.mock.patch("nandy_data.time.time")
    def test_task_incomplete(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample_chore(person="kid", status="ended", data={"start": 1, "end": 1}, tasks=[{
            "text": "do it", "end": 7
        }])

        self.assertTrue(self.nandy_data.task_incomplete(chore.data["tasks"][0], chore))

        updated = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(updated.status, "started")
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "notified": 7,
                    "text": "do it"
                }
            ]
        })

        self.assertEqual(len(self.nandy_data.speech.redis.messages), 2)
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[0]["data"]), {
            "timestamp": 7,
            "text": "kid, I'm sorry but you did not do it yet",
            "language": "en-us"
        })
        self.assertEqual(json.loads(self.nandy_data.speech.redis.messages[1]["data"]), {
            "timestamp": 7,
            "text": "kid, I'm sorry but you did not chore it yet",
            "language": "en-us"
        })

        self.assertFalse(self.nandy_data.task_incomplete(chore.data["tasks"][0], chore))

    # Act

    @unittest.mock.patch("nandy_data.time.time")
    def test_act_create(self, mock_time):

        mock_time.return_value = 7

        person = self.sample_person("unit")

        created = self.nandy_data.act_create(template={
            "person": "unit",
            "name": 'Unit',
            "value": "positive",
            "chore": {
                "name": "Test",
                "text": "chore it",
                "node": "bump"
            }
        })
        self.nandy_data.mysql.session.add(created)
        self.nandy_data.mysql.session.commit()

        self.assertEqual(created.person_id, person.person_id)
        self.assertEqual(created.name, "Unit")
        self.assertEqual(created.created, 7)
        self.assertEqual(created.value, "positive")
        self.assertEqual(created.data, {
            "person": "unit",
            "name": 'Unit',
            "value": "positive",
            "chore": {
                "name": "Test",
                "text": "chore it",
                "node": "bump"
            }
        })

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Act).one()
        self.assertEqual(queried.person_id, person.person_id)
        self.assertEqual(queried.name, "Unit")
        self.assertEqual(queried.value, "positive")
        self.assertEqual(queried.created, 7)
        self.assertEqual(queried.data, {
            "person": "unit",
            "name": 'Unit',
            "value": "positive",
            "chore": {
                "name": "Test",
                "text": "chore it",
                "node": "bump"
            }
        })

        chore = self.nandy_data.mysql.session.query(nandy_mysql.Chore).one()
        self.assertEqual(chore.person_id, person.person_id)
        self.assertEqual(chore.name, "Test")

        fielded = self.nandy_data.act_create(fields={
            "person_id": person.person_id,
            "name": 'Unit',
            "value": "positive",
            "data": {}
        })
        self.nandy_data.mysql.session.add(fielded)
        self.nandy_data.mysql.session.commit()

        self.assertEqual(fielded.person_id, person.person_id)
        self.assertEqual(fielded.name, "Unit")
        self.assertEqual(fielded.created, 7)
        self.assertEqual(fielded.value, "positive")

    def test_act_list(self):

        self.sample_act(person="unit", name="Unit", created=7)
        self.sample_act(person="test", name="Test", created=8)

        acts = self.nandy_data.act_list()
        self.assertEqual(acts[0].name, "Test")
        self.assertEqual(acts[1].name, "Unit")
        
        acts = self.nandy_data.act_list({"name": "Unit"})
        self.assertEqual(acts[0].name, "Unit")

    def test_act_retrieve(self):

        sample = self.sample_act(person="kid", name='Unit', value="positive", created=7, data={"a": 1})

        retrieved = self.nandy_data.act_retrieve(sample.act_id)
        self.assertEqual(retrieved.name, "Unit")

    def test_act_update(self):

        sample = self.sample_act(person="kid", name='Unit')

        self.nandy_data.act_update(sample.act_id, {"name": "Test"})

        queried = self.nandy_data.mysql.session.query(nandy_mysql.Act).one()
        self.assertEqual(queried.name, "Test")

    def test_act_delete(self):

        sample = self.sample_act(person="kid", name='Unit')

        self.assertEqual(self.nandy_data.act_delete(sample.act_id), 1)
        self.assertEqual(len(self.nandy_data.mysql.session.query(nandy_mysql.Act).all()), 0)
