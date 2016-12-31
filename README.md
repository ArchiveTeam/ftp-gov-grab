ftp-gov-grab
=============

More information about the archiving project can be found on the ArchiveTeam wiki: [FTP GOV](http://archiveteam.org/index.php?title=FTP_GOV)

Setup instructions
=========================

Be sure to replace `YOURNICKHERE` with the nickname that you want to be shown as, on the tracker. You don't need to register it, just pick a nickname you like.

In most of the below cases, there will be a web interface running at http://localhost:8001/. If you don't know or care what this is, you can just ignore it—otherwise, it gives you a fancy view of what's going on.

**If anything goes wrong while running the commands below, please scroll down to the bottom of this page. There's troubleshooting information there.**

Running with a warrior
-------------------------

Follow the [instructions on the ArchiveTeam wiki](http://archiveteam.org/index.php?title=Warrior) for installing the Warrior, and select the "FTP GOV" project in the Warrior interface.

Running without a warrior
-------------------------
To run this outside the warrior, clone this repository, cd into its directory and run:

    pip install --upgrade seesaw
    pip2 install --upgrade warc

Grab a copy of Wpull 2.0.1 from https://launchpad.net/wpull/+download:

    wget https://launchpad.net/wpull/trunk/v2.0.1/+download/wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip
    python -c "import zipfile; f=zipfile.ZipFile('wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip'); f.extractall('./')"
    chmod +x ./wpull

then start downloading with:

    run-pipeline pipeline.py --concurrent 2 YOURNICKHERE

For more options, run:

    run-pipeline --help

If you don't have root access and/or your version of pip is very old, you can replace "pip install --upgrade seesaw" with:

    wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py ; python get-pip.py --user ; ~/.local/bin/pip install --user seesaw

so that pip and seesaw are installed in your home, then run

    ~/.local/bin/run-pipeline pipeline.py --concurrent 2 YOURNICKHERE

Running multiple instances on different IPs
-------------------------------------------

This feature requires seesaw version 0.0.16 or greater. Use `pip install --upgrade seesaw` to upgrade.

Use the `--context-value` argument to pass in `bind_address=123.4.5.6` (replace the IP address with your own).

Example of running 2 threads, no web interface, and Wget binding of IP address:

    run-pipeline pipeline.py --concurrent 2 YOURNICKHERE --disable-web-server --context-value bind_address=123.4.5.6

Distribution-specific setup
-------------------------
### For Debian/Ubuntu:

    adduser --system --group --shell /bin/bash archiveteam
    apt-get update && install -y git-core libgnutls-dev screen python-dev python-pip bzip2 zlib1g-dev unzip
    pip install --upgrade seesaw
    su -c "cd /home/archiveteam; git clone https://github.com/ArchiveTeam/ftp-gov-grab.git" archiveteam
    su -c "cd /home/archiveteam/ftp-gov-grab/; wget https://launchpad.net/wpull/trunk/v2.0.1/+download/wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip; unzip wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip; chmod +x ./wpull" archiveteam
    screen su -c "cd /home/archiveteam/ftp-gov-grab/; run-pipeline pipeline.py --concurrent 2 --address '127.0.0.1' YOURNICKHERE" archiveteam
    [... ctrl+A D to detach ...]


### For CentOS:

Ensure that you have the CentOS equivalent of bzip2 installed as well. You might need the EPEL repository to be enabled.

    yum -y install gnutls-devel python-pip zlib-devel unzip
    pip install --upgrade seesaw
    [... pretty much the same as above ...]

### For openSUSE:

    zypper install screen python-pip libgnutls-devel bzip2 python-devel gcc make unzip
    pip install --upgrade seesaw
    [... pretty much the same as above ...]

### For OS X:

You need Homebrew. Ensure that you have the OS X equivalent of bzip2 installed as well.

    brew install python gnutls unzip
    pip install --upgrade seesaw
    [... pretty much the same as above ...]

**There is a known issue with some packaged versions of rsync. If you get errors during the upload stage, ftp-gov-grab will not work with your rsync version.**

This supposedly fixes it:

    alias rsync=/usr/local/bin/rsync

### For Arch Linux:

Ensure that you have the Arch equivalent of bzip2 installed as well.

1. Make sure you have `python2-pip` installed.
2. Run `pip2 install seesaw`.
3. Modify the run-pipeline script in seesaw to point at `#!/usr/bin/python2` instead of `#!/usr/bin/python`.
4. `useradd --system --group users --shell /bin/bash --create-home archiveteam`
5. `su -c "cd /home/archiveteam; git clone https://github.com/ArchiveTeam/ftp-gov-grab.git" archiveteam`
6. `su -c "cd /home/archiveteam/ftp-gov-grab/; wget https://launchpad.net/wpull/trunk/v2.0.1/+download/wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip; unzip wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip; chmod +x ./wpull" archiveteam`
7. `screen su -c "cd /home/archiveteam/ftp-gov-grab/; run-pipeline pipeline.py --concurrent 2 --address '127.0.0.1' YOURNICKHERE" archiveteam`

### For FreeBSD:

Nothing specific here. If not so, please do let us know on IRC (irc.efnet.org #archiveteam).

Troubleshooting
=========================

Broken? These are some of the possible solutions:

### Wpull not successfully running

If you have trouble getting Wpull running, please see http://wpull.readthedocs.org/en/master/install.html.

### Problem with gnutls or openssl during building

Please ensure that gnutls-dev(el) and openssl-dev(el) are installed.

### ImportError: No module named seesaw

If you're sure that you followed the steps to install `seesaw`, permissions on your module directory may be set incorrectly. Try the following:

    chmod o+rX -R /usr/local/lib/python2.7/dist-packages

### run-pipeline: command not found

Install `seesaw` using `pip2` instead of `pip`.

    pip2 install seesaw

### Issues in the code

If you notice a bug and want to file a bug report, please use the GitHub issues tracker.

Are you a developer? Help write code for us! Look at our [developer documentation](http://archiveteam.org/index.php?title=Dev) for details.

### Other problems

Have an issue not listed here? Join us on IRC and ask! We can be found at irc.efnet.org #cheetoftp.
