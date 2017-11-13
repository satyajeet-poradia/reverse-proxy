import datetime

from peewee import *

"""
Initialize Database
"""
DATABASE = SqliteDatabase('nextbus.sqlite')


"""
Create a database schema
"""
class Details(Model):
    url = CharField()
    time = FloatField()
    dt = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = DATABASE

"""
Inititalize database connection and create tables
"""
def initialize():
    DATABASE.connect()
    DATABASE.create_tables([Details], safe=True)
    DATABASE.close()