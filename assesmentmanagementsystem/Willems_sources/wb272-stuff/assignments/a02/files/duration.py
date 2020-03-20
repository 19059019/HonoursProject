#!/usr/bin/env python3

def end_time():
    time_start = int(input('Start time: '))
    duration = int(input('Duration: '))
    time_end = (time_start // 100) * 60 + (time_start % 100) + duration
    return '{0:02}{1:02}'.format((time_end // 60) % 24, time_end % 60)

if __name__ == '__main__':
    print(end_time())
