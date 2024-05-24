#!/usr/bin/python3
"""
    This is the main code and library for gip [Git In Python]
"""
import argparse
import collections
import configparser
from datetime import datetime
import grp
import pwd
from fnmatch import fnmatch
import hashlib
from math import ceil
import os
import re
import zlib


argparser = argparse.ArgumentParser(
    description="To help with parsing arguments")
argsubparser = argparser.add_subparsers(title="Commands", dest="command")
argsubparser.required = True


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    match args.command:
        case "add": cmd_add(args)
        case "cat-file": cmd_catfile(args)
        case "check-ignore": cmd_checkignore(args)
        case "checkout": cmd_checkout(args)
        case "commit": cmd_commit(args)
        case "hash-object": cmd_hashobject(args)
        case "init": cmd_init(args)
        case "log": cmd_log(args)
        case "ls-files": cmd_lsfiles(args)
        case "ls-trees": cmd_lstrees(args)
        case "rev-parse": cmd_revparse(args)
        case "rm": cmd_rm(args)
        case "show-ref": cmd_showref(args)
        case "status": cmd_status(args)
        case "tag": cmd_tag(args)
        case _: print("Wrong Command!")
