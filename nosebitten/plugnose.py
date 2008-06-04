# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id$
# =============================================================================
#             $URL$
# $LastChangedDate$
#             $Rev$
#   $LastChangedBy$
# =============================================================================
# Copyright (C) 2006 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

import re
import os
import sys
import time
import logging
import traceback
from cStringIO import StringIO
from nose.plugins.base import Plugin
from nose.plugins.cover import Coverage
from nose.util import tolist, test_address
from bitten.util import xmlio
from bitten.util.testrunner import filter_coverage


log = logging.getLogger('nose.plugins.nosebitten')


class BittenNosetests(Plugin):
    """
    Use this plugin to write XML output to be used by Bitten.
    """

    name = 'bitten'

    def add_options(self, parser, env=os.environ):
        log.debug('Adding options on Bitten plug')
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--xml-results', action='store', dest='xml_results',
            metavar='FILE', help='write XML test results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'test-results.xml')
        )

    def configure(self, options, conf):
        log.debug('Configuring Bitten plug')
        Plugin.configure(self, options, conf)
        self.options = options
        self.conf = conf

    def begin(self):
        log.debug('Starting Bitten Output')
        if not os.path.exists(os.path.dirname(self.options.xml_results)):
            os.makedirs(os.path.dirname(self.options.xml_results))
        self.test_results = []

    def _add_test_result(self, test, status, output, err=None):
        filename, module, _ = test_address(test)
        if filename and filename.endswith('.pyc'):
            filename = filename[:-1]
        result = {
            'status': status,
            'fixture': module or test.id(),
            'description': test.shortDescription() or '',
            'file': filename,
            'output': output,
        }
        if err is not None:
            result['traceback'] = traceback.format_exception(*err)
        self.test_results.append(result)

    def addError(self, test, err, capt):
        log.debug('addError %s', test)
        self._add_test_result(test, 'error', capt, err)

    def addFailure(self, test, err, capt, tb_info):
        log.debug('addFailure %s', test)
        self._add_test_result(test, 'failure', capt, err)

    def addSuccess(self, test, capt):
        log.debug('addSuccess %s', test)
        self._add_test_result(test, 'success', capt)

    def finalize(self, result):
        log.debug('finalize dest = %s', self.options.xml_results)
        dom = xmlio.Element('unittest-results')
        for test_info in self.test_results:
            case = xmlio.Element('test')
            for key, val in test_info.iteritems():
                if val:
                    case.append(xmlio.Element(key)[val])
            dom.append(case)
        dom.write(open(self.options.xml_results, 'wt'), newlines=True)


class BittenNoseCoverage(Coverage):
    name = 'bitten-coverage'

    def options(self, parser, env=os.environ):
        Coverage.options(self, parser, env)
        Plugin.add_options(self, parser, env)
        parser.add_option(
            '--coverage-summary', action='store', dest='coverage_summary',
            metavar='FILE', help='write XML coverage results to FILE. Default: %default',
            default=os.path.join(os.getcwd(), 'build', 'coverage-results.txt')
        )
        parser.add_option(
            '--cover-packages', action='store', default=env.get('NOSE_COVER_PACKAGE'), dest='cover_packages'
        )

    def configure(self, options, config):
        Coverage.configure(self, options, config)
        self.coverage_summary = options.coverage_summary

    def begin(self):
        if not os.path.exists(os.path.dirname(self.coverage_summary)):
            os.makedirs(os.path.dirname(self.coverage_summary))
        Coverage.begin(self)

    def report(self, stream):
        buf = StringIO()
        Coverage.report(self, buf)
        buf.seek(0)
        fileobj = open(self.coverage_summary, 'w')
        try:
            filter_coverage(buf, fileobj)
        finally:
            fileobj.close()
        buf.seek(0)
        stream.writelines(buf)
