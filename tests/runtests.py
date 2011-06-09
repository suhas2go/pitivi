import glob
import os
import sys
import unittest
import tests

SKIP_FILES = ['common', 'runtests']  # They are not testsuites
#Those files need sample files, and therefore shoud not be tested
#when running distcheck
INTEGRATION_FILES = ['test_still_image', 'test_integration']


def gettestnames(which):
    if os.getenv("TEST_INTEGRATION"):
        return INTEGRATION_FILES
    else:
        SKIP_FILES.extend(INTEGRATION_FILES)

    if not which:
        dir = os.path.split(os.path.abspath(__file__))[0]
        which = [os.path.basename(p) for p in glob.glob('%s/test_*.py' % dir)]

    names = map(lambda x: x[:-3], which)
    for f in SKIP_FILES:
        if f in names:
            names.remove(f)
    return names

suite = unittest.TestSuite()
loader = unittest.TestLoader()

TEST_CASE = os.getenv("TESTCASE")

if TEST_CASE:
    suite.addTest(loader.loadTestsFromName(TEST_CASE))
    if not suite._tests:
        raise Exception("could not find test case %r" % TEST_CASE)
else:
    for name in gettestnames(sys.argv[1:]):
        suite.addTest(loader.loadTestsFromName(name))

descriptions = 1
verbosity = 1
if 'VERBOSE' in os.environ:
    descriptions = 2
    verbosity = 2
from pitivi.log import log
log.init('PITIVI_DEBUG', 1)

# Make available to configure.py the top level dir.
dir = os.path.dirname(os.path.abspath(__file__))
top_srcdir = os.path.split(dir)[0]
os.environ.setdefault('PITIVI_TOP_LEVEL_DIR', top_srcdir)

# Run the tests.
testRunner = unittest.TextTestRunner(descriptions=descriptions,
    verbosity=verbosity)
result = testRunner.run(suite)
if result.failures or result.errors:
    sys.exit(1)
