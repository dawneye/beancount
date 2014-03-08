"""Try to automatically convert a V1 ".ledger" beancount input file to the newer
".beancount" V2 syntax.
"""
import sys
import re
import datetime


def unquote(s):
    return s.replace('"', "'")

def add_strings(line):
    mo = re.match('^((?:\d\d\d\d-\d\d-\d\d)(?:=\d\d\d\d-\d\d-\d\d)? .) (?:(.+?)[ \t]*\|)?(.*)$', line)
    if mo:
        dateflag, payee, desc = mo.groups()
        payee = (unquote(payee).strip() if payee else payee)
        desc = unquote(desc).strip()
        if mo.group(2) is None:
            return '{} "{}"\n'.format(dateflag, desc)
        else:
            return '{} "{}" | "{}"\n'.format(dateflag, payee, desc)
    else:
        return line

def convert_certain_commodities(line):
    line = re.sub('\bMiles\b', 'MILES', line)
    line = re.sub('\bHsbcPoints\b', 'HSBCPTS', line)
    line = re.sub('\bFidoDollars\b', 'FIDOPTS', line)
    line = re.sub('\bAmtrak\b', 'AMTRAKPTS', line)
    return line

def convert_var_directive(line):
    mo = re.match('@var ofx accid\s+([^ ]+)\s+(.*)', line)
    if mo:
        return ';;accid "{}" {}\n'.format(mo.group(1), mo.group(2))
    else:
        return line

def convert_defcomm_directive(line):
    mo = re.match('@defcomm', line)
    if mo:
        return ';%s' % line
    else:
        return line

def convert_tags(line):
    mo = re.match('(@(?:begin|end)tag)\s+(.*)', line)
    if mo:
        return '{} "{}"\n'.format(mo.group(1), mo.group(2).strip())
    else:
        return line

def unindent_comments(line):
    mo = re.match(r'\s+(;.*)', line)
    if mo:
        return '{}\n'.format(mo.group(1))
    else:
        return line

def convert_quoted_currencies(line):
    return re.sub('"(CRA1|JDU.TO|NT.TO|NT.TO1|AIS\d+|RBF\d+|NBC\d+|H107659)"', "\\1", line)

def convert_location(line):
    mo = re.match('@location\s+([\d-]+)\s+(.*)', line)
    if mo:
        return '@event {} "location" "{}"\n'.format(mo.group(1), mo.group(2))
    else:
        return line

def convert_directives(line):
    return re.sub('@(defaccount|var|pad|check|begintag|endtag|price|location|event)', '\\1', line)

def swap_directives_into_events(line):
    return re.sub('(check|pad|location|price|event)\s+(\d\d\d\d-\d\d-\d\d)', '\\2 \\1', line)

def defaccount_to_open(line):
    mo = re.match('^defaccount\s+(D[re]|Cr)\s+([A-Za-z0-9:\-_]+)\s*(.*)\n', line)
    if mo:
        return '1970-01-01 open {:64} {}\n'.format(
            mo.group(2).strip(),
            mo.group(3) or '')
    else:
        return line

def uncomment_tentative(line):
    mo = re.match('^;@([a-z]+)\s+(\d\d\d\d-\d\d-\d\d)\s*(.*)', line)
    if mo:
        return '{} {} {}\n'.format(mo.group(2), mo.group(1), mo.group(3))
    else:
        return line

def add_org_mode_section(line):
    mo = re.match('^;;;;; (.*)', line)
    if mo:
        return '* {}\n'.format(mo.group(1))
    else:
        return line

def remove_datepair(line):
    mo = re.match('^(\d\d\d\d-\d\d-\d\d)=(\d\d\d\d-\d\d-\d\d) (.*)', line)
    if mo:
        return '{} {} {{{}}}\n'.format(*mo.group(1,3,2))
    else:
        return line

def convert_tags(line):
    if re.match('(begintag|endtag)', line):
        return re.sub('(begintag|endtag)\s+(.*)', '\\1 #\\2', line)
    else:
        return line

def check_to_check_after(line):
    mo = re.match('(\d\d\d\d)-(\d\d)-(\d\d) check (.*)', line)
    if mo:
        d = datetime.date(*list(map(int, mo.group(1,2,3))))
        d += datetime.timedelta(days=1)
        return '{:%Y-%m-%d} check {}\n'.format(d, mo.group(4))
    else:
        return line

def tags_begin_to_push(line):
    mo = re.match('^(begin|end)tag', line)
    if mo:
        newtag = 'push' if mo.group(1) == 'begin' else 'pop'
        return re.sub('(begin|end)', newtag, line)
    else:
        return line


def main():
    import argparse, logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s: %(message)s')
    parser = argparse.ArgumentParser(__doc__.strip())
    parser.add_argument('filename', help='Filenames')
    opts = parser.parse_args()

    lines = open(opts.filename).readlines()
    lines = map(remove_datepair, lines)
    lines = map(add_strings, lines)
    lines = map(convert_certain_commodities, lines)
    lines = map(convert_var_directive, lines)
    lines = map(convert_defcomm_directive, lines)
    lines = map(convert_tags, lines)
    lines = map(unindent_comments, lines)
    lines = map(convert_quoted_currencies, lines)
    lines = map(convert_location, lines)
    lines = map(convert_directives, lines)
    lines = map(swap_directives_into_events, lines)
    lines = map(defaccount_to_open, lines)
    lines = map(uncomment_tentative, lines)
    lines = map(add_org_mode_section, lines)
    lines = map(convert_tags, lines)
    lines = map(check_to_check_after, lines)
    lines = map(tags_begin_to_push, lines)

    for line in lines:
        sys.stdout.write(line)


if __name__ == '__main__':
    main()
