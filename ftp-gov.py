import re
import sys
import urllib.request

from wpull.application.hook import Actions
from wpull.application.plugin import WpullPlugin, PluginFunctions, hook
from wpull.protocol.abstract.request import BaseResponse
from wpull.pipeline.session import ItemSession

tries = {}


class FTPPlugin(WpullPlugin):
    @hook(PluginFunctions.handle_response)
    def handle_resp(self, item_session: ItemSession):
        if 200 <= item_session.response.response_code() <= 299:
            tries[item_session.request.url_info.url] = 0
            return Actions.NORMAL
        elif item_session.response.response_code() in (530, 550):
            tries[item_session.request.url_info.url] = 0
            return Actions.FINISH

        if tries[item_session.request.url_info.url] >= 5:
            raise Exception('Something went wrong, received status code %d 5 times. ABORTING...' % (response_code))

        print('You received status code %d. Retrying...' % response_code)
        sys.stdout.flush()

        if not item_session.request.url_info.url in tries:
            tries[item_session.request.url_info.url] = 0
        tries[item_session.request.url_info.url] += 1

        return Actions.RETRY

    @hook(PluginFunctions.handle_error)
    def handle_err(self, item_session: ItemSession, error: BaseException):
        ftp_server = re.search(r'^ftp:\/\/([^/]+)', item_session.request.url).group(1)
        item_file = ftp_server + '_bad_url'
        item_url = 'http://master.newsbuddy.net/ftplists/' + item_file

        item_message = urllib.request.urlopen(item_url)
        item_message_text = item_message.read()
        item_messages = item_message_text.decode('utf-8') \
            .split('NONEXISTINGFILEdgdjahxnedadbacxjbc')

        if item_message.getcode() == 200:
            try:
                urllib.request.urlopen(item_session.request.url)
            except Exception as error:
                error_message = str(error)
                print("ERROR Received error message " + error_message)
                sys.stdout.flush()

                if all(text in error_message for text in item_messages):
                    print('INFO ' + item_session.request.url
                        + ' does not exist, skipping...')
                    sys.stdout.flush()

                    return Actions.FINISH

        elif item_message.getcode() == 404:
            raise Exception('URL ' + item_url + ' doesn\'t exist. ABORTING...')

        else:
            raise Exception('Received status code '
                + str(item_list.status_code) + ' for URL ' + item_url
                + '. ABORTING...')

        if not item_session.request.url in tries:
            tries[item_session.request.url] = 0
        tries[item_session.request.url] += 1

        if tries[item_session.request.url] >= 5:
            raise Exception('Something went wrong... ABORTING...')

        return Actions.RETRY