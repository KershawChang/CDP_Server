import os.path
import tornado.ioloop
import tornado.web
from os import listdir
from os.path import isdir, join
import json

testDataPath = os.path.join(os.getcwd(), "static/testData/")
tests = {};

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", title="CDP Test", tests=tests)

class ResultHandler(tornado.web.RequestHandler):
    def get(self, data):
        selectedKeys = data.split("+");
        selectedTests = [];
        for k in selectedKeys:
            selectedTests.append(tests[k])

        print selectedTests
        sites = ["CNN", "Twitter", "Wired", "nytimes", "500px"]
        dataTypes = [{"text": "Hero Element", "value": "HeroElementResult"},
                     {"text": "Trackers", "value": "TrackingResult"}]
        TimingDataStr = ['Start Time (ms)', 'End Time (ms)', 'Time to Load (ms)', 'Time to First Byte (ms)']
        self.render("result_template.html", selectedTests=selectedTests, sites=sites, dataTypes=dataTypes, TimingDataStr=TimingDataStr)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
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

    app =Application()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()