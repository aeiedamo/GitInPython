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


def main(argv=sys.argv[1:]):
    """
    The main function to run for this program :)
    """
    if len(argv) < 1:
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


argsp = argsubparsers.add_parser("init", help="Create an empty Git directory.")
argsp.add_argument(
    "path",
    metavar="directory",
    nargs="?",
    default=".",
    help="Location of Git repository",
)


def cmd_init(args):
    """
    The base function to run the command.
    """
    repo_create(args.path)


class GitRepo(object):
    """
    This class will create a Git repository object.
    """

    worktree, gitdir, conf = None, None, None

    def __init__(self, path, force=False) -> None:
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("{} is not a git directory.".format(path))

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuation file missing.")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(
                    "Unsupported repository format version: {}".format(vers)
                )


def repo_path(repo, *path):
    """
    find path under a repository.
    """
    return os.path.join(repo.gitdir, *path)


def repo_file(repo, *path, mkdir=False):
    """
    this will create the missing basic Configuation files like
    head, ref, origin and others
    """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)


def repo_dir(repo, *path, mkdir=False):
    """
    same as repo_file but will mkdir the path if mkdir is True
    """
    path = repo_path(repo, *path)
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            return Exception("{} is not a directory.".format(path))

    if mkdir:
        os.makedirs(path)
        return path
    return None


def repo_create(path):
    """
    This function creates the repository base files
    """

    repo = GitRepo(path, True)

    if not (repo.worktree and repo.gitdir):
        raise Exception("Some base git files are missing.")

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception("{} is not a directory.".format(path))
        if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
            raise Exception("{} is not empty".format(path))
    else:
        os.makedirs(repo.worktree)

    assert repo_dir(repo, "branches", mkdir=True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    description = repo_file(repo, "description")

    if not description:
        raise Exception("description file not found.")

    with open(description, "w") as f:
        f.write("Unnamed repository, edit file 'description' to name it\n")

    head = repo_file(repo, "HEAD")

    if not head:
        raise Exception("HEAD file not found.")

    with open(head, "w") as f:
        f.write("ref: refs/heads/main\n")

    conf = repo_file(repo, "config")

    if not conf:
        raise Exception("Configuation file not found")

    with open(conf, "w") as f:
        config = repo_default_config()
        config.write(f)
    return repo


def repo_default_config():
    """
    The base Configuation file content.
    """

    rtn = configparser.ConfigParser()
    rtn.add_section("core")
    rtn.set("core", "repositoryformatversion", "0")
    rtn.set("core", "filemode", "false")
    rtn.set("core", "bare", "false")

    return rtn


def repo_find(path=".", required=True):
    """
    to find the root of the repository.
    """
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".git")):
        return GitRepo(path)
    parent = os.path.realpath(os.path.join(path, ".."))
    if parent == path:
        if required:
            raise Exception("Not a git directory.")
        else:
            return None
    return repo_find(parent, required)
