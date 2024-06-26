#!/usr/bin/python3
"""
The main source code for GIP [short for Git In Python] :)
"""

import argparse
import collections
import configparser
from datetime import datetime
import grp
from os.path import exists
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
            cmd_showref(args)
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
            raise Exception("{} is not a directory.".format(path))

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

    def __init__(self, data=None):
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

    if not os.path.isfile(path):
        return None

    with open (path, "rb") as f:
        raw = zlib.decompress(f.read())

        # Read object type
        x = raw.find(b' ')
        fmt = raw[0:x]

        # Read and validate object size
        y = raw.find(b'\x00', x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw)-y-1:
            raise Exception("Malformed object {0}: bad length".format(sha))

        # Pick constructor
        match fmt:
            case b'commit' : c=GitCommit
            case b'tree'   : c=GitTree
            case b'tag'    : c=GitTag
            case b'blob'   : c=GitBlob
            case _:
                raise Exception("Unknown type {0} for object {1}".format(fmt.decode("ascii"), sha))

        # Call constructor and return object
        return c(raw[y+1:])


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


def kvlmParse(raw, start=0, dct=None):
    """
    Key-Value List with Messages.
    This function will help with parsing the commit fields.
    """

    if not dct:
        dct = collections.OrderedDict()
    
    spc = raw.find(b' ', start)
    nl = raw.find(b'\n', start)

    if (spc < 0) or (nl < spc):
        assert nl == start
        dct[None] = raw[start+1:]
        return dct
    
    key = raw[start:spc]

    end = start
    while True:
        end = raw.find(b'\n', end+1)
        if raw[end+1] != ord(' '): break

    value = raw[spc+1:end].replace(b'\n ', b'\n')

    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [ dct[key], value ]
    else:
        dct[key]=value

    return kvlmParse(raw, start=end+1, dct=dct)


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


argsp = argsubparsers.add_parser("log", help="Display history of a commit.")
argsp.add_argument("commit", default="HEAD", nargs="?", help="commit to start at")


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
    if not commit or commit.fmt != b"commit":
        raise Exception("The object is not a commit object")
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


argsp = argsubparsers.add_parser("ls-tree", help="print a tree object")
argsp.add_argument(
    "-r", dest="recursive", action="store_true", help="recursive into trees"
)
argsp.add_argument("tree", help="a tree-like object")


def cmd_lstree(args):
    """
    kickstarter for ls-tree command.
    """
    repo = repo_find()
    ls_tree(repo, args.tree, args.recursive)


def ls_tree(repo, ref, recursive=None, prefix=""):
    sha = object_find(repo, ref, fmt=b"tree")
    obj = object_read(repo, sha)
    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type: # Determine the type.
            case b'04': type = "tree"
            case b'10': type = "blob" # A regular file.
            case b'12': type = "blob" # A symlink. Blob contents is link target.
            case b'16': type = "commit" # A submodule
            case _: raise Exception("Weird tree leaf mode {}".format(item.mode))

        if not (recursive and type=='tree'): # This is a leaf
            print("{0} {1} {2}\t{3}".format(
                "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                # Git's ls-tree displays the type
                # of the object pointed to.  We can do that too :)
                type,
                item.sha,
                os.path.join(prefix, item.path)))
        else: # This is a branch, recurse
            ls_tree(repo, item.sha, recursive, os.path.join(prefix, item.path))


class GitTreeLeaf(object):
    """
    This defines a git tree leaf object.
    """

    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha


def tree_parse_one(content, start=0):
    """
    this parser is made to extract a single record.
    """
    x = content.find(b" ", start)
    assert x - start == 5 or x - start == 6
    mode = content[start:x]
    if len(mode) == 5:
        mode = b" " + mode

    y = content.find(b"\x00", x)
    path = content[x + 1 : y]

    sha = format(int.from_bytes(content[y + 1, y + 21], "big"), "040x")
    return (y + 21, GitTreeLeaf(mode, path.decode("utf8"), sha))


def tree_parse(content):
    """
    this will recall the above function recursively.
    """

    pos = 0
    max = len(content)
    rtn = list()
    while pos < max:
        pos, data = tree_parse_one(content, pos)
        rtn.append(data)

    return rtn


def TreeLeaf_SortKey(leaf):
    """
    this is an edit due some problems with sorting in python3
    """
    if leaf.mode.startwith(b"10"):
        return leaf.path
    else:
        return leaf.path + "/"


