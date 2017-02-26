from distutils.version import StrictVersion
import codecs
import datetime
import hashlib
import os
import re
import socket
import shutil
import time
import sys
import urllib

try:
    import requests
except ImportError:
    print('Please install or update the requests module.')
    sys.exit(1)
import seesaw
import warcat.model
from seesaw.config import realize, NumberConfigValue
from seesaw.externalprocess import WgetDownload, ExternalProcess
from seesaw.item import ItemInterpolation, ItemValue
from seesaw.pipeline import Pipeline
from seesaw.project import Project
from seesaw.task import SimpleTask, SetItemKey, LimitConcurrent
from seesaw.tracker import PrepareStatsForTracker, GetItemFromTracker, \
    UploadWithTracker, SendDoneToTracker
from seesaw.util import find_executable


# check the seesaw version
if StrictVersion(seesaw.__version__) < StrictVersion("0.8.3"):
    raise Exception("This pipeline needs seesaw version 0.8.3 or higher.")


###########################################################################
# Find a useful Wpull executable.
#
# WPULL_EXE will be set to the first path that
# 1. does not crash with --version, and
# 2. prints the required version string
WPULL_EXE = find_executable(
    "Wpull",
    re.compile(r"\b2\.0\.1\b"),
    [
        "./wpull",
        os.path.expanduser("~/.local/share/wpull-2.0.1/wpull"),
        os.path.expanduser("~/.local/bin/wpull"),
        "/usr/local/bin/wpull",
        "./wpull_bootstrap",
        "wpull"
    ]
)

if not WPULL_EXE:
    raise Exception("No usable Wpull found.")


###########################################################################
# The version number of this pipeline definition.
#
# Update this each time you make a non-cosmetic change.
# It will be added to the WARC files and reported to the tracker.
VERSION = "20170226.01"
TRACKER_ID = 'ftp-gov'
TRACKER_HOST = 'tracker.archiveteam.org'


###########################################################################
# This section defines project-specific tasks.
#
# Simple tasks (tasks that do not need any concurrency) are based on the
# SimpleTask class and have a process(item) method that is called for
# each item.


class CheckIP(SimpleTask):
    def __init__(self):
        SimpleTask.__init__(self, "CheckIP")
        self._counter = 0

    def process(self, item):
        if self._counter <= 0:
            item.log_output('Checking IP address.')
            ip_set = set()

            ip_set.add(socket.gethostbyname('twitter.com'))
            ip_set.add(socket.gethostbyname('facebook.com'))
            ip_set.add(socket.gethostbyname('youtube.com'))
            ip_set.add(socket.gethostbyname('microsoft.com'))
            ip_set.add(socket.gethostbyname('icanhas.cheezburger.com'))
            ip_set.add(socket.gethostbyname('archiveteam.org'))

            if len(ip_set) != 6:
                item.log_output('Got IP addresses: {0}'.format(ip_set))
                item.log_output(
                    'You are behind a firewall or proxy. That is a big no-no!')
                raise Exception(
                    'You are behind a firewall or proxy. That is a big no-no!')

        # Check only occasionally
        if self._counter <= 0:
            self._counter = 10
        else:
            self._counter -= 1


class PrepareDirectories(SimpleTask):
    def __init__(self, warc_prefix):
        SimpleTask.__init__(self, "PrepareDirectories")
        self.warc_prefix = warc_prefix

    def process(self, item):
        item_name = item["item_name"]
        escaped_item_name = item_name.replace(':', '_').replace('/', '_')
        item['escaped_item_name'] = escaped_item_name

        dirname = "/".join((item["data_dir"], escaped_item_name))

        if os.path.isdir(dirname):
            shutil.rmtree(dirname)

        os.makedirs(dirname)

        item["item_dir"] = dirname
        item["warc_file_base"] = "%s-%s-%s" % (
            self.warc_prefix, escaped_item_name,
            time.strftime("%Y%m%d-%H%M%S")
        )

        open("%(item_dir)s/%(warc_file_base)s.warc.gz" % item, "w").close()
        open("%(item_dir)s/%(warc_file_base)s.records" % item, "w").close()


class MoveFiles(SimpleTask):
    def __init__(self):
        SimpleTask.__init__(self, "MoveFiles")

    def process(self, item):
        # Check if wget was compiled with zlib support
        if os.path.exists("%(item_dir)s/%(warc_file_base)s.warc" % item):
            raise Exception('Please compile wget with zlib support!')

        os.rename("%(item_dir)s/%(warc_file_base)s.warc.gz" % item,
                  "%(data_dir)s/%(warc_file_base)s.warc.gz" % item)
        os.rename("%(item_dir)s/%(warc_file_base)s.records" % item,
                  "%(data_dir)s/%(warc_file_base)s.records" % item)

        shutil.rmtree("%(item_dir)s" % item)

def get_hash(filename):
    with open(filename, 'rb') as in_file:
        return hashlib.sha1(in_file.read()).hexdigest()


CWD = os.getcwd()
PIPELINE_SHA1 = get_hash(os.path.join(CWD, 'pipeline.py'))
SCRIPT_SHA1 = get_hash(os.path.join(CWD, 'ftp-gov.py'))


def stats_id_function(item):
    # For accountability and stats.
    d = {
        'pipeline_hash': PIPELINE_SHA1,
        'script_hash': SCRIPT_SHA1,
        'python_version': sys.version,
        }

    return d


