import os.path
import tornado.ioloop
import tornado.web
import tornado.options
from os import listdir
from os.path import isdir, join
import json
import sys
from tornado.log import enable_pretty_logging
enable_pretty_logging()

testDataDir = "static/testData/"
testDataPath = os.path.join(os.getcwd(), testDataDir)
testCategoryTable = {'tp': 'Tracking Protection',
                     'tabs': 'Active Tab Priority',
                     'honza_0830': 'Tailing test 0830',
                     'honza_0901': 'Tailing test 0901',
                     'bug1247843_tailing': 'favicon test'}
tests = {};
logPath = './server.log'

showTrackerCategory = ['tp', 'honza_0830', 'honza_0901']

interestPrefTable = {'tp':['privacy.trackingprotection.lower_network_priority',
                           'network.http.throttle.enable'],
                     'tabs':['network.http.active_tab_priority',
                             'network.http.throttle.enable'],
                     'honza_0830':['preference'],
                     'honza_0901':['preference'],
                     'bug1247843_tailing': ['network.http.tailing.enabled']}

class MainHandler(tornado.web.RequestHandler):
    def get(self, name):
        selectedCategory = name.replace('.html', '')
        if not selectedCategory:
            selectedCategory = 'tp'
        self.render("index2.html", testCategoryTable=testCategoryTable, selectedCategory=selectedCategory, tests=tests)

class StopHandler(tornado.web.RequestHandler):
    def get(self):
        tornado.ioloop.IOLoop.current().stop()

class LogHandler(tornado.web.RequestHandler):
    def get(self):
        with open(logPath, 'r') as f:
            data = f.readlines()
            for l in data:
                self.write('<p>' + l + '</p>')
            self.finish()

class ResultHandler(tornado.web.RequestHandler):
    def get(self, data):
        category = self.get_argument("category")
        selectedKeys = [self.get_argument("t1"), self.get_argument("t2")]
        selectedTests = [];
        for k in selectedKeys:
            selectedTests.append(tests[category][k])

        sites = ["CNN", "Twitter", "Wired", "nytimes", "500px"]
        dataTypes = [{"text": "Hero Element", "value": "HeroElementResult"}]
        if category in showTrackerCategory:
            dataTypes.append({"text": "Trackers", "value": "TrackingResult"})
        TimingDataStr = ['Start Time (ms)', 'End Time (ms)', 'Time to Load (ms)', 'Time to First Byte (ms)']
        prefList = interestPrefTable[category]
        self.render("dashboard_template.html", prefList=prefList, selectedTests=selectedTests, sites=sites, dataTypes=dataTypes, TimingDataStr=TimingDataStr)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/result/([^/]*)", ResultHandler),
                    (r"/stop", StopHandler),
                    (r"/log", LogHandler),
                    (r"/(.*)", MainHandler)]
        settings = {
            "template_path": os.path.join(os.getcwd(), "templates"),
            "static_path": os.path.join(os.getcwd(), "static")
        }

        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    for key in testCategoryTable:
        tests[key] = {}
        tmpPath = testDataPath + key + '/'
        if not os.path.isdir(tmpPath):
            print tmpPath + " is not existed!"
            continue

        dirs = [f for f in listdir(tmpPath) if isdir(join(tmpPath, f))]
        for d in dirs:
            summary = tmpPath + d + "/summary.json"
            with open(summary) as data_file:
                data = json.load(data_file)
                tests[key][d] = {'title': data['title'], 'path': 'testData/' + key + '/' + d + '/', 'category':key}
    for cat in tests:
        print cat
        for key in tests[cat]:
            print tests[cat][key]

    app = Application()
    app.listen(8888)
    args = sys.argv
    args.append("--log_file_prefix=./server.log")
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line(args)
    tornado.ioloop.IOLoop.current().start()



