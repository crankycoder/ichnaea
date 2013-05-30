import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column, Index
from sqlalchemy import DateTime, Integer, LargeBinary, SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from colander.iso8601 import UTC


_Model = declarative_base()


RADIO_TYPE = {
    'gsm': 0,
    'cdma': 1,
    'umts': 2,
    'lte': 3,
}
RADIO_TYPE_KEYS = list(RADIO_TYPE.keys())


class Cell(_Model):
    __tablename__ = 'cell'
    __table_args__ = (
        Index('cell_idx', 'radio', 'mcc', 'mnc', 'lac', 'cid'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
        }
    )

    id = Column(Integer, primary_key=True)

    # lat/lon * decimaljson.FACTOR
    _position = Column(Geometry('POINT'))

    # mapped via RADIO_TYPE
    radio = Column(SmallInteger)
    # int in the range 0-1000
    mcc = Column(SmallInteger)
    # int in the range 0-1000 for gsm
    # int in the range 0-32767 for cdma (system id)
    mnc = Column(SmallInteger)
    lac = Column(Integer)
    cid = Column(Integer)
    # int in the range 0-511
    psc = Column(SmallInteger)
    range = Column(Integer)

    def _get_pos(self):
        shape = to_shape(self._position)
        # XXX floats :S
        return shape.x, shape.y

    def _set_pos(self, value):
        self._position = 'POINT (%.7f %.7f)' % (value[0], value[1])

    position = property(_get_pos, _set_pos)


cell_table = Cell.__table__


class Measure(_Model):
    __tablename__ = 'measure'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8',
        'mysql_row_format': 'compressed',
        'mysql_key_block_size': '4',
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    _position = Column(Geometry('POINT'))
    _time = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    accuracy = Column(SmallInteger)
    altitude = Column(SmallInteger)
    altitude_accuracy = Column(SmallInteger)
    radio = Column(SmallInteger)  # mapped via RADIO_TYPE
    # json blobs
    cell = Column(LargeBinary)
    wifi = Column(LargeBinary)

    def _get_pos(self):
        shape = to_shape(self._position)
        return shape.x, shape.y

    def _set_pos(self, value):
        self._position = 'POINT (%.7f %.7f)' % (value[0], value[1])

    position = property(_get_pos, _set_pos)

    # postgres stores naive dates without timezones, but they are UTC
    # here we're removing the tzinfo before storage and putting it
    # back when accessing the value
    def _get_time(self):
        return self._time.replace(tzinfo=UTC)

    def _set_time(self, value):
        value = value.replace(tzinfo=None)
        self._time = value

    time = property(_get_time, _set_time)


measure_table = Measure.__table__


class BaseDB(object):

    def __init__(self, sqluri):
        options = dict(pool_recycle=3600, pool_size=10, pool_timeout=10)
        scheme = sqluri.split(':')[0]
        if scheme in ('sqlite+pysqlite', 'sqlite', 'postgres'):
            del options['pool_size']
            del options['pool_timeout']
        self.engine = create_engine(sqluri, **options)
        self.session_factory = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False)

    def session(self):
        return self.session_factory()


class CellDB(BaseDB):

    def __init__(self, sqluri):
        super(CellDB, self).__init__(sqluri)
        cell_table.metadata.bind = self.engine
        cell_table.create(checkfirst=True)


class MeasureDB(BaseDB):

    def __init__(self, sqluri):
        super(MeasureDB, self).__init__(sqluri)
        self.sqluri = sqluri
        measure_table.metadata.bind = self.engine
        measure_table.create(checkfirst=True)
