import math
import os
import subprocess
import util

linear_scalar = lambda x: int(x)
log_scalar = lambda x: math.log(1+int(x))

class GitRepoDifferBase(object):
    def run_git_diff(self, project, options):
        raise NotImplemented

    # Returns a "score" of the diff, which is an arbitrary object such that, given two of them,
    # the "smaller" diff is the one that is less-than the other.
    def calculate_diff(self, project, ignore_spaces=False):
        options = []

        if ignore_spaces:
            options.extend(['--ignore-blank-lines', '--ignore-space-at-eol'])

        return self.run_git_diff(project, options)

class GitRepoDifferRankLines(GitRepoDifferBase):
    def run_git_diff(self, project, options):
        options = options or []
        diff = project.git_repo.run(['diff', '--shortstat'] + options)

        # Get the numbers from something like "3 files changed, 148 insertions(+), 15 deletions(-)"
        files, insertions, deletions = [int(x.split()[0]) for x in diff.split(',')]

        # To rank a "better" git-diff, we order by:
        #  1. the fewest lines changed (either added or deleted)
        #  2. then, if that's equal, we want to touch fewer files
        #  3. then, if that's still equal, we'd prefer to delete than insert.

        return (max(insertions, deletions), files, abs(insertions-deletions))

class GitRepoDifferRankFiles(GitRepoDifferRankLines):
    def run_git_diff(self, project, options):
        result = GitRepoDifferRankLines.run_git_diff(self, project, options)
        return result[1], result[0], result[2]

class GitRepoDifferByFile(GitRepoDifferBase):
    def __init__(self):
        super(GitRepoDifferByFile, self).__init__()
        self.scalar = linear_scalar

    def run_git_diff(self, project, options):
        options = options or []

        diff = project.git_repo.run(['diff', '--numstat'] + options)

        # turn into list of (insertions, deletions, filename)
        stats = [line.split('\t') for line in diff.split('\n') if line]

        files = len(stats)
        maxid = sum(max(self.scalar(s[0]),self.scalar(s[1])) for s in stats)
        delta = sum(abs(self.scalar(s[0])-self.scalar(s[1])) for s in stats)

        # To rank a "better" git-diff, we order by:
        #  1. the fewest lines changed (either added or deleted)
        #  2. then, if that's equal, we want to touch fewer files
        #  3. then, if that's still equal, we'd prefer to delete than insert.

        return (maxid, files, delta)

class GitRepoDifferByFileLog(GitRepoDifferByFile):
    def __init__(self):
        super(GitRepoDifferByFileLog, self).__init__()
        self.scalar = log_scalar


class GitRepoDifferWords(GitRepoDifferBase):
    def __init__(self):
        super(GitRepoDifferWords, self).__init__()
        self.scalar = linear_scalar

    def run_git_diff(self, project, options):
        options = options or []
        diff = project.git_repo.run(['diff', '--word-diff=porcelain', '-U0', '--word-diff-regex=.'] + options)

        delta = {}
        cur_file = None
        for line in diff.splitlines():
            if line[0]=='+':
                delta[cur_file]['+'] += self.scalar(len(line))
            elif line[0]=='-':
                delta[cur_file]['-'] += self.scalar(len(line))
            elif line.startswith('diff'):
                cur_file = line
                delta[cur_file] = {'+': 0, '-': 0}

        head = list(delta.itervalues())[0]

        files = len(delta)
        maxid = sum(max(self.scalar(s['+']),self.scalar(s['-'])) for s in delta.itervalues())
        delta = sum(abs(self.scalar(s['+'])-self.scalar(s['-'])) for s in delta.itervalues())

        return (maxid, files, delta)

class GitRepoDifferWordsLog(GitRepoDifferWords):
    def __init__(self):
        super(GitRepoDifferWordsLog, self).__init__()
        self.scalar = log_scalar

diff_options = {
    'words': GitRepoDifferWords,
    'words-log': GitRepoDifferWordsLog,
    'lines': GitRepoDifferRankLines,
    'files': GitRepoDifferRankFiles,
    'hybrid': GitRepoDifferByFile,
    'hybrid-log': GitRepoDifferByFileLog,
}
diff_default = 'words-log'

class GitRepo(object):
    def __init__(self, path, context):
        self.path = path
        self.context = context

    # Helpers to run git commands.

    def check(self, subcommand):
        """Run a git command and verify that the exit code is 0"""
        if isinstance(subcommand, basestring):
            subcommand = [subcommand]
        try:
            util.run(['git'] + subcommand, check=True)
            return True
        except:
            return False

    def run(self, subcommand):
        """Run a git command and return stdio. Throws if exit code is nonzero."""
        if isinstance(subcommand, basestring):
            subcommand = [subcommand]
        return util.run(['git'] + subcommand)

    # Canned helpers.

    def is_dirty(self):
        return (
            not self.check('diff-index --quiet --cached HEAD'.split())  # staged changes
         or not self.check('diff-files --quiet'.split())                # unstaged changes
        )

    def reset(self):
        return self.check('reset --hard'.split())

    # API

    def apply_style(self, style):
        # Write out the style file.
        with open(os.path.join(self.path, '.clang-format'), 'wb') as clang_format_style_file:
            style.dump(clang_format_style_file)

        # Restyle all the files.
        util.run([self.context['clang-format'], '-style=file', '-i'] + self.context['files_to_format'])

# A model of a project managed by a git repo.
class GitProject(object):
    def __init__(self, path, context):
        self.path = path
        self.context = context
        self.git_repo = GitRepo(path=path, context=context)

    # API

    def apply_style(self, style):
        if self.git_repo.is_dirty():
            raise ValueError("git repo is not clean")
        self.git_repo.apply_style(style)

    def apply_temporary_style(self, style):
        if self.git_repo.is_dirty():
            raise ValueError("git repo is not clean")

        return self.create_styled_repo_context(style)

    def get_files(self, extensions):
        return util.get_files_with_extensions(self.path, extensions)

    def check(self):
        if not os.path.exists(os.path.join(self.path, '.git')):
            raise ValueError("The directory %r does not seem to be a git repo (no .git subdir)" % self.path)
        if self.git_repo.is_dirty():
            raise ValueError("git repo is not clean; please make sure you have checked in your changes, or create a temporary copy to play in.")

    # Helpers

    def create_styled_repo_context(self, style):
        class StyledRepo(object):
            def __init__(self, git_repo, style):
                self.path = git_repo.path
                self.context = git_repo.context
                self.style = style

                self.git_repo = git_repo

            def __enter__(self):
                self.git_repo.apply_style(self.style)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.git_repo.reset()

        return StyledRepo(self.git_repo, style)
