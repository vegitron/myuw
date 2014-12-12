# From https://github.com/Victory/django-travis-saucelabs
import os
import sys

from unittest2 import skipIf

try:
    from selenium import webdriver
    has_selenium = True
except Exception as ex:
    has_selenium = False

from django.test import LiveServerTestCase

RUN_LOCAL = os.environ.get('RUN_TESTS_LOCAL') == 'True'
RUN_SELENIUM = os.environ.get('RUN_SELENIUM') == 'True'


if RUN_LOCAL:
    # could add Chrome, PhantomJS etc... here
    browsers = ['Firefox']
else:
    try:
        from sauceclient import SauceClient
        USERNAME = os.environ.get('SAUCE_USERNAME')
        ACCESS_KEY = os.environ.get('SAUCE_ACCESS_KEY')
        sauce = SauceClient(USERNAME, ACCESS_KEY)
    except Exception as ex:
        pass

    if has_selenium:
        iphone = webdriver.DesiredCapabilities.IPHONE
        iphone['platform'] = "OS X 10.9"
        iphone['version'] = "8.1"
        iphone['browserName'] = "iPhone"
        iphone['device-orientation'] = 'portrait'

        ipad = webdriver.DesiredCapabilities.IPAD
        ipad['platform'] = "OS X 10.9"
        ipad['version'] = "8.1"
        ipad['browserName'] = "iPad"
        ipad['device-orientation'] = 'portrait'

        android_nexus = webdriver.DesiredCapabilities.ANDROID
        android_nexus['platform'] = "Linux"
        android_nexus['version'] = "4.4"
        android_nexus['deviceName'] = "Google Nexus 7 HD Emulator"
        android_nexus['device-orientation'] = 'portrait'

        browsers = [
            iphone,
            ipad,
            android_nexus,
            {"platform": "Mac OS X 10.9",
             "browserName": "chrome",
             "version": "35"},
            {"platform": "Windows 8.1",
             "browserName": "internet explorer",
             "version": "11"},
            {"platform": "Linux",
             "browserName": "firefox",
             "version": "29"}]
    else:
        browsers = []

def on_platforms(platforms, local):
    if local:
        def decorator(base_class):
            module = sys.modules[base_class.__module__].__dict__
            for i, platform in enumerate(platforms):
                d = dict(base_class.__dict__)
                d['browser'] = platform
                name = "%s_%s" % (base_class.__name__, i + 1)
                module[name] = type(name, (base_class,), d)
            pass
        return decorator

    def decorator(base_class):
        module = sys.modules[base_class.__module__].__dict__
        for i, platform in enumerate(platforms):
            d = dict(base_class.__dict__)
            d['desired_capabilities'] = platform
            name = "%s_%s" % (base_class.__name__, i + 1)
            module[name] = type(name, (base_class,), d)
    return decorator


@on_platforms(browsers, RUN_LOCAL)
@skipIf(not RUN_SELENIUM, "Requires RUN_SELENIUM=True as an environment variable")
class HelloSauceTest(LiveServerTestCase):
    """
    Runs a test using travis-ci and saucelabs
    """

    def setUp(self):
        if RUN_LOCAL:
            self.setUpLocal()
        else:
            self.setUpSauce()

    def tearDown(self):
        if RUN_LOCAL:
            self.tearDownLocal()
        else:
            self.tearDownSauce()

    def setUpSauce(self):
        self.desired_capabilities['name'] = self.id()
        self.desired_capabilities['tunnel-identifier'] = \
            os.environ.get('TRAVIS_JOB_NUMBER', '')
        self.desired_capabilities['build'] = os.environ.get('TRAVIS_BUILD_NUMBER', '')
        self.desired_capabilities['tags'] = \
            [os.environ.get('TRAVIS_PYTHON_VERSION', ''), 'CI']

        print self.desired_capabilities

        sauce_url = "http://%s:%s@ondemand.saucelabs.com:80/wd/hub"
        self.driver = webdriver.Remote(
            desired_capabilities=self.desired_capabilities,
            command_executor=sauce_url % (USERNAME, ACCESS_KEY)
        )
        self.driver.implicitly_wait(5)

    def setUpLocal(self):
        self.driver = getattr(webdriver, self.browser)()
        self.driver.implicitly_wait(3)

    def tearDownLocal(self):
        self.driver.quit()

    def tearDownSauce(self):
        print("\nLink to your job: \n "
              "https://saucelabs.com/jobs/%s \n" % self.driver.session_id)
        try:
            if sys.exc_info() == (None, None, None):
                sauce.jobs.update_job(self.driver.session_id, passed=True)
            else:
                sauce.jobs.update_job(self.driver.session_id, passed=False)
        finally:
            self.driver.quit()

    def test_sauce(self):
        self.driver.get(self.live_server_url + '/mobile/landing/')
        self.assertEquals(self.driver.title, "MyUW Mobile Home")

