import sys
import unittest2

import pyspatialite
import pysqlite2


#TEST_DB = 'sqlite+pysqlite:///:memory:'
TEST_DB = 'postgres://gis:gis@localhost/gis'


class TestSpatialite(unittest2.TestCase):
    def setUp(self):
        #self.old_module = sys.modules['pysqlite2']
        #sys.modules['pysqlite2'] = pyspatialite
        pass

    def _get_session(self):
        from ichnaea.db import MeasureDB
        return MeasureDB(TEST_DB).session()

    def tearDown(self):
        #sys.modules['pysqlite2'] = self.old_module
        session = self._get_session()
        session.execute('delete from measure')
        session.execute('delete from cell')
        session.commit()
