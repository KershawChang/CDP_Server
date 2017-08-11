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
tests = {};
logPath = './server.log'

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", title="CDP Test", tests=tests)

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
        selectedKeys = [self.get_argument("t1"), self.get_argument("t2")]
        print selectedKeys
        selectedTests = [];
        for k in selectedKeys:
            selectedTests.append(tests[k])

        sites = ["CNN", "Twitter", "Wired", "nytimes", "500px"]
        dataTypes = [{"text": "Hero Element", "value": "HeroElementResult"},
                     {"text": "Trackers", "value": "TrackingResult"}]
        TimingDataStr = ['Start Time (ms)', 'End Time (ms)', 'Time to Load (ms)', 'Time to First Byte (ms)']
        self.render("dashboard_template.html", selectedTests=selectedTests, sites=sites, dataTypes=dataTypes, TimingDataStr=TimingDataStr)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    (r"/stop", StopHandler),
                    (r"/log", LogHandler),
                    (r"/result/([^/]*)", ResultHandler)]
        settings = {
            "template_path": os.path.join(os.getcwd(), "templates"),
            "static_path": os.path.join(os.getcwd(), "static")
        }

        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    dirs = [f for f in listdir(testDataPath) if isdir(join(testDataPath, f))]
    for d in dirs:
        summary = testDataPath + d + "/summary.json"
        with open(summary) as data_file:
            data = json.load(data_file)
            tests[d] = {'title': data['title'], 'path': 'testData/' + d + '/'}

    app = Application()
    app.listen(8888)
    args = sys.argv
    args.append("--log_file_prefix=./server.log")
    tornado.options.options.logging = "debug"
    tornado.options.parse_command_line(args)
    tornado.ioloop.IOLoop.current().start()