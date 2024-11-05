#!/usr/bin/env python3
# create the enterprises.c file from
# https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers
# or an offline copy
#
# Copyright 2022 by Moshe Kaplan
# Based on make-sminmpec.pl by Gerald Combs
#
# Wireshark - Network traffic analyzer
# By Gerald Combs <gerald@wireshark.org>
# Copyright 2004 Gerald Combs
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
import argparse
import re
import urllib.request


ENTERPRISES_CFILE = os.path.join('epan', 'enterprises.c')

ENTERPRISE_NUMBERS_URL = "https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers"

DECIMAL_PATTERN = r"^(\d+)"
# up to three spaces because of formatting errors in the source
ORGANIZATION_PATTERN = r"^   ?(\S.*)"
FORMERLY_PATTERN = r" \(((formerly|previously) .*)\)"


LOOKUP_FUNCTION = r"""
const char* global_enterprises_lookup(uint32_t value)
{
    if (value >= array_length(table)) {
        return NULL;
    }
    return table[value];
}
"""

DUMP_FUNCTION = r"""
void global_enterprises_dump(FILE *fp)
{
    for (size_t idx = 0; idx < array_length(table); idx++) {
        if (table[idx] != NULL) {
            fprintf(fp, "%zu\t%s\n", idx, table[idx]);
        }
    }
}
"""

# This intermediate format is no longer written to a file - returned as string
def generate_enterprise_entries(file_content):
    # We only care about the "Decimal" and "Organization",
    # not the contact or email
    org_lines = []
    last_updated = ""
    end_seen = False
    for line in file_content.splitlines():
        decimal_match = re.match(DECIMAL_PATTERN, line)
        if decimal_match:
            decimal = decimal_match.group(0)
        elif re.match(ORGANIZATION_PATTERN, line):
            organization = line.strip()
            if organization.lower() == "unassigned":
                continue
            organization = re.sub(FORMERLY_PATTERN, r"\t# \1", organization)
            org_lines += [decimal + "\t" + organization]
        elif "last updated" in line.lower():
            last_updated = line
        elif "end of document" in line.lower():
            end_seen = True

    if not end_seen:
        raise Exception('"End of Document" not found. Truncated source file?')

    last_updated_line = "/* " + last_updated + " */\n\n"
    output = "\n".join(org_lines) + "\n"
    return (output,last_updated_line)

class CFile:
    def __init__(self, filename, last_updated_line):
        self.filename = filename
        self.f = open(filename, 'w')
        self.mappings = {}
        self.highest_num = 0

        # Write file header
        self.f.write('/* ' + os.path.basename(self.filename) + '\n')
        self.f.write(' *\n')
        self.f.write(' * Wireshark - Network traffic analyzer\n')
        self.f.write(' * By Gerald Combs <gerald@wireshark.org>\n')
        self.f.write(' * Copyright 1998 Gerald Combs\n')
        self.f.write(' *\n')
        self.f.write(' * Do not edit - this file is automatically generated\n')
        self.f.write(' * SPDX-License-Identifier: GPL-2.0-or-later\n')
        self.f.write(' */\n\n')
        self.f.write(last_updated_line)

        # Include header files
        self.f.write('#include "config.h"\n\n')
        self.f.write('#include <stddef.h>\n')
        self.f.write('#include <wsutil/array.h>\n')
        self.f.write('#include "enterprises.h"\n')
        self.f.write('\n\n')

    def __del__(self):
        # Write static table
        self.f.write('static const char * const table[] =\n')
        self.f.write('{\n')
        # Largest index
        # Entries (read from dict)
        for n in range(0, self.highest_num+1):
            if n not in self.mappings:
                # There are some gaps, write a NULL entry so can lookup by index
                line = '    NULL'
            else:
                line = '    "' + self.mappings[n] + '"'
            # Add comma.
            if n < self.highest_num:
                line += ','
            # Add number as aligned comment.
            line += ' '*(90-len(line)) + '// ' + str(n)

            self.f.write(line+'\n')

        # End of array
        self.f.write('};\n')
        print('Re-generated', self.filename)

        # Lookup function
        self.f.write(LOOKUP_FUNCTION)

        # Dump function
        self.f.write(DUMP_FUNCTION)

    # Add an individual mapping to the function
    def addMapping(self, num, name):
        # Handle some escapings
        name = name.replace('\\', '\\\\')
        name = name.replace('"', '""')

        # Record.
        self.mappings[num] = name
        self.highest_num = num if num>self.highest_num else self.highest_num



def main():
    parser = argparse.ArgumentParser(description="Create the {} file.".format(ENTERPRISES_CFILE))
    parser.add_argument('--infile')
    parser.add_argument('outfile', nargs='?', default=ENTERPRISES_CFILE)
    parsed_args = parser.parse_args()

    # Read data from file or webpage
    if parsed_args.infile:
        with open(parsed_args.infile, encoding='utf-8') as fh:
            data = fh.read()
    else:
        with urllib.request.urlopen(ENTERPRISE_NUMBERS_URL) as f:
            if f.status != 200:
                raise Exception("request for " + ENTERPRISE_NUMBERS_URL + " failed with result code " + f.status)
            data = f.read().decode('utf-8').replace(u'\u200e', '')

    # Find bits we need and generate enterprise entries
    enterprises_content,last_updated_line = generate_enterprise_entries(data)

    # Now write to a C file the contents (which is faster than parsing the global file at runtime).
    c_file = CFile(parsed_args.outfile, last_updated_line)

    mapping_re = re.compile(r'^(\d+)\s+(.*)$')
    for line in enterprises_content.splitlines():
        match = mapping_re.match(line)
        if match:
            num, name = match.group(1), match.group(2)
            # Strip any comments and/or trailing whitespace
            idx = name.find('#')
            if idx != -1:
                name = name[0:idx]
            name = name.rstrip()
            # Add
            c_file.addMapping(int(num), name)



if __name__ == "__main__":
    main()