# fit-clang-format
Find the best-fit clang-format rules file for a git repo.

# Overview

Clang-format is an awesome tool that automatically reformats your source code according to a style file that you build (spaces anyone? or tabs?).

However, creating that style file is tedious and annoying. This Python tool iteratively tries all the options until it finds the style file that gives you the closest fit:
1. Pick tabs vs spaces (and how much one identation level is)
2. Pick the closest predefined top-level style (LLVM, Google, WebKit)
3. For each of the other style options, iteratively try every possible option and pick the one that fits "closest"

# Usage


    $ cd YourRepo
    $ fit-clang-format
       [ ... ]
    $ git diff   # Like it? Or reset and re-run?

You may need to specify the path to the clang-format tool if it is not in your path:

    $ fit-clang-format --clang-format-path /path/to/clang-format

The tool automatically grabs every source file (by extension) and performs reformatting and calculates the size of the delta.
It tries to find the combination that is the closest fit.

After the tool completes, your repo will have a `.clang-format` file in the root of your repository and the files will
have that format applied so you can run git-diff to see how it looks. 

## Trouble-Shooting and Fine-Tuning
   * Is it not finding the clang-format tool?
      * Use the '--clang-format-path' to manually specify a path to the tool.
   * Are there any files you *don't* want to format?
      * 3rd party files (eg, utility headers from OSS projects)
      * Unruly or large files you don't want to influence the final style
      * Use the '--exclude-path' option to skip those files.
   * Are there files that you know are mostly well-formated?
      * Use the '--include-path' option to limit the search to just those files.
   * Is the search just way too slow?
      * If your repo is large, it can take a while to reform it all a couple hundred times.
      * Consider using the '--randomly-limit' to pick a random sampling of files in your repo.
   * Do you already know a bit about the style you want?
      * Use the '--style-base' to force a base style.
      * Use the '--force-style' to force certain options.
      * Use the '--skip-option' to skip keys you know won't work well.
      * Visit 'http://clang.llvm.org/docs/ClangFormatStyleOptions.html' to learn more about what each option means.
   * Why are some options commented out?
      * Some options are commented out because the default value was the best. Review them and see if there's any to tweak.
   * What do I do next?
      * Make the clang-format tool a part of your regular workflow!

# How It Works

The scripts works by:
1. *Picking the best "base" style.* There are five pre-defined styles that are tuned to match the style preferences
of a few large OSS projects (Chromium, Google, LLVM, Mozilla, WebKit). The tool tries each one and picks the "best"
one.
2. *Tabs or Spaces?* The most basic question of style. The tool first figures out the usual indent and whether indentation is correct (space) or not (tabs). </trolling>
3. *Retry the base styles*. Now that indentation is decided, rerun the base check to double-check.
4. *Try all the others*. Then, for each of the ~60 options, it tries each one, in series. Note that the tool caches results, so it can skip one option of each set (the default in that base).


Figuring out which style is "better" is tricky, and there are a few different algorithms implemented that you can try.
Each algorithm reads the output of git-diff and calculates a score. These scores are a triplet of three values (in
different orders):
   * max(insertions, deletions): the size of the change (larger changes are worse)
   * files touched: the number of files that were modified (more files is worse)
   * net-insertion: if everything else is equal, prefer code that inserts the least code.
The algorithms are:
   * 'files': bias to change fewer *files* using 'git diff --shortstat'
   * 'lines': bias to change fewer *lines* of code using 'git diff --shortstat'
   * 'hybrid': bias to change fewer *lines* of code using ' using 'git diff --numstat'
   * 'hybrid-log': same as hybrid, but use logarithm to reduce impact of larger files
   * 'words': bias to change fewer *words* in the code using 'git diff --word-diff'
   * 'words-log': (default) same as words, but use logarithm to reduce impact of larger files

# License
This software is dual-licensed under MIT and LLVM licenses.
