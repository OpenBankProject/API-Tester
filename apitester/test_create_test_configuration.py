from django.test import TestCase
from runtests.models import TestConfiguration

class NewTestConfigurationTestCase(TestCase):
    '''
        Create a new (empty) TestConfiguration model.
    '''
    def test_create_test_configuration(self):
        test_config = TestConfiguration(owner_id=1, name='Fred', 
                                        api_version='3.1.0')
        test_config.save()
        return test_config
