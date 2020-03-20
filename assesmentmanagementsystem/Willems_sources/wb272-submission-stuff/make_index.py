#!/usr/bin/env python3

import datetime
import jinja2
import os
import sys
import yaml


HTML_TEMPLATE_FILENAME = 'index.template.html'


def format_datetime(dt):
    return dt.strftime('%A, %-d %B %Y, %H:%M')


def format_date(dt):
    return dt.strftime('%b, %-d')


def format_duration(mins):
    if mins < 60:
        return '{} minutes'.format(mins)
    else:
        hours = mins // 60
        hourfrac = mins / 60
        if hours != hourfrac:
            hours = hourfrac
        return '{} hours'.format(hours)


def emit(assessments, out_filename,
         template_filename=HTML_TEMPLATE_FILENAME):

    # set up jinja
    env = jinja2.Environment(loader = jinja2.FileSystemLoader('.'),
                             trim_blocks = True,
                             lstrip_blocks = True)
    env.filters['format_date'] = format_date
    env.filters['format_datetime'] = format_datetime
    env.filters['format_duration'] = format_duration
    template = env.get_template(template_filename)

    # write
    with open(out_filename, 'w') as f:
        f.write(template.render(assessments=assessments))


def main(argv):
    # load setup
    with open('assessments.yaml', 'r') as stream:
        assessments = yaml.load(stream)

    # attach venue assignments
    for ass in assessments:
        print(ass)
        vaname = ass['anchor'] + '_venue_assignments.yaml'
        if os.path.exists(vaname):
            with open(vaname, 'r') as stream:
                venue_assignments = yaml.load(stream)
            ass['venues'] = venue_assignments
        else:
            print('No venue assignment at ' + vaname)

    emit(assessments, 'index.html')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
