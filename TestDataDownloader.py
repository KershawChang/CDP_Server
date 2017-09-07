import sys
import csv
import json
import urllib2
import os.path
import shutil

TimingDataStr = ['Start Time (ms)', 'End Time (ms)', 'Time to Load (ms)', 'Time to First Byte (ms)']

class ResourceData:
    def __init__(self):
        self.clear()

    def clear(self):
        self.HeroElementLoadData = []
        self.TrackingResourcesData = []


def combineSameData(data):
    result = {}
    for d in data:
        url = d[0]
        timeData = d[1]
        if url not in result:
            result[url] = {}
            result[url]['count'] = 0
            result[url]['timing'] = []
            result[url]['total'] = {}
            result[url]['avg'] = {}
            for timeString in TimingDataStr:
                result[url]['total'][timeString] = 0
                result[url]['avg'][timeString] = 0
        result[url]['count'] += 1
        result[url]['timing'].append(timeData)

    for key in result:
        for ele in result[key]['timing']:
            for timeString in TimingDataStr:
                result[key]['total'][timeString] += ele[timeString]

        for timeString in TimingDataStr:
            result[key]['avg'][timeString] = result[key]['total'][timeString] / result[key]['count']

    return result


def GetTimeingData(line):
    timing = {}
    for str in TimingDataStr:
        timing[str] = int(line[str])
    return timing

def ParseCSV(csvContent, TestData):
    #reader = csv.DictReader(csvContent)
    reader = csv.DictReader(open(csvContent))
    result = ResourceData()
    for row in reader:
        foundHeroElement = False
        for heroElement in TestData['HeroElement']:
            if heroElement == row['URL']:
                result.HeroElementLoadData.append((row['Host'] + row['URL'],GetTimeingData(row)))
                foundHeroElement = True

        if foundHeroElement:
            continue

        for domain in TestData['HeroElementDomain']:
            if domain == row['Host']:
                result.HeroElementLoadData.append((row['Host'] + row['URL'],GetTimeingData(row)))
                foundHeroElement = True

        if foundHeroElement:
            continue

        for trackingHost in TestData['TrackingResources']:
            if trackingHost in row['Host']:
                result.TrackingResourcesData.append((row['Host'],GetTimeingData(row)))

    return result


