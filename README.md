# fit-clang-format
Find the best-fit clang-format rules file for a git repo

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

You may also want to limit the files that the tool tests:
* if your repository is very large, maybe select some representative files (via `--include-path`)
* if your repository has sources you don't want to touch (eg, in-tree copies of external sources) or that could skew the results (test suites), then you can blacklist files (via `--exclude-path`)
* if your selections is still too large, you can have the tool randomly select files of each extension type (via `--randomly-limit`)

# License
This software is dual-licensed under MIT and LLVM licenses.
