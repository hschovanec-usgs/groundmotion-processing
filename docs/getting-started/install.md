# Installation

See the [README](https://github.com/usgs/groundmotion-processing) at the top-level source directory.

## Dependencies

* Mac OSX or Linux operating systems; we hope to be able to support Windows sysmtems
  in the next release.

* bash shell, gcc, git, curl

## Installing via conda

The conda package is the easiest way to install the code, but is not generally as up to
date as installing from the source code.

```bash
conda install gmprocess
```

## Installing from source

The `install.sh` script in the base directory of the package installs this package and all
other dependencies, including python and the required python libraries. It is regularly
tested on OSX, CentOS, and Ubuntu.

Note: we are not yet able to test on Mac OS version 10.14 or newer because of institutional
restrictions. We have also had many bug reports from people who have tried to install our
code from source, typically related to the C compiler not being able to find header files.
The best we can do is point you to
[this](https://stackoverflow.com/questions/52509602/cant-compile-c-program-on-a-mac-after-upgrade-to-mojave)
discussion of the issue and hope that it help. Alernatively, you can install via conda.