CDPTests = {
    'http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html':
        {'site': 'cnn',
         'HeroElement': ['/2017/07/19/health/gupta-mccain-glioblastoma/index.html',
                         '/cnnnext/dam/assets/170720033628-john-mccain-brain-tumor-diagnosis-gupta-dnt-ac-00014000-exlarge-169.jpg',
                         '/i/cnn/big/health/2017/07/20/john-mccain-brain-tumor-diagnosis-gupta-dnt-ac.cnn_1538305_ios_,440,650,840,1240,3000,5500,.mp4.csmil/segment1_1_av.ts?null=0'],
         'HeroElementDomain': [],
         'TrackingResources': ['static.chartbeat.com',
                               'amplifypixel.outbrain.com',
                               'cdn.krxd.net',
                               'www.googletagservices.com',
                               'pixel.quantserve.com',
                               'secure-us.imrworldwide.com',
                               'widgets.outbrain.com',
                               'b.scorecardresearch.com',
                               'connect.facebook.net']
        },
    'https://500px.com/popular':
        {'site': '500px',
         'HeroElement': ['/photo/221022345/q%3D80_h%3D300/v2?webp=true&sig=5ab75a11402bbc288addfef12b8046433231b1282271ff57a36c12d4105d4539',
                          '/photo/220967373/q%3D80_h%3D300/v2?webp=true&sig=15d6f878bae207eadc1e2ca416e2ab36b76d2b277c2e3b2ae2e369a29d628831',
                          '/photo/220998205/q%3D80_h%3D300/v2?webp=true&sig=9488c7e53bbf9f0cd4b05a0bda182f9fc1474f03d745a318adc9cb8da5ec68bb',
                          '/photo/220996255/q%3D80_h%3D300/v2?webp=true&sig=b57e5407eebe7433924f94492e8b8f7854d5fad0b883b522e26d6d37d8ce69c5',
                          '/photo/220985045/q%3D80_h%3D300/v2?webp=true&sig=590846a2755f457ab10225917566a59d1462b3ba6d545b498a5fc0b9fb05a32d',
                          '/photo/220979443/q%3D80_h%3D300/v2?webp=true&sig=625d0eb86e5b363f77f088a2c70ec32f99e32fb13b666200fbea575f6bb4ca51',
                          '/photo/220978109/q%3D80_h%3D300/v2?webp=true&sig=cd131f2853a08b6a1b3faf038a303c719aee79a6f573b451207caf81c85605e8',
                          '/popular'],
         'HeroElementDomain': ['drscdn.500px.org'],
         'TrackingResources': ['www.google-analytics.com',
                                'graph.facebook.com',
                                'js-agent.newrelic.com']
        },
    'https://twitter.com/bagder':
        {'site': 'twitter',
         'HeroElement': ['/media/DFMT5bvWsAAzh54.jpg',
                          '/profile_banners/14893620/1471436582/1500x500',
                          '/bagder'],
         'HeroElementDomain': ['pbs.twimg.com'],
         'TrackingResources': ['www.google-analytics.com',
                                'cm.g.doubleclick.net',
                                't.tellapart.com']
        },
    'https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/':
        {'site': 'wired',
         'HeroElement': ['/photos/59266febcfe0d93c47430337/master/w_289,c_limit/AmericanSpiesCover.jpg',
                          '/2017/03/mass-spying-isnt-just-intrusive-ineffective/'],
         'HeroElementDomain': [],
         'TrackingResources': ['s.skimresources.com',
                                'dpm.demdex.net',
                                'sb.scorecardresearch.com',
                                'odb.outbrain.com',
                                'graph.facebook.com',
                                'www.googletagservices.com',
                                'static.chartbeat.com',
                                'condenast.demdex.net']
        },
    'https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news':
        {'site': 'nytimes',
         'HeroElement': ['/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news',
                          '/images/2017/07/22/us/23minneapolis1/23minneapolis1-superJumbo.jpg'],
         'HeroElementDomain': [],
         'TrackingResources': ['contextual.media.net',
                                'www.googletagservices.com',
                                'connect.facebook.net',
                                'sb.scorecardresearch.com',
                                'cdn.krxd.net',
                                'www.google-analytics.com',
                                'pnytimes.chartbeat.net',
                                'www.googleadservices.com',
                                'sp.analytics.yahoo.com']
        }
}

