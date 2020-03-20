#!/usr/bin/env python3

import argparse
import random
import sys
import textwrap
import yaml


SEATS = {
    'A': 92,
    'B': 90,
    'D': 120,
    'E': 36,
    'F': 24,
    'G': 88,
    'H': 88,
    'O': 88,
}


def warning(*objs):
    print(*objs, file=sys.stderr)


def set_up_argparser():
    ap = argparse.ArgumentParser(
        description='Randomly assign students to NARGA venues'
    )
    ap.add_argument(
        '-o', '--occupancy',
        default=[14, 15],
        metavar=('NUMERATOR', 'DENOMINATOR'),
        nargs=2,
        type=int,
        help='''two integers specifying the ratio of seats used to seats
                available'''
    )
    ap.add_argument(
        '-f', '--fix-venues',
        default=0,
        metavar='NUM_VENUES',
        type=int,
        help='''fix the first NUM_VENUES venues to the exact ratio, with
                spillover added to remaining venues'''
    )
    ap.add_argument(
        'class_list_file',
        help='''the file that contains the list of student numbers, one student
                number per line'''
    )
    ap.add_argument(
        'assessment_id',
        help='''the HTML identifier of the assessment opportunity'''
    )
    ap.add_argument(
        'venues',
        metavar='venue',
        nargs='+',
        help='''the venues, in the order they must be filled'''
    )
    return ap


def main():
    # evaluate and check command-line arguments
    args = set_up_argparser().parse_args()
    venues = [v.upper() for v in args.venues]
    cfilename = args.class_list_file
    aid = args.assessment_id

    num, den = args.occupancy
    if num < 0 or den < 1:
        warning('Invalid occupancy specified: {}/{}'.format(num, den))
        return 1
    occupancy = num / den

    invalid_rooms = set(venues) - set(SEATS.keys())
    if len(invalid_rooms) > 0:
        plural = 's' if len(invalid_rooms) > 1 else ''
        warning('Invalid room{1}: {0}'.format(', '.join(invalid_rooms), plural))
        return 1

    # collect venue details
    capacities = [round(SEATS[v] * occupancy) for v in venues]

    # collect and shuffle student numbers
    try:
        with open(cfilename, 'r') as r:
            numbers = [n.strip() for n in r.readlines()]
    except IOError as e:
        warning('{}: {}'.format(e.strerror, e.filename))
        return 1

    if len(numbers) > sum(capacities):
        if args.fix_venues > 0:
            diff = len(numbers) - sum(capacities)
            spill = round(diff / len(capacities[args.fix_venues:]))
            for i in range(args.fix_venues, len(capacities)):
                capacities[i] += spill
        else:
            msg = 'Not enough seats: {} required, {} available'
            warning(msg.format(len(numbers), sum(capacities)))
            return 1

    random.shuffle(numbers)

    # collect
    assignments = []
    start = 0
    for venue_name, capacity in zip(venues, capacities):
        end = min(start + capacity, len(numbers))
        venue = {}
        venue['name'] = 'NARGA ' + venue_name
        venue['students'] = [n for n in sorted(numbers[start:end])]
        assignments.append(venue)
        start = end

    # display
    for venue in assignments:
        print('{} ({} students)'.format(venue['name'],
                                        len(venue['students'])))
        print('\n'.join(textwrap.wrap(' '.join(venue['students']), width=80)))
        print()

    # write as YAML
    output = yaml.dump(assignments)
    with open(aid + '_venue_assignments.yaml', 'w') as f:
        f.write(output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
