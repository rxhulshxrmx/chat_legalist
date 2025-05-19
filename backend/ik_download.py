# ik_download.py
import argparse
import logging
import os
import re
import codecs
import json
import http.client
import urllib.request, urllib.parse, urllib.error
import base64
import glob
import csv
import datetime
import time
import multiprocessing

def print_usage(progname):
    print('''python %s -t token -o offset -n limit -d datadir''' % progname)

class IKApi:
    def __init__(self, args, storage):
        self.logger = logging.getLogger('ikapi')

        self.headers = {
            'Authorization': 'Token %s' % args.token,
            'Accept': 'application/json'
        }

        self.basehost = 'api.indiankanoon.org'
        self.storage = storage
        self.maxcites = args.maxcites
        self.maxcitedby = args.maxcitedby
        self.orig = args.orig
        self.maxpages = args.maxpages
        self.pathbysrc = args.pathbysrc
        self.queue = multiprocessing.Queue(20)
        self.num_workers = args.numworkers
        self.addedtoday = args.addedtoday
        self.fromdate = args.fromdate
        self.todate = args.todate
        self.sortby = args.sortby

        if self.maxpages > 100:
            self.maxpages = 100

    def call_api_direct(self, url):
        connection = http.client.HTTPSConnection(self.basehost)
        connection.request('POST', url, headers=self.headers)
        response = connection.getresponse()
        results = response.read()

        if isinstance(results, bytes):
            results = results.decode('utf8')
        return results

    def call_api(self, url):
        count = 0

        while count < 10:
            try:
                results = self.call_api_direct(url)
                if results is None or (isinstance(results, str) and re.match('error code:', results)):
                    self.logger.warning('Error in call_api %s %s', url, results)
                    count += 1
                    time.sleep(count * 5)  # Reduced sleep time for debugging
                else:
                    return results
            except Exception as e:
                self.logger.warning('Error in call_api %s %s', url, e)
                count += 1
                time.sleep(count * 5)  # Reduced sleep time for debugging
        
        # If we get here, all attempts failed
        self.logger.error('Failed after 10 attempts: %s', url)
        return json.dumps({"errmsg": "Failed to connect to Indian Kanoon API after multiple attempts"})

    def fetch_doc(self, docid):
        url = '/doc/%d/' % docid

        args = []
        if self.maxcites > 0:
            args.append('maxcites=%d' % self.maxcites)

        if self.maxcitedby > 0:
            args.append('maxcitedby=%d' % self.maxcitedby)

        if args:
            url = url + '?' + '&'.join(args)

        return self.call_api(url)

    # Keep other methods from the original file...
    # Abbreviated for clarity, make sure to include all methods in your actual file

    def search(self, q, pagenum, maxpages):
        """Search the Indian Kanoon API"""
        try:
            q = urllib.parse.quote_plus(q.encode('utf8'))
            url = '/search/?formInput=%s&pagenum=%d&maxpages=%d' % (q, pagenum, maxpages)
            return self.call_api(url)
        except Exception as e:
            self.logger.error('Error in search method: %s', e)
            return json.dumps({"errmsg": str(e)})

# Include other classes from the original file (FileStorage, etc.)
# Abbreviated for clarity

def get_dateobj(datestr):
    ds = re.findall('\\d+', datestr)
    return datetime.date(int(ds[0]), int(ds[1]), int(ds[2]))

def mk_dir(datadir):
    if not os.path.exists(datadir):
        os.mkdir(datadir)

class FileStorage:
    def __init__(self, datadir):
        self.datadir = datadir
        # Ensure the directory exists
        mk_dir(datadir)

    def save_json(self, results, filepath):
        json_doc = results
        json_file = codecs.open(filepath, mode='w', encoding='utf-8')
        json_file.write(json_doc)
        json_file.close()
        return True

    def exists(self, filepath):
        return os.path.exists(filepath)

    def exists_original(self, origpath):
        return glob.glob('%s.*' % origpath)

    def get_docpath(self, docsource, publishdate):
        datadir = os.path.join(self.datadir, docsource)
        mk_dir(datadir)

        d = get_dateobj(publishdate)
        datadir = os.path.join(datadir, '%d' % d.year)
        mk_dir(datadir)

        docpath = os.path.join(datadir, '%s' % d)
        mk_dir(docpath)

        return docpath

    # Include other methods from the original FileStorage class
    # Abbreviated for clarity