AllTaskURL = "http://presto.xeon.tw/api/tasks"
'''AllTasks = [{"id":"170801_TX_4W","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_OFF.internet"},
            {"id":"170801_ZC_4X","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_ON.internet"},
            {"id":"170801_XR_4Y","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_OFF.internet"},{"id":"170801_54_5H","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_ON.mitm.tabs"},{"id":"170801_09_5G","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_OFF.mitm.tabs"},{"id":"170801_TY_4Z","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_ON.internet"},{"id":"170801_G5_50","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_OFF.internet"},{"id":"170801_W9_51","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_ON.internet"},{"id":"170801_NB_52","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_OFF.internet"},{"id":"170801_5K_53","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_ON.internet"},{"id":"170801_M5_5K","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_ON.mitm.tabs"},{"id":"170801_JC_5J","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_OFF.mitm.tabs"},{"id":"170801_KV_54","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_OFF.internet"},{"id":"170801_SG_55","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_ON.internet"},{"id":"170801_86_5M","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_OFF.mitm.tabs"},{"id":"170801_H3_5N","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_ON.mitm.tabs"},{"id":"170801_K3_56","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_OFF.internet"},{"id":"170801_MK_57","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_ON.internet"},{"id":"170801_FJ_5P","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_OFF.mitm.tabs"},{"id":"170801_HR_5Q","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_ON.mitm.tabs"},{"id":"170801_A9_58","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_OFF.internet"},{"id":"170801_8M_59","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_ON.internet"},{"id":"170801_FK_5A","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_OFF.internet"},{"id":"170801_V2_5S","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_ON.mitm.tabs"},{"id":"170801_RP_5B","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_ON.internet"},{"id":"170801_PY_5C","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_OFF.internet"},{"id":"170801_PD_5X","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_ON.mitm.tabs"},{"id":"170801_9K_5D","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_ON.internet"},{"id":"170801_PF_5E","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_OFF.internet"},{"id":"170801_TB_63","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_ON.mitm.tabs"},{"id":"170801_J4_5F","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_ON.internet"},{"id":"170802_Z6_2","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_OFF.mitm.tabs"},{"id":"170802_4D_1","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_OFF.mitm.tabs"},{"id":"170802_SA_4","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_OFF.mitm.tabs"},{"id":"170802_0X_3","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_OFF.mitm.tabs"},{"id":"170802_46_5","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_ON.mitm.tabs"},{"id":"170802_13_6","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_ON.mitm.tabs"},{"id":"170802_7D_7","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_OFF.mitm.tabs"},{"id":"170802_Y2_8","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_OFF.mitm.tabs"},{"id":"170802_DB_9","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_ON.mitm.tabs"},{"id":"170802_YF_Z","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_ON.internet.tabs"},{"id":"170802_C0_Y","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_OFF.Throttle_OFF.internet.tabs"},{"id":"170802_S9_11","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_ON.internet.tabs"},{"id":"170802_ER_10","url":"http://edition.cnn.com/2017/07/19/health/gupta-mccain-glioblastoma/index.html","label":"TP.LNP_ON.Throttle_OFF.internet.tabs"},{"id":"170802_G9_13","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_ON.internet.tabs"},{"id":"170802_K4_12","url":"https://twitter.com/bagder","label":"TP.LNP_OFF.Throttle_OFF.internet.tabs"},{"id":"170802_AF_14","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_OFF.internet.tabs"},{"id":"170802_BS_15","url":"https://twitter.com/bagder","label":"TP.LNP_ON.Throttle_ON.internet.tabs"},{"id":"170802_7J_16","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_OFF.internet.tabs"},{"id":"170802_HR_17","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_OFF.Throttle_ON.internet.tabs"},{"id":"170802_Q4_19","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_ON.internet.tabs"},{"id":"170802_FN_18","url":"https://www.wired.com/2017/03/mass-spying-isnt-just-intrusive-ineffective/","label":"TP.LNP_ON.Throttle_OFF.internet.tabs"},{"id":"170802_BF_1A","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_OFF.internet.tabs"},{"id":"170802_SW_1B","url":"https://500px.com/popular","label":"TP.LNP_OFF.Throttle_ON.internet.tabs"},{"id":"170802_MF_1C","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_OFF.internet.tabs"},{"id":"170802_3T_1D","url":"https://500px.com/popular","label":"TP.LNP_ON.Throttle_ON.internet.tabs"},{"id":"170802_1Z_1E","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_OFF.internet.tabs"},{"id":"170802_R9_1F","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_OFF.Throttle_ON.internet.tabs"},{"id":"170802_NM_1G","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_OFF.internet.tabs"},{"id":"170802_Q9_1H","url":"https://www.nytimes.com/2017/07/22/us/minneapolis-police-shooting.html?hp&action=click&pgtype=Homepage&clickSource=story-heading&module=photo-spot-region&region=top-news&WT.nav=top-news","label":"TP.LNP_ON.Throttle_ON.internet.tabs"}]'''

AllTasks = {}
TestDataPath = os.path.join(os.getcwd(), "static/testData/")
# http://wpt.xeon.tw/result/170801_TX_4W/requests.csv
WPTUrl = "http://wpt.xeon.tw/result/"

testCategoryTable = {'tp': 'Tracking Protection',
                     'tabs': 'Active Tab Priority (B/C Slots)',
                     'honza_0830': 'Tailing test 0830',
                     'honza_0901': 'Tailing test 0901'}

prefTable = {'LNP': 'privacy.trackingprotection.lower_network_priority',
             'Throttle': 'network.http.throttle.enable',
             'NoTabPrio': 'network.http.active_tab_priority'}

testProxyTable = {'internet': 'none',
                  'mitm': 'mitm proxy'}


AllBuilds = {}
BuildsURL = "http://presto.xeon.tw/api/builds"

def downloadCSV(url):
    pass

def createDir(label, category):
    dirname = category + '/' + label.replace(".", "_")
    if os.path.exists(TestDataPath + dirname):
        shutil.rmtree(TestDataPath + dirname)
    os.makedirs(TestDataPath + dirname)
    return dirname

def findUrls(label, dirname):
    global AllTasks
    result = []
    for task in AllTasks:
        if task["label"] == label:
            tmp = {}
            tmp["label"] = label
            tmp["id"] = task["id"]
            tmp["csvUrl"] = WPTUrl + task["id"] + "/requests.csv"
            tmp["testUrl"] = task["url"]
            tmp["dir"] = dirname
            result.append(tmp)
    return result

def createDataFromLabel(label, category, skipSummary):
    global AllBuilds

    print label
    dirname = createDir(label, category)

    results = findUrls(label, dirname)
    for item in results:
        if item["testUrl"] not in CDPTests:
            continue

        response = urllib2.urlopen(item["csvUrl"])
        content = response.read()
        with open('tmp.csv', 'w') as file:
            file.write(content)

        parsedCSVResult = ParseCSV("tmp.csv", CDPTests[item["testUrl"]])
        HeroElementResult = combineSameData(parsedCSVResult.HeroElementLoadData)
        TrackingResult = combineSameData(parsedCSVResult.TrackingResourcesData)

        if not HeroElementResult:
            print 'Error: No HeroElementResult for ' + CDPTests[item["testUrl"]]["site"]
        if not TrackingResult:
            print 'Error: No HeroElementResult for ' + CDPTests[item["testUrl"]]["site"]

        jsonResult = {'HeroElementResult':HeroElementResult, 'TrackingResult':TrackingResult}
        jsonFileName = CDPTests[item["testUrl"]]["site"] + ".json"
        outputPath = TestDataPath + item["dir"] + "/"
        with open(outputPath + jsonFileName, 'w') as outfile:
            json.dump(jsonResult, outfile, indent=4, separators=(',', ': '))

    if skipSummary is True:
        return

    summary = {"title": label}
    l = label.split('.')

    summary["Pref"] = {}
    for key in prefTable:
        summary["Pref"][prefTable[key]] = "true"
    for s in l:
        if s in testCategoryTable:
            summary["TestCategory"] = testCategoryTable[s]
            continue

        lnp = s.split('_')
        if lnp[0] == 'LNP':
            if lnp[1] == 'OFF':
                summary["Pref"][prefTable[lnp[0]]] = "false"
            continue

        throttle = s.split('_')
        if throttle[0] == 'Throttle':
            if throttle[1] == 'OFF':
                summary["Pref"][prefTable[throttle[0]]] = "false"
            continue

        if s in testProxyTable:
            summary["ProxyType"] = testProxyTable[s]
            continue

        if s in prefTable:
            summary["Pref"][prefTable[s]] = "false"


    for build in AllBuilds:
        if build['revision'] == label:
            summary['build'] = build['id']
            break


    with open(TestDataPath + dirname + "/" + "summary.json", 'w') as outfile:
        json.dump(summary, outfile, indent=4, separators=(',', ': '))


def main(argv):
    global AllTasks
    global AllBuilds
    if not AllTasks:
        response = urllib2.urlopen(AllTaskURL)
        AllTasks = json.loads(response.read())

    response = urllib2.urlopen(BuildsURL)
    AllBuilds = json.loads(response.read())

    labels = [  'a0536161fd2f7accd748f52ac706c9038984f008-mitm',
                '414d25ef3a26d53b30f39c924be7ac6c78709fa9-mitm',
                '75dcac95e0b217e8bc1cbd661cb1b44c10d11c84-mitm'
                ]

    for label in labels:
        createDataFromLabel(label, 'honza_0901', True)





if __name__ == "__main__":
    main(sys.argv)

