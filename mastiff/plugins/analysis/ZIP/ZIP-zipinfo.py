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
Zipinfo Analysis Plug-in

Plugin Type: ZIP
Purpose:
  This plug-in extracts metadata information stored within a zip archive
  for the analysis.

  Alot of information was taken from
  http://www.pkware.com/documents/casestudies/APPNOTE.TXT.

TO DO:
  - Decode external attributes.
  - Decode extra data.

Output:
   zipinfo.txt - File containing all of the metadata.

"""

__version__ = "$Id$"

import os
import logging
import zipfile
import codecs

import mastiff.plugins.category.zip as zip

class ZipInfo_u(zip.ZipCat):
    """Class to extract zip metadata and place it into a file."""

    def __init__(self):
        """Initialize the plugin."""
        zip.ZipCat.__init__(self)

    def activate(self):
        """Activate the plugin."""
        zip.ZipCat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        zip.ZipCat.deactivate(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # grab the info out of the file
        try:
            my_zip = zipfile.ZipFile(filename, 'r')
            info_list = my_zip.infolist()
        except (zipfile.BadZipfile, IOError), err:
            log.error('Unable to open or process zip file: %s' \
                      % err)
            return False


        out_str = u"File Name: %s\n" % (os.path.basename(filename))
        if my_zip.comment is None or len(my_zip.comment) == 0:
            out_str += "This file has no comment.\n\n"
        else:
            # ignore any unprintable unicode characters
            out_str += unicode("Comment: %s\n\n" % (my_zip.comment),  errors='ignore')            
        
        my_zip.close()

        out_str += self.quick_info(info_list) + '\n'
        out_str += self.full_info(info_list)

        self.output_file(config.get_var('Dir','log_dir'), out_str)
        return True

    def quick_info(self, info_list):
        """ Obtain quick directory listing of the archive with some information."""
        output = '{0:19} {1:10} {2:35}\n'.format('Modification Date', \
                                                 'File Size', 'File Name',)
        output += '-'*80 + '\n'

        for file_info in info_list:
            date_str = "%d/%d/%d %d:%d:%d" % \
            (file_info.date_time[1], file_info.date_time[2], file_info.date_time[0], \
             file_info.date_time[3], file_info.date_time[4], file_info.date_time[5])

            # if file is encrypted, flag it
            filename = file_info.filename
            if file_info.flag_bits & 0x1 == 0x1:
                filename = '* ' + file_info.filename

            output += u'{0:19} {1:<10} {2:35}\n'.format(date_str, \
                                                       file_info.file_size, \
                                                       filename)


        return output

    def _version_created(self, version):
        """ Return a string containing the system that created the archive.
             Taken from http://www.pkware.com/documents/casestudies/APPNOTE.TXT
        """
        sys_list = ["MS-DOS, OS/2, FAT/VFAT/FAT32", "Amiga", "OpenVMS",  "UNIX",
                    "VM/CMS",  "Atari ST",  "OS/2 H.P.F.S.",  "Macintosh",
                    "Z-System",  "CP/M",  "Windows NTFS",  "MVS (OS/390 - Z/OS)",
                    "VSE",  "Acorn Risc",  "VFAT",  "alternative MVS",  "BeOS",
                    "Tandem",  "OS/400",  "OS X Darwin",  "Unknown"]
        if version > 20:
            version = 19

        return sys_list[version]

    def _flag_bits(self, flag_bits, method):
        """ Returns a string containing the explanation of the flag bits. """

        output = ""
        if flag_bits & 0x1 == 0x1:
            output += " "*24 + "- This file is encrypted.\n"

        if method == 6:
            # Imploding
            if flag_bits & 0x2 == 0x2:
                output += " "*24 + "- 8K sliding dictionary used for compression.\n"
            else:
                output += " "*24 + "- 4K sliding dictionary used for compression.\n"
            if flag_bits & 0x4 == 0x4:
                output += " "*24 + "- 3 Shannon-Fano trees used for sliding dictionary.\n"
            else:
                output += " "*24 + "- 2 Shannon-Fano trees used for sliding dictionary.\n"
        elif method == 8 or method == 9:
            # Deflating
            if flag_bits & 0x6 == 0:
                output += " "*24 + "- Normal (-en)"
            elif flag_bits & 0x6 == 0x2:
                output += " "*24 + "- Maximum (-exx/-ex)"
            elif flag_bits & 0x6 == 0x4:
                output += " "*24 + "- Fast (-ef)"
            elif flag_bits & 0x6 == 0x6:
                output += " "*24 + "- Super Fast (-es)"
            else:
                output += " "*24 + "- UNKNOWN"
            output += " compression option was used.\n"
        elif method == 14:
            # LZMA
            if flag_bits & 0x02 == 0x02:
                output += " "*24 + "- EOS marker indicates end of compressed data stream.\n"

        if flag_bits & 8 == 8:
            output += " "*24 + "- Correct values for CRC-32 and sizes are in data descriptor.\n"

        if flag_bits & 32 == 32:
            output += " "*24 + "- File is compressed patched data.\n"

        if flag_bits & 64 == 64:
            output += " "*24 + "- Strong encryption is used.\n"

        if flag_bits & 2048 == 2048:
            output += " "*24 + "- Filename and comments must be encoded in UTF-8.\n"

        if flag_bits & 8192 == 8192:
            output += " "*24 + "- Central Directory encrypted."

        return output

    def _compression_method(self, method):
        """ Returns a string describing the compression method used. """

        methods = [ 'no compression', 'Shrunk',
                   'Reduced with compression factor 1',
                  'Reduced with compression factor 2',
                  'Reduced with compression factor 3',
                  'Reduced with compression factor 4', 'Imploded',
                  'Tokenizing compression algorithm', 'Deflated',
                  'Enhanced Deflating using Deflate64(tm)',
                  'PKWARE Data Compression Library Imploding (old IBM TERSE)',
                  'Reserved by PKWARE', 'BZIP2 algorithm', 'Reserved by PKWARE',
                  'LZMA (EFS)', 'Reserved by PKWARE', 'Reserved by PKWARE',
                  'Reserved by PKWARE', 'IBM TERSE (new)',
                  'IBM LZ77 z Architecture (PFS)', 'WavPack compressed',
                  'PPMd version I, Rev 1',  'UNKNOWN']

        if method == 97:
            method = 20
        elif method == 98:
            method = 21
        elif method > 19:
            method = 22

        return methods[method]

    def _internal_attribs(self, attrib):
        """ Returns a string describing the internal attributes."""

        output = ""
        if attrib & 0x01 == 0x01:
            output += " "*24 + "- File is apparently ASCII or text.\n"

        """ NOTE: bit 0x0002 means that a 4 byte variable record length
             field is present, but this info doesn't seem useful in this case.
        """

        return output

    def full_info(self, info_list):
        """ Obtain a full set of information for each file within the archive. """

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.fileinfo')
        output = ""

        try:
            for file_info in info_list:
                output += u"{0:24}".format("File Name:") + "%s\n" % file_info.filename

                date_str = "%d/%d/%d %d:%d:%d" % \
                (file_info.date_time[1], file_info.date_time[2], file_info.date_time[0], \
                file_info.date_time[3], file_info.date_time[4], file_info.date_time[5])

                output += "{0:24}".format("Last modification date:") + "%s\n" % date_str
                output +=  "{0:24}".format("Compression Type:") + "%d - %s\n" % \
                (file_info.compress_type, self._compression_method(file_info.compress_type))

                output +=  "{0:24}".format("File comment:")
                if file_info.comment is None or len(file_info.comment) == 0:
                    output += "None\n"
                else:
                    output +=  u"%s\n" % file_info.comment

                output +=  "{0:24}".format("Creation system:") + "%s (%d)\n" % \
                (self._version_created(file_info.create_system), file_info.create_system)

                output +=  "{0:24}".format("PKZIP creation version:") + "%s\n" % file_info.create_version
                output +=  "{0:24}".format("Version to extract:") + "%d\n" % file_info.extract_version
                output +=  "{0:24}".format("Flag bits:") + "0x%x\n" % file_info.flag_bits
                output +=  self._flag_bits(file_info.flag_bits, file_info.compress_type)
                output +=  "{0:24}".format("Volume number:") + "%s\n" % file_info.volume
                output +=  "{0:24}".format("Internal attributes:") + "0x%x\n" % file_info.internal_attr
                output += self._internal_attribs(file_info.internal_attr)
                output +=  "{0:24}".format("External attributes:") + "0x%x\n" % file_info.external_attr
                output +=  "{0:24}".format("CRC32:") + "%s\n" % file_info.CRC
                output +=  "{0:24}".format("Header offset:") + "%s\n" % file_info.header_offset
                output +=  "{0:24}".format("Compressed size:") + "%s\n" % file_info.compress_size
                output +=  "{0:24}".format("Uncompress size:") + "%s\n" % file_info.file_size
                if file_info.extra is not None:
                    output += "{0:24}".format("This file entry contains extra data. Not supported yet.")

                output += "\n\n"

        except ImportError:
            log.error('Error obtaining file information from archive for %s.' % file_info.filename)

        return output

    def output_file(self, outdir, data):
        """Print output from analysis to a file."""

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.output')

        try:
            outfile = codecs.open(outdir + os.sep + 'zipinfo.txt', 'w',  encoding='utf-8')
            outfile.write(data)
            outfile.close()
        except IOError, err:
            log.error('Could not open zipinfo.txt: %s' % err)
            return False

        return True