def get_arg_parser():
    parser = argparse.ArgumentParser(description='For downloading from the api.indiankanoon.org endpoint', add_help=True)
    parser.add_argument('-l', '--loglevel', dest='loglevel', action='store',
                        required=False, default='info',
                        help='log level(error|warning|info|debug)')

    parser.add_argument('-g', '--logfile', dest='logfile', action='store',
                        required=False, default=None, help='log file')

    parser.add_argument('-c', '--doctype', dest='doctype', action='store',
                        required=False, help='doctype')
    parser.add_argument('-f', '--fromdate', dest='fromdate', action='store',
                        required=False, help='from date in DD-MM-YYYY format')
    parser.add_argument('-t', '--todate', dest='todate', action='store',
                        required=False, help='to date in DD-MM-YYYY format')
    parser.add_argument('-S', '--sortby', dest='sortby', action='store',
                        required=False, help='sort results by (mostrecent|leastrecent)')

    parser.add_argument('-D', '--datadir', dest='datadir', action='store',
                        required=False, help='directory to store files')
    parser.add_argument('-s', '--sharedtoken', dest='token', action='store',
                        required=False, help='api.ik shared token')

    parser.add_argument('-q', '--query', dest='q', action='store',
                        required=False, help='ik query')
    parser.add_argument('-Q', '--qfile', dest='qfile', action='store',
                        required=False, help='queries in a file')
    parser.add_argument('-d', '--docid', type=int, dest='docid',
                        action='store', required=False, help='ik docid')

    parser.add_argument('-o', '--original', dest='orig', action='store_true',
                        required=False, help='ik original')

    parser.add_argument('-m', '--maxcites', type=int, dest='maxcites',
                        action='store', default=0, required=False,
                        help='doc maxcites')
    parser.add_argument('-M', '--maxcitedby', type=int, dest='maxcitedby',
                        action='store', default=0, required=False,
                        help='doc maxcitedby')
    parser.add_argument('-p', '--maxpages', type=int, dest='maxpages',
                        action='store', required=False,
                        help='max search result pages', default=1)
    parser.add_argument('-P', '--pathbysrc', dest='pathbysrc',
                        action='store_true', required=False,
                        help='save docs by src')
    parser.add_argument('-a', '--addedtoday', dest='addedtoday',
                        action='store_true', required=False, default=False,
                        help='Search only for documents that were added today')
    parser.add_argument('-N', '--workers', type=int, dest='numworkers',
                        action='store', default=5, required=False,
                        help='num workers for parallel downloads')
    return parser

# Setup logging functions
logformat = '%(asctime)s: %(name)s: %(levelname)s %(message)s'
dateformat = '%Y-%m-%d %H:%M:%S'

def initialize_file_logging(loglevel, filepath):
    logging.basicConfig(
        level=loglevel,
        format=logformat,
        datefmt=dateformat,
        stream=filepath
    )

def initialize_stream_logging(loglevel=logging.INFO):
    logging.basicConfig(
        level=loglevel,
        format=logformat,
        datefmt=dateformat
    )

def setup_logging(level, filename=None):
    leveldict = {'critical': logging.CRITICAL, 'error': logging.ERROR,
                 'warning': logging.WARNING, 'info': logging.INFO,
                 'debug': logging.DEBUG}
    loglevel = leveldict[level]

    if filename:
        filestream = codecs.open(filename, 'w', encoding='utf8')
        initialize_file_logging(loglevel, filestream)
    else:
        initialize_stream_logging(loglevel)

# The main function can be kept for command-line usage
if __name__ == '__main__':
    parser = get_arg_parser()
    args = parser.parse_args()

    setup_logging(args.loglevel, filename=args.logfile)

    logger = logging.getLogger('ikapi')

    filestorage = FileStorage(args.datadir)
    ikapi = IKApi(args, filestorage)

    has_more = True

    if args.docid is not None and args.q:
        logger.warning('Docfragment for %d q: %s', args.docid, args.q)
        ikapi.save_doc_fragment(args.docid, args.q)
    elif args.docid is not None:
        ikapi.download_doc(args.docid, args.datadir)
    elif args.q:
        q = args.q
        if args.addedtoday:
            q += ' added:today'
        logger.warning('Search q: %s', q)
        ikapi.save_search_results(q)
    elif args.doctype:
        ikapi.download_doctype(args.doctype)
    elif args.qfile:
        queries = []
        filehandle = open(args.qfile, 'r', encoding='utf8')
        for line in filehandle.readlines():
            queries.append(line.strip())
        ikapi.execute_tasks(queries)
        filehandle.close()