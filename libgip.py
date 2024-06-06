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
import hashlib

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


argsp = argsubparsers.add_parser("cat-file", help="Display the content of a Git object")
argsp.add_argument(
    "type",
    metavar="type",
    choices=["blob", "commit", "tag", "tree"],
    help="Specify the type of object",
)
argsp.add_argument("object", metavar="object", help="The object to display")


def cmd_catfile(args):
    """
    The main function of cat-file command.
    """
    repo = repo_find()
    catfile(repo, args.object, fmt=args.type.encode())


def catfile(repo, obj, fmt=None):
    """
    This function prints all content to stdout.
    """
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    if not obj:
        raise Exception("Object wasn't found")
    sys.stdout.buffer.write(obj.serialize())


def object_find(repo, name, fmt=None, follow=True):
    """
    This will only print name for now.
    """
    return name


class GitObject(object):
    """
    This class will create a Git object
    """

    def __init__(self, data=None) -> None:
        if data:
            self.deserialize(data)
        else:
            self.init()

    def serialize(self, repo):
        raise Exception("Unimplemented")

    def deserialize(self, data):
        raise Exception("Unimplemented")

    def init(self):
        pass


def object_read(repo, sha):
    """
    to read the object's sha from git repo.
    """
    path = repo_file(repo, "objects", sha[0:2], sha[2:])

    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        content = zlib.decompress(f.read())
        x = content.find(b" ")
        fmt = content[0:x]
        y = content.find(b"\x00", x)
        size = int(content[x:y].decode("ascii"))
        if size != len(content) - y - 1:
            raise Exception("Malformed object {}: bad lenth".format(sha))

        match fmt:
            case b"commit":
                c = GitCommit
            case b"tree":
                c = GitTree
            case b"tag":
                c = GitTag
            case b"blob":
                c = GitBlob
            case _:
                raise Exception(
                    "Unkown type {} for object {}".format(fmt.decode("ascii"), sha)
                )
        return c(content[y + 1 :])


def object_write(obj, repo=None):
    """
    function to write object's hash representation.
    """
    data = obj.serialize()
    result = obj.fmt + b" " + str(len(data)).encode() + b"\x00" + data

    sha = hashlib.sha1(result).hexdigest()
    if repo:
        path = repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not path:
            raise Exception("path not found.")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(zlib.compress(result))
    return sha


class GitBlob(GitObject):
    """
    This defines a GitBlob object.
    """

    fmt = b"blob"

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data


argsp = argsubparsers.add_parser("hash-object", help="Compute object id and sha")

argsp.add_argument(
    "-t",
    metavar="type",
    dest="type",
    choices=["blob", "commit", "tag", "tree"],
    default="blob",
    help="Specify the type of object",
)

argsp.add_argument(
    "-w", dest="write", action="store_true", help="write Object to database"
)

argsp.add_argument("path", help="Read object from <file>")


def cmd_hashobject(args):
    """
    The base kickstarter for hash-object
    """
    if args.write:
        repo = repo_find()
    else:
        repo = None

    with open(args.path, "rb") as f:
        sha = object_hash(f, args.type.encode(), repo)
        print(sha)


def object_hash(f, fmt, repo=None):
    """
    to hash an object, to write it to repository if needed
    """
    data = f.read()

    match fmt:
        case b"commit":
            obj = GitCommit(data)
        case b"tree":
            obj = GitTree(data)
        case b"tag":
            obj = GitTag(data)
        case b"blob":
            obj = GitBlob(data)
        case _:
            raise Exception("Unknown type: {}".format(fmt))
    return object_write(obj, repo)


argsp = argsubparsers.add_parser("log", help="Display history of a commit.")
argsp.add_argument("commit", default="HEAD", nargs="?", help="commit to start at")


class GitCommit(GitObject):
    """
    this defines the class git commit and creates its objects.
    """

    fmt = b"commit"

    def deserialize(self, data):
        self.kvlm = kvlmParse(data)

    def serialize(self):
        return kvlmSerialize(self.kvlm)

    def init(self):
        self.kvlm = dict()


def kvlmParse(content, start=0, dct=None):
    """
    Key-Value List with Messages.
    This function will help with parsing the commit fields.
    """

    if not dct:
        dct = collections.OrderedDict()

    space = content.find(b" ", start)
    newLine = content.find(b"\n", start)

    if space < 0 or newLine < space:
        assert newLine == start
        dct[None] = content[start + 1 :]
        return dct

    key = content[start:space]
    end = start

    while True:
        end = content.find(b"\n", end + 1)
        if content[end + 1] != ord(" "):
            break

    value = content[space + 1 : end].replace(b"\n ", b"\n")

    if key in dct:
        if isinstance(dct[key], list):
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlmParse(content, start=end + 1, dct=dct)


def kvlmSerialize(kvlm):
    """
    to write similar objects like the above function.
    """

    rtn = b""

    for k in kvlm.keys():
        if k is None:
            continue
        value = kvlm[k]
        if not isinstance(value, list):
            value = [value]
        for v in value:
            rtn += k + b" " + v.replace(b"\n", b"\n ") + b"\n"

    rtn += b"\n" + kvlm[None] + b"\n"

    return rtn


def cmd_log(args):
    """
    kickstarter for log command.
    """
    repo = repo_find()
    print("base giplog:\t")
    log_graphiz(repo, object_find(repo, args.commit), set())
    print()


def log_graphiz(repo, sha, seen):
    """
    We will use graphiz software to show log in a graphical representation.
    """
    if sha in seen:
        return
    seen.add(sha)
    commit = object_read(repo, sha)
    if not commit:
        raise Exception("commit not found")
    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace('"', '\\"')

    if "\n" in message:
        message = message[: message.index("\n")]

    print('\tc_{} [label="{}: {}"]'.format(sha, sha[0:7], message))
    assert commit.fmt == b"commit"

    if b"parent" not in commit.kvlm.keys():
        return

    parents = commit.kvlm[b"parent"]

    if not isinstance(parents, list):
        parents = [parents]

    for p in parents:
        if not p:
            raise Exception("parent not found.")
        p = p.decode("ascii")
        print("\tc_{} -> c_{}".format(sha, p))
        print("\n\t", "-" * 100, "\n")
        log_graphiz(repo, p, seen)
