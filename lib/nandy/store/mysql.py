import os

import pymysql
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.ext.mutable
import flask_jsontools
import sqlalchemy_jsonfield

class MySQL(object):
    """
    Main class for interacting with Nandy in MySQL
    """

    def __init__(self, host=None, port=None):

        self.engine = sqlalchemy.create_engine(f"mysql+pymysql://root@{host or os.environ['MYSQL_HOST']}:{port or os.environ['MYSQL_PORT']}/nandy")
        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()


Base = sqlalchemy.ext.declarative.declarative_base(cls=(flask_jsontools.JsonSerializableBase))


class Person(Base):

    __tablename__ = "person"
    
    person_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(64), nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String(128), nullable=False)

    sqlalchemy.schema.UniqueConstraint('name', name='label')
    sqlalchemy.schema.UniqueConstraint('email', name='email')

    def __repr__(self):
        return "<Person(name='%s')>" % (self.name)


class Area(Base):

    __tablename__ = "area"
    
    area_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)

    name = sqlalchemy.Column(sqlalchemy.String(64), nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String(32), nullable=False)
    updated = sqlalchemy.Column(sqlalchemy.Integer)
    data = sqlalchemy.Column(
        sqlalchemy.ext.mutable.MutableDict.as_mutable(
            sqlalchemy_jsonfield.JSONField(enforce_string=True,enforce_unicode=False)
        ), 
        nullable=False
    )

    sqlalchemy.schema.UniqueConstraint('name', name='label')

    def __repr__(self):
        return "<Area(name='%s')>" % (self.name)


class Template(Base):

    __tablename__ = "template"
    
    template_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(128), nullable=False)
    kind = sqlalchemy.Column(sqlalchemy.Enum("chore", "act"))
    data = sqlalchemy.Column(
        sqlalchemy.ext.mutable.MutableDict.as_mutable(
            sqlalchemy_jsonfield.JSONField(enforce_string=True,enforce_unicode=False)
        ), 
        nullable=False
    )

    sqlalchemy.schema.UniqueConstraint('name', 'kind', name='label')

    def __repr__(self):
        return "<Template(name='%s',kind='%s')>" % (self.name, self.kind)


class Chore(Base):

    __tablename__ = "chore"
    
    chore_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    person_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("person.person_id"), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    status = sqlalchemy.Column(sqlalchemy.Enum("started", "ended"))
    created = sqlalchemy.Column(sqlalchemy.Integer)
    updated = sqlalchemy.Column(sqlalchemy.Integer)
    data = sqlalchemy.Column(
        sqlalchemy.ext.mutable.MutableDict.as_mutable(
            sqlalchemy_jsonfield.JSONField(enforce_string=True,enforce_unicode=False)
        ), 
        nullable=False
    )

    person = sqlalchemy.orm.relationship("Person") 

    sqlalchemy.schema.UniqueConstraint('name', 'person_id', 'created', name='label')

    def __repr__(self):
        return "<Chore(name='%s',person='%s',created=%s)>" % (self.name, self.person.name, self.created)


class Act(Base):

    __tablename__ = "act"
    
    act_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    person_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("person.person_id"), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String(128), nullable=False)
    value = sqlalchemy.Column(sqlalchemy.Enum("positive", "negative"))
    created = sqlalchemy.Column(sqlalchemy.Integer)
    data = sqlalchemy.Column(
        sqlalchemy.ext.mutable.MutableDict.as_mutable(
            sqlalchemy_jsonfield.JSONField(enforce_string=True,enforce_unicode=False)
        ), 
        nullable=False
    )

    person = sqlalchemy.orm.relationship("Person") 

    sqlalchemy.schema.UniqueConstraint('name', 'person_id', 'created', name='label')

    def __repr__(self):
        return "<Act(name='%s',person='%s',created=%s)>" % (self.name, self.person.name, self.created)


def create_database():

    connection = pymysql.connect(host='mysql', user='root')

    try:

        with connection.cursor() as cursor:
            cursor.execute("DROP DATABASE IF EXISTS nandy")
            cursor.execute("CREATE DATABASE nandy")

        connection.commit()

    finally:

        connection.close()


class Sample:

    def __init__(self, session):

        self.session = session

    def person(self, name, email=None):

        if email is None:
            email = name

        person = Person(name=name, email=email)
        self.session.add(person)
        self.session.commit()

        return person

    def area(self, name, status=None, updated=7, data=None):

        if status is None:
            status = name

        if data is None:
            data = {}

        area = Area(name=name, status=status, updated=updated, data=data)
        self.session.add(area)
        self.session.commit()

        return area

    def template(self, name, kind, data=None):

        if data is None:
            data = {}

        template = Template(name=name, kind=kind, data=data)
        self.session.add(template)
        self.session.commit()

        return template

    def chore(self, person, name="Unit", status="started", created=7, updated=8, data=None, tasks=None):

        if data is None:
            data = {}

        base = {
            "text": "chore it",
            "language": "en-us"
        }

        base.update(data)

        if tasks is not None:
            base["tasks"] = tasks

        chore = Chore(
            person_id=self.person(person).person_id,
            name=name,
            status=status,
            created=created,
            updated=updated,
            data=base
        )

        self.session.add(chore)
        self.session.commit()

        return chore

    def act(self, person, name="Unit", value="positive", created=7, data=None):

        if data is None:
            data = {}

        act = Act(
            person_id=self.person(person).person_id,
            name=name,
            value=value,
            created=created,
            data=data
        )
        self.session.add(act)
        self.session.commit()

        return act
