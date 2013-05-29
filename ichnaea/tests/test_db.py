from ichnaea.tests.support import TEST_DB
from ichnaea.tests.support import TestSpatialite


class TestCellDB(TestSpatialite):
    def tearDown(self):
        db = self._make_one()
        session = db.session()
        session.execute('delete from cell')
        session.commit()

    def _make_one(self):
        from ichnaea.db import CellDB
        return CellDB(TEST_DB)

    def test_constructor(self):
        db = self._make_one()
        self.assertEqual(db.engine.name, 'postgresql')

    def test_session(self):
        db = self._make_one()
        session = db.session()
        self.assertTrue(session.bind is db.engine)

    def test_table_creation(self):
        db = self._make_one()
        session = db.session()
        result = session.execute('select * from cell')
        self.assertTrue(result.first() is None)


class TestCell(TestSpatialite):
    def tearDown(self):
        session = self._get_session()
        session.execute('delete from cell')
        session.commit()

    def _make_one(self):
        from ichnaea.db import Cell
        return Cell()

    def _get_session(self):
        from ichnaea.db import CellDB
        return CellDB(TEST_DB).session()

    def test_constructor(self):
        cell = self._make_one()
        self.assertTrue(cell.id is None)

    def test_fields(self):
        cell = self._make_one()
        cell.position = 12345678., 23456789.
        cell.mcc = 100
        cell.mnc = 5
        cell.lac = 12345
        cell.cid = 234567

        session = self._get_session()
        session.add(cell)
        session.commit()

        result = session.query(cell.__class__).first()
        self.assertEqual(result.position, (12345678., 23456789.))
        self.assertEqual(result.mcc, 100)
        self.assertEqual(result.cid, 234567)


class TestMeasureDB(TestSpatialite):

    def _make_one(self):
        from ichnaea.db import MeasureDB
        return MeasureDB(TEST_DB)

    def tearDown(self):
        db = self._make_one()
        session = db.session()
        session.execute('delete from measure')
        session.commit()

    def test_constructor(self):
        db = self._make_one()
        self.assertEqual(db.engine.name, 'postgresql')

    def test_session(self):
        db = self._make_one()
        session = db.session()
        self.assertTrue(session.bind is db.engine)

    def test_table_creation(self):
        db = self._make_one()
        session = db.session()
        result = session.execute('select * from measure;')
        self.assertTrue(result.first() is None)


class TestMeasure(TestSpatialite):

    def _make_one(self):
        from ichnaea.db import Measure
        return Measure()

    def _get_session(self):
        from ichnaea.db import MeasureDB
        return MeasureDB(TEST_DB).session()

    def test_constructor(self):
        measure = self._make_one()
        self.assertTrue(measure.id is None)

    def test_fields(self):
        measure = self._make_one()
        measure.position = 12345678., 23456789.
        measure.cell = "[]"
        measure.wifi = "[]"

        session = self._get_session()
        session.add(measure)
        session.commit()

        result = session.query(measure.__class__).first()
        #self.assertEqual(result.id, 1)
        self.assertEqual(result.position, (12345678.0, 23456789.0))
        self.assertEqual(result.cell, "[]")
        self.assertEqual(result.wifi, "[]")
