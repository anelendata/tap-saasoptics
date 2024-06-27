#!/usr/bin/env python3

import sys
import json
import argparse
import singer
from singer import metadata, utils
from tap_saasoptics.client import SaaSOpticsClient
from tap_saasoptics.discover import discover
from tap_saasoptics.sync import sync

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    'token',
    'account_name',
    'server_subdomain',
    'start_date',
    'user_agent'
]


def add_metadata(catalog_dict):
    for stream in catalog_dict["streams"]:
        if catalog_dict["streams"][stream].get("key_properties") is None:
            catalog_dict["streams"][stream]["key_properties"] = ["id"]
        if catalog_dict["streams"][stream].get("metadata") is None:
            metadata = []
            for key in catalog_dict["streams"][stream]["schema"].get("properties", {}).keys():
                metadata.append(
                    {
                        "breadcrumb": [
                            "properties",
                            key,
                        ],
                        "metadata": {
                            "inclusion": "available",
                            # Examples of additional entries
                            # "table-key-properties": ["id"],
                            # "forced-replication-method": "INCREMENTAL",
                            # "valid-replication-keys": ["modified"],
                        },
                    }
                )
                catalog_dict["streams"][stream]["metadata"] = metadata
    return catalog_dict


def do_discover(schema_dir, is_full_sync=False):
    LOGGER.info('Starting discover')
    catalog = discover(schema_dir, is_full_sync)
    catalog_dict = catalog.to_dict()
    # Need to add metadata and key_properties
    catalog_dict = add_metadata(catalog_dict)
    json.dump(catalog_dict, sys.stdout, indent=2)
    LOGGER.info('Finished discover')


@singer.utils.handle_top_exception(LOGGER)
def main():

    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)

    with SaaSOpticsClient(parsed_args.config['token'],
                          parsed_args.config['account_name'],
                          parsed_args.config['server_subdomain'],
                          parsed_args.config['user_agent']) as client:

        is_full_sync = parsed_args.config.get("full_sync", "full_sync")

        if is_full_sync:
            LOGGER.info('Running on full-sync mode')
        else:
            LOGGER.info('Running on incremental-sync mode')

        schema_dir = parsed_args.config.get("schema_dir", "schemas")
        state = {}
        if parsed_args.state:
            state = parsed_args.state

        if parsed_args.discover:
            do_discover(schema_dir, is_full_sync=is_full_sync)
        elif parsed_args.catalog:
            sync(client=client,
                 config=parsed_args.config,
                 catalog=parsed_args.catalog,
                 state=state,
                 is_full_sync=is_full_sync)

if __name__ == '__main__':
    main()
