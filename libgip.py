#!/usr/bin/python3
"""
The main source code for GIP [short for Git In Python] :)
"""

import argparse
import collections
import configparser
from datetime import datetime
import grp
import pwd
from fnmatch import fnmatch
from math import ceil
import os
import sys
import re
import zlib


argparser = argparse.ArgumentParser(description="This is the parser for the arguments")
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

commands = [
    "add",
    "cat-file",
    "check-ignore",
    "checkout",
    "commit",
    "hash-object",
    "init",
    "log",
    "ls-files",
    "ls-tree",
    "rev-parse",
    "rm",
    "show-ref",
    "status",
    "tag",
]
cmd_list = ", ".join(commands)


def main(argv=sys.argv):
    """
    The main function to run for this program :)
    """
    if len(argv) < 2 or argv[1] not in commands:
        return cmd_help()
    args = argparser.parse_args(argv)
    match args.command:
        case "add":
            cmd_add(args)
        case "cat-file":
            cmd_catfile(args)
        case "check-ignore":
            cmd_checkignore(args)
        case "checkout":
            cmd_checkout(args)
        case "commit":
            cmd_commit(args)
        case "hash-object":
            cmd_hashobject(args)
        case "init":
            cmd_init(args)
        case "log":
            cmd_log(args)
        case "ls-files":
            cmd_lsfiles(args)
        case "ls-tree":
            cmd_lstree(args)
        case "rev-parse":
            cmd_revparse(args)
        case "rm":
            cmd_rm(args)
        case "show-ref":
            cmd_showred(args)
        case "status":
            cmd_status(args)
        case "tag":
            cmd_tag(args)
        case "help":
            cmd_help()
        case _:
            print(
                "gip: '{}' is not a gip command. See 'gip --help'.".format(cmd_help())
            )


argsp = argsubparsers.add_parser(
    "help", help="This a command to print the basic manual for help"
)


def cmd_help():
    """
    To offer basic help if no or a wrong command was input.
    """
    print("This is the GIP manual.")
    print("the available commands are [{}].".format(cmd_list))
    print("You can use --help with any of them.")
