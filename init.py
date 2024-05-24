#!/usr/bin/python3
"""
    This files handles the init command and the git
    repository creation.
"""
import os
import configparser


class GitRepo(object):
    """
        We need this class to create an object to handle and store
        basic git repo information and to use the "worktree/.git"
        approach at least
    """
    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False) -> None:
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("Not a git directory {}".format(path))

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")
        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(
                    "Unsupported repositoryformatversion {}".format(vers))


def repo_path(repo, *path):
    """
        find path in repo's git directory
    """
    return os.path.join(repo.gitdir, *path)


def repo_file(repo, *path):
    """

    """