def tree_serialize(obj):
    """
    to serialize and turn object to sha.
    """

    obj.items.sort(key=TreeLeaf_SortKey)
    rtn = b""
    for i in obj.items:
        rtn += i.mode
        rtn += b" "
        rtn += i.path.encode("utf8")
        rtn += b"\x00"
        sha = int(i.sha, 16)
        rtn += sha.to_bytes(20, byteorder="big")
    return rtn


class GitTree(GitObject):
    """
    defines a git tree object.
    """

    fmt = b"tree"

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()


argsp = argsubparsers.add_parser(
    "checkout", help="checkout a commit inside of a directory"
)
argsp.add_argument("commit", help="The commit to checkout")
argsp.add_argument("path", help="the empty directory to checkout on")


def cmd_checkout(args):
    """
    a kickstarter function
    """
    repo = repo_find()
    obj = object_read(repo, object_find(repo, args.commit))

    if not obj:
        raise Exception("No object was found")

    if obj.fmt == b"commit":
        obj = object_read(repo, obj.kvlm[b"tree"].decode("ascii"))

    if os.os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory: {}".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty: {}".format(args.path))
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))


def tree_checkout(repo, tree, path):
    for item in tree.items:
        obj = object_read(repo, item.sha)
        dest = os.path.join(path, item.path)

        if obj.fmt == b"tree":
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b"blob":
            with open(dest, "wb") as f:
                f.write(obj.blobdata)


def ref_resolve(repo, ref):
    """
    To evaluate the ref name.
    """
    path = repo_file(repo, ref)

    if not os.path.isfile(path):
        return None

    with open(path, "r") as f:
        data = f.read()[:-1]
    if data.startwith("ref:"):
        return ref_resolve(repo, data[5:])
    else:
        return data


def ref_list(repo, path=None):
    """
    to collect refs and store them in a dict
    """
    if not path:
        path = repo_dir(repo, "refs")
    rtn = collections.OrderedDict()
    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)
        if os.path.isdir(can):
            rtn[f] = ref_list(repo, can)
        else:
            rtn[f] = ref_resolve(repo, can)
    return rtn


argsp = argsubparsers.add_parser("show-ref", help="list references")


def cmd_showref(args):
    """
    kickstrter to show ref
    """

    repo = repo_find()

    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def show_ref(repo, refs, with_hash=True, prefix=""):
    """
    The actual function to show refs
    """
    for k, v in refs.items():
        if isinstance(v, str):
            print(
                "{}{}{}".format(
                    v + " " if with_hash else "", prefix + "/" if prefix else "", k
                )
            )
        else:
            show_ref(
                repo,
                v,
                with_hash=with_hash,
                prefix="{}{}{}".format(prefix, "/" if prefix else "", k),
            )


class GitTree(GitCommit):
    """
    This will define the Git Tag class object.
    """

    fmt = b"tag"


argsp = argsubparsers.add_parser("tag", help="List and create tags")
argsp.add_argument(
    "-a", action="store_true", dest="create_tag_object", help="to create a tag"
)
argsp.add_argument("name", nargs="?", help="tag's name")
argsp.add_argument("object", default="HEAD", nargs="?", help="The object to point to")


def cmd_tag(args):
    """
    kickstarter for tag command.
    """
    repo = repo_find()

    if args.name:
        tag_create(
            repo,
            args.name,
            args.object,
            type="object" if args.create_tag_object else "ref",
        )
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def tag_create(repo, name, ref, create_tag_object=False):
    """
    To call when in need to create a tag object
    """
    sha = object_find(repo, ref)

    if create_tag_object:
        tag = GitTag(repo)

        tag.kvlm = collections.OrderedDict()
        tag.kvlm[b"object"] = sha.encode()
        tag.kvlm[b"type"] = b"commit"
        tag.kvlm[b"tag"] = name.encode()
        tag.kvlm[b"tagger"] = b"gip <gip@gip.org>"
        tag.kvlm[None] = b"filler message when creating a tag."
        tag_sha = object_write(tag)

        ref_create(repo, "tags/" + name, tag_sha)

    else:
        ref_create(repo, "tags/" + name, sha)


def ref_create(repo, ref_name, sha):
    """
    To create a ref.
    """
    with open(repo_file(repo, "refs/" + ref_name), "w") as f:
        f.write(sha + "\n")
