#!/usr/bin/env python
# coding: utf-8

import sys
import os
import re
import getopt
import cherrypy
import json

from . import tools
#import tools


class Summarizer(object):

    def __init__(self):
        self.summarizers = {}

    def get_summarizer(self, name):
        '''
        import summarizers on-demand
        '''
        if name in self.summarizers:
            pass
        elif name == 'lexrank':
            from . import lexrank
            print("ERRORRRRRRRRRRRRRRRRRRR100")
            self.summarizers[name] = lexrank.summarize
            print("ERRORRRRRRRRRRRRRRRRRRR1000")
        elif name == 'mcp':
            from . import mcp_summ
            self.summarizers[name] = mcp_summ.summarize

        return self.summarizers[name]

    @cherrypy.expose
    def summarize(self, text=None, algo=u'lexrank', **summarizer_params):
        '''
        Args:
          text: text to be summarized
          algo: summarizaion algorithm
              - 'lexrank' (default) graph-based
              - 'clexrank' Continuous LexRank
              - 'divrank' DivRank (Diverse Rank)
              - 'mcp' select sentences in terms of maximum coverage problem

          summarizer_params examples:
            char_limit: summary length (the number of characters)
            sent_limit: (not supported with mcp)
              summary length (the number of sentences)
            imp_require: (lexrank only)
              cumulative LexRank score [0.0-1.0]
        '''
        try:  # TODO: generate more useful error message
            # fix parameter type
            for param, value in summarizer_params.items():
                if value == '':
                    del summarizer_params[param]
                    continue
                elif re.match(r'^\d*.\d+$', value):
                    value = float(value)
                elif re.match(r'^\d+$', value):
                    value = int(value)
                elif value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                summarizer_params[param] = value

            if algo in ('lexrank', 'clexrank', 'divrank'):
                summarizer = self.get_summarizer('lexrank')
                print(summarizer)
                if algo == 'clexrank':
                    summarizer_params['continuous'] = True
                if algo == 'divrank':
                    summarizer_params['use_divrank'] = True
            elif algo == 'mcp':
                summarizer = self.get_summarizer('mcp')
            print("ERRORRRRRRRRRRRRRRRRRRR10")

            summary, debug_info = summarizer(text, **summarizer_params)
            print("ERRORRRRRRRRRRRRRRRRRRR10000")
            print(summary)

        except Exception, e:
            return json.dumps({'error': str(e)}, ensure_ascii=False, indent=2)
        else:
            res = json.dumps(
                tools.tree_encode({
                    'summary': summary, 'debug_info': debug_info
                }),
                ensure_ascii=False, indent=2
            )
            return res


if __name__ == '__main__':

    config = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': int(os.environ.get('PORT', 5000)),
        },
        '/': {
            'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__))
        },
        '/summarize': {
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [
                ('Content-type', 'application/json')
            ]
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './server_data'
        }
    }
    cherrypy.quickstart(Summarizer(), '/', config=config)