class WgetArgs(object):
    def realize(self, item):
        wget_args = [
            WPULL_EXE,
            "-nv",
            "--plugin-script", "ftp-gov.py",
            "-o", ItemInterpolation("%(item_dir)s/wpull.log"),
            "--no-check-certificate",
            "--database", ItemInterpolation("%(item_dir)s/wpull.db"),
            "--delete-after",
            "--no-robots",
            "--no-cookies",
            "--rotate-dns",
            "--timeout", "60",
            "--tries", "inf",
            "--wait", "0.5",
            "--random-wait",
            "--waitretry", "5",
            "--warc-file", ItemInterpolation("%(item_dir)s/%(warc_file_base)s"),
            "--warc-header", "operator: Archive Team",
            "--warc-header", "ftp-gov-dld-script-version: " + VERSION,
            "--warc-header", ItemInterpolation("ftp-gov-item: %(item_name)s"),
        ]

        item_name = item['item_name']
        assert ':' in item_name
        item_sort, item_file = item_name.split(':', 1)

        MAX_SIZE = 10737418240
        
        skipped = requests.get('https://raw.githubusercontent.com/ArchiveTeam/ftp-items/master/skipped_sites')
        if skipped.status_code != 200:
            raise Exception('Something went wrong getting the skipped_sites list from GitHub. ABORTING.')
        skipped_dirs = requests.get('https://raw.githubusercontent.com/ArchiveTeam/ftp-items/master/skipped_dirs')
        if skipped_dirs.status_code != 200:
            raise Exception('Something went wrong getting the skipped_sites list from GitHub. ABORTING.')

        for skipped_item in skipped.text.splitlines():
            if item_file.startswith(skipped_item):
                raise Exception('This FTP will be skipped...')

        skipped_dirs_ = ['ftp://' + s.strip().replace(':', '', 1) for s in skipped_dirs.text.splitlines()]

        item_url = 'http://master.newsbuddy.net/ftplists/{0}'.format(item_file)
        item_list = requests.get(item_url)
        if item_list.status_code != 200:
            raise Exception('You received status code %d with URL %s. ABORTING.'%(item_list.status_code, item_url))
        itemsize = int(re.search(r'ITEM_TOTAL_SIZE: ([0-9]+)', item_list.text).group(1))
        if itemsize > MAX_SIZE:
            raise Exception('Item is %d bytes. This is larger then %d bytes. ABORTING.'%(itemsize, MAX_SIZE))

        urls = [u for u in item_list.text.splitlines() if u.startswith('ftp://') and not any([str(u).startswith(skip) for skip in skipped_dirs_])]

        urls.append(item_url)

        print(urls)
        print(skipped_dirs_)

        for url in urls:
            url = url.replace('&#32;', '%20').replace('&amp;', '&')
            url = urllib.unquote(url)

            if '#' in url:
                raise Exception('%s containes a bad character.'%(url))
            else:
                wget_args.append(url)

        if 'bind_address' in globals():
            wget_args.extend(['--bind-address', globals()['bind_address']])
            print('')
            print('*** Wget will bind address at {0} ***'.format(
                globals()['bind_address']))
            print('')

        return realize(wget_args, item)


###########################################################################
# Initialize the project.
#
# This will be shown in the warrior management panel. The logo should not
# be too big. The deadline is optional.
project = Project(
    title="ftp-gov",
    project_html="""
        <img class="project-logo" alt="Project logo" src="http://archiveteam.org/images/thumb/0/09/NOAA_logo.png/240px-NOAA_logo.png" height="50px" title=""/>
        <h2>USA-Gov <span class="links"><a href="http://archiveteam.org/index.php?title=USA-Gov">Website</a> &middot;
            <a href="http://tracker.archiveteam.org/ftp-gov/">Leaderboard</a></span></h2>
        <p>Archiving all government FTPs!</p>
    """
)

pipeline = Pipeline(
    CheckIP(),
    GetItemFromTracker("http://%s/%s" % (TRACKER_HOST, TRACKER_ID), downloader,
                       VERSION),
    PrepareDirectories(warc_prefix="ftp-gov"),
    WgetDownload(
        WgetArgs(),
        max_tries=1,
        accept_on_exit_code=[0, 8],
        env={
            "item_dir": ItemValue("item_dir"),
            "downloader": downloader
        }
    ),
    PrepareStatsForTracker(
        defaults={"downloader": downloader, "version": VERSION},
        file_groups={
            "data": [
                ItemInterpolation("%(item_dir)s/%(warc_file_base)s.warc.gz"),
            ]
        },
        id_function=stats_id_function,
    ),
    ExternalProcess("ExtractRecordsInfo", ["python3", "extract.py", ItemInterpolation("%(item_dir)s/%(warc_file_base)s")]),
    ExtractRecordsInfo(),
    MoveFiles(),
    LimitConcurrent(
        NumberConfigValue(min=1, max=20, default="20",
                          name="shared:rsync_threads", title="Rsync threads",
                          description="The maximum number of concurrent uploads."),
        UploadWithTracker(
            "http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
            downloader=downloader,
            version=VERSION,
            files=[
                ItemInterpolation("%(data_dir)s/%(warc_file_base)s.warc.gz"),
                ItemInterpolation("%(data_dir)s/%(warc_file_base)s.records"),
            ],
            rsync_target_source_path=ItemInterpolation("%(data_dir)s/"),
            rsync_extra_args=[
                "--recursive",
                "--partial",
                "--partial-dir", ".rsync-tmp",
                ]
        ),
    ),
    SendDoneToTracker(
        tracker_url="http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
        stats=ItemValue("stats")
    )
)
