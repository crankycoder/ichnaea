from webtest import TestApp
from ichnaea import application
from ichnaea.tests.support import TestSpatialite


class TestIchnaea(TestSpatialite):
    def test_ok(self):
        app = TestApp(application)
        app.get('/', status=404)
