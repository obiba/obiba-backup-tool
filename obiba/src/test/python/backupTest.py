import unittest
import yaml


class BackupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print "BackupTest.setUpClass"

    def testYaml(self):
        stream = open("../resources/test.yml", 'r')
        config = yaml.load(stream)
        print config['projects']




