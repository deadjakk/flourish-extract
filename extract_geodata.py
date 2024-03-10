#!/usr/bin/env python
from re import findall
from requests import get
from argparse import ArgumentParser
import logging
from json import JSONDecoder, dumps
logging.basicConfig(level=logging.DEBUG)


def extract_json_objects(text, decoder=JSONDecoder()):
    """Find JSON objects in text, and yield the decoded JSON data

    Does not attempt to look for JSON arrays, text, or other JSON types outside
    of a parent JSON object.

    """
    pos = 0
    while True:
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            result, index = decoder.raw_decode(text[match:])
            yield result
            pos = match + index
        except ValueError:
            pos = match + 1


def get_coords_from_embed(web_content):
    json_items = extract_json_objects(str(web_content))
    dict_items = [ item for item in json_items if isinstance(item, dict) ]
    coords = [ item for item in dict_items if 'lat' in item.keys() ]
    return coords


def get_fourish_urls(url):
    matches = findall('[fF]lo[.a-z0-9]+\\.sh/visualisation/[0-9]+', url)
    if matches:
        logging.info("provided url is an embed url, using it")
        return matches

    resp = get(args.url)
    logging.debug(f"response from {args.url}: {resp.status_code}")

    if resp.status_code != 200:
        logging.error(f"unsuccessful request, status code: {resp.status_code}")
        exit(1)

    data = resp.content
    matches = findall('[fF]lo[.a-z0-9]+\\.sh/visualisation/[0-9]+', str(data))


parser = ArgumentParser()
parser.add_argument("url", help="url of the page with the embedded flourish map")
args = parser.parse_args()

matches = get_fourish_urls(args.url)
if not matches:
    logging.error("flourish urls not found in returned web content, exiting")
    exit(2)

logging.info(f"{len(matches)} 2 flourish map sources found")
for match in matches:
    built_url = f"https://{match}/embed"
    logging.debug(f"making request to {built_url}")
    resp = get(built_url)
    if resp.status_code != 200:
        logging.error(f"unsuccessful request {built_url}, status code: {resp.status_code}, skipping")
        continue
    coords = None
    try:
        coords = get_coords_from_embed(resp.content)
    except Exception as e:
            logging.error(f"could not parse coords for {built_url}, skipping")
            continue

    name = findall('[0-9]+', match)[0]
    filename = f"{name}_coordinates.json"
    if not coords:
        logging.warning(f"no coordinates found for {built_url}")
        continue
    with open(filename,'w') as fh:
        written = fh.write(dumps(coords))
        logging.info(f"wrote {written} to {filename} for {built_url}")
