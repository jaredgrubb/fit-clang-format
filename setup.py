from setuptools import setup, find_packages
from os import path
# Py 2.7
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fit_clang_format',
    version='0.1.0',
    description='Find the best-fit clang-format rules file for a git repo',
    long_description_content_type='text/markdown',
    url='https://github.com/pypa/sampleproject',
    author='https://github.com/jaredgrubb/fit-clang-format',
    author_email='jaredgrubb+github@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'License :: OSI Approved :: University of Illinois/NCSA Open Source License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='c++ clang-format formatter',  # Optional
    packages=find_packages(),  # Required
    python_requires='>=2.5',
    install_requires=['pyyaml', 'six'],  # Optional
    # TODO: get a main function
    entry_points={  # Optional
        'scripts': [
            'fit_clang_format/fit-clang-format.py',
        ],
    },
)
