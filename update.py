#!/usr/bin/env python3
'''
Helper script to convert Google form responses
(exported from Google Spreadsheet via File -> Download as -> Tab-separated values)
to Markdown table rendered in README.md

Example invocation:

./update.py ~/Downloads/Kubernetes\ on\ AWS-\ User\ Survey\ \(Responses\)\ -\ Form\ responses\ 1.tsv
'''

import argparse
import csv
import json
import re

COLUMN_MAPPING = {
    'Timestamp': 'time',
    'Your Company/Organization': 'organization_name',
    'Your Company/Organization Website': 'organization_url',
    'What kind of workload are you running on Kubernetes on AWS at the moment?': 'workload',
    'How do you provision/run Kubernetes on AWS?': 'provisioning',
    'Do you have public information about your Kubernetes on AWS usage?': 'more_info',
    'Your Location': 'location'
}

VALUE_MAPPING = {
    'None: we are not running Kubernetes on AWS at all, not even a proof of concept (POC).': 'none',
    'Proof of concept: we are in the proof of concept phase for Kubernetes on AWS.': 'proof of concept',
    'Development/test/staging: we are using Kubernetes on AWS for dev/test/staging environments.': 'dev/test/staging',
    'Internal tooling/services or non-critical apps: we are running internal applications on Kubernetes on AWS, outages are not business critical.': 'internal/non-critical apps',
    'Critical business applications: we are running critical production workloads on Kubernetes on AWS.': 'critical business apps',
}

LINK = re.compile(r'(https?://)(\S+\b/?)([!"#$%&\'()*+,\-./:;<=>?@[\\\]^_`{|}~]*)(\s|$)', re.I)


def replace(match):
    return '[{1}]({0}{1}{2}){3}'.format(*match.groups())


parser = argparse.ArgumentParser()
parser.add_argument('tsvfile')
args = parser.parse_args()

rows = []

with open(args.tsvfile) as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter='\t')
    for tsvrow in reader:
        row = {}
        for column_name, key in COLUMN_MAPPING.items():
            value = tsvrow[column_name]
            value = VALUE_MAPPING.get(value, value)
            if key == 'organization_url' and value and not value.startswith('http'):
                # fix website URL
                value = 'http://{}'.format(value)
            row[key] = value
        rows.append(row)

rows.sort(key=lambda r: r['organization_name'].lower())

with open('form-responses.json', 'w') as fd:
    json.dump(rows, fd, sort_keys=True)

with open('README.md') as fd:
    template = fd.read()

lines = [
    '| Organization | Workload (K8s on AWS) | Provisioning | More Info | Location |',
    '|---|---|---|---|---|'
]
for row in rows:
    for key, val in row.items():
        if key in ('provisioning', 'more_info'):
            # shorten link display
            row[key] = LINK.sub(replace, val)
    lines.append('| [{organization_name}]({organization_url}) | {workload} | {provisioning} | {more_info} | {location} |'.format(**row))

table = '\n'.join(lines)

contents = re.sub(r'(^<!-- TABLE_START -->$).*(^<!-- TABLE_END -->$)', '\\1\n{}\n\\2'.format(table), template, flags=re.DOTALL | re.MULTILINE)

with open('README.md', 'w') as fd:
    fd.write(contents)
