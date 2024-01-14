#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import re
import logging
from datetime import datetime
from threading import Thread
from typing import Iterator
from http.server import HTTPServer, BaseHTTPRequestHandler

# - gauge will be held in global metrics variable
# - read gpuz.txt (output) file in different thread.
# - everytime a new line is read, metrics variable will be prepared and saved.
# - when GET request is, the metrics variable will be sent as response.

first_line = None
raw_metrics = None
metrics = None


def parse_txt(first_line, raw_metrics):
    header_parts = first_line.split(',')
    # print("header_parts[0]: '{}'".format(header_parts[0].strip()))
    # print("len1: ", len(header_parts)) # 32
    metric_parts = raw_metrics.split(',')
    # print("len2: ", len(metric_parts))

    metrics_new = []
    count = len(header_parts)
    for i in range(count):
        metric_help = header_parts[i].strip()
        if len(metric_help) == 0:
            continue
        (localized_src_name, src_units) = split_help(metric_help)
        metric_name = prepare_metric_name(localized_src_name)
        metric_data = metric_parts[i].strip()
        if src_units == "timestamp":
            metric_data = parse_date(metric_data)
        line = "# HELP {} {}".format(metric_name, metric_help)
        metrics_new.append(line)
        line = "# TYPE {} gauge".format(metric_name)
        metrics_new.append(line)
        tags = prepare_tags(localized_src_name, src_units)
        line = "{}{} {}".format(metric_name, tags, metric_data)
        metrics_new.append(line)

    # print("metrics_new:", metrics_new)
    return metrics_new


def parse_date(metric_data):
    # 2024-01-14 19:00:11
    # %y-%m-%d %H:%M:%S
    dt_obj = datetime.strptime(metric_data, '%Y-%m-%d %H:%M:%S')
    return int(time.mktime(dt_obj.timetuple()))


def split_help(metric_help):
    parts = metric_help.split('[')
    if len(parts) > 1:
        localized_src_name = parts[0].strip()
        src_units = parts[1].split(']')[0]
        return localized_src_name, src_units
    return parts[0].strip(), "timestamp"


def prepare_metric_name(metric_help):
    # return re.sub(r' ', '_', metric_help).lower()
    metric_name = re.sub(r' ', '_', metric_help).lower()
    metric_name = re.sub(r'[^A-Za-z0-9_]', '', metric_name)
    metric_name = re.sub(r'__', '_', metric_name)
    metric_name = 'gpuz_' + metric_name
    return metric_name


def prepare_tags(localized_src_name, src_units):
    return '{{localizedSrcName="{}",srcUnits="{}"}}'.format(localized_src_name, src_units)


class MyHttpRequestHandler(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

    def do_GET(self):
        # https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7
        # logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        global metrics
        # print("metrics 2: ", metrics)
        self._set_response()
        self.wfile.write(metrics)


class MyHttpServer(HTTPServer):
    file_pointer = None

    def __init__(self, server_address, file_name, handler_class=MyHttpRequestHandler):
        super().__init__(server_address, handler_class)
        # https://stackoverflow.com/questions/51363497/httpserver-run-requires-a-basehttprequesthandler-class-instead-an-object
        self.file_pointer = open(file_name, 'r')


def follow(file, sleep_sec=0.7) -> Iterator[str]:
    """ Yield each line from a file as they are written.
    `sleep_sec` is the time to sleep after empty reads. """
    line = ''
    while True:
        tmp = file.readline()
        if tmp is not None and tmp != "":
            line += tmp
            if line.endswith("\n"):
                yield line
                line = ''
        elif sleep_sec:
            time.sleep(sleep_sec)


def threaded_function(file_name):
    global first_line, raw_metrics, metrics
    # https://stackoverflow.com/a/54263201
    with open(file_name, mode='r', encoding="ISO-8859-1") as file:
        for line in follow(file):
            if line.startswith('        Date        '):
                first_line = line
            else:
                raw_metrics = line
            # print("first_line 1: ", first_line)
            # print("metrics 1: ", metrics)
            if (first_line is not None) and (raw_metrics is not None):
                metrics_new = parse_txt(first_line, raw_metrics)
                output = '\n'.join(metrics_new) + '\n'
                metrics = output.encode()


def run(port=9184, file_name='gpuz.txt'):
    logging.basicConfig(level=logging.INFO)
    logging.info('Starting tail...\n')
    thread = Thread(target=threaded_function, args=(file_name,))
    thread.start()

    httpd = MyHttpServer(server_address=('', port), file_name=file_name)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')
    thread.join(0.1)
    logging.info('shutdown complete...\n')


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        run(port=int(argv[1]), file_name=argv[2])
    else:
        run()
