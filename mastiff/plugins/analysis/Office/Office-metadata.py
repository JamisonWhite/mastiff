#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  This software, having been partly or wholly developed and/or
  sponsored by KoreLogic, Inc., is hereby released under the terms
  and conditions set forth in the project's "README.LICENSE" file.
  For a list of all contributors and sponsors, please refer to the
  project's "README.CREDITS" file.
"""

__doc__ = """
Office MetaData Plug-in

Plugin Type: PDF
Purpose:
  Extracts any metadata from an Office document using exiftool
  (http://www.sno.phy.queensu.ca/~phil/exiftool/).

Output:
   metadata.txt - Contains selected pieces of metadata.

Requirements:
  The exiftool binary is required for this plug-in. The binary can be downloaded
  from http://www.sno.phy.queensu.ca/~phil/exiftool/.

Configuration Options:
[Office Metadata]
exiftool = Path to exiftool program
"""

__version__ = "$Id$"

import subprocess
import logging
import os

from mastiff.plugins import printable_str
import mastiff.plugins.category.office as office

class OfficeMetadata(office.OfficeCat):
    """Office Metadata plug-in."""

    def __init__(self):
        """Initialize the plugin."""
        office.OfficeCat.__init__(self)

    def analyze(self, config, filename):
        """
        Obtain the command and options from the config file and call the
        external program.
        """
        # make sure we are activated
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # get my config options
        plug_opts = config.get_section(self.name)
        if plug_opts is None:
            log.error('Could not get %s options.', self.name)
            return False

        # verify external program exists and we can call it
        if not plug_opts['exiftool'] or \
           not os.path.isfile(plug_opts['exiftool']) or \
           not os.access(plug_opts['exiftool'], os.X_OK):
            log.error('%s is not accessible. Skipping.', plug_opts['exiftool'])
            return False

        # run your external program here
        run = subprocess.Popen([plug_opts['exiftool']] + \
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            return False

        metadata = dict()
        keywords = [ 'Author', 'Code Page', 'Comments', 'Company',
                     'Create Date', 'Current User', 'Error',
                     'File Modification Date/Time', 'File Type',
                     'Internal Version Number', 'Keywords',
                     'Last Modified By', 'Last Printed', 'MIME Type',
                     'Modify Date', 'Security', 'Software', 'Subject',
                     'Tag PID GUID', 'Template', 'Title', 'Title Of Parts',
                     'Total Edit Time', 'Warning']

        # grab only data we are interested in
        for line in output.split('\n'):
            if line.split(' :')[0].rstrip() in keywords:
                metadata[line.split(':')[0].rstrip()] = \
                line.split(' :')[1].rstrip()


        self.output_file(config.get_var('Dir','log_dir'), metadata)
        log.debug ('Successfully ran %s.', self.name)

        return True

    def output_file(self, outdir, data):
        """Place the data into a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        try:
            out_file = open(outdir + os.sep + "metadata.txt",'w')
            out_file.write('Office Document Metadata\n\n')
            for key in data.keys():
                out_file.write('{0:25}\t{1}\n'.format(key, printable_str(data[key])) )
        except IOError, err:
            log.error('Write error: %s', err)
            return False

        out_file.close()
        return True

