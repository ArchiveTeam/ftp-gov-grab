#!/bin/sh -e


if ! sudo pip freeze | grep -q requests
then
  echo "Installing requests"
  if ! sudo pip install requests
  then
    exit 1
  fi
fi


echo "Installing warc"
if ! sudo pip2 install warc
then
  exit 1
fi


echo "Getting the wpull binary"

VERSION='2.0.1'
TARBALL_32='wpull-2.0.1-linux-i686-3.4.3-20161230193418.zip'
CHECKSUM_32=85ca374bdb31196cf09f737c77069597
TARBALL_64='wpull-2.0.1-linux-x86_64-3.4.3-20161230193838.zip'
CHECKSUM_64=049b55d105866069f8911e74402513c5
INSTALL_DIR="${HOME}/.local/share/wpull-${VERSION}/"

if [ "`uname -m`" = "x86_64" ]; then
    TARBALL=${TARBALL_64}
    CHECKSUM=${CHECKSUM_64}
else
    TARBALL=${TARBALL_32}
    CHECKSUM=${CHECKSUM_32}
fi

DOWNLOAD_URL="https://launchpad.net/wpull/trunk/v${VERSION}/+download/${TARBALL}"

set +e
${INSTALL_DIR}/wpull --version > /dev/null 2>&1
RETVAL=$?
set -e

echo "Test for Wpull returned $RETVAL"

if [ $RETVAL -ne 0 ]; then
    echo "Downloading Wpull"

    TMP_DIR=/tmp/${CHECKSUM}/
    mkdir -p ${TMP_DIR}

    wget $DOWNLOAD_URL --continue --directory-prefix ${TMP_DIR}

    echo "Verify checksum"
    RESULT_CHECKSUM=`md5sum "${TMP_DIR}/${TARBALL}" | cut -f 1 -d " "`
    if [ "$RESULT_CHECKSUM" != "$CHECKSUM" ]; then
        echo "Checksum failed. Got ${RESULT_CHECKSUM}. Need ${CHECKSUM}"
        exit 1
    fi

    echo "Extracting contents to ${INSTALL_DIR}"
    mkdir -p "${INSTALL_DIR}"
    # tar -xzf "${TMP_DIR}/${TARBALL}" --strip-components 1 --directory "${INSTALL_DIR}"
    python -c "import zipfile; f=zipfile.ZipFile('${TMP_DIR}/${TARBALL}'); f.extractall('${INSTALL_DIR}')"
    chmod +x ${INSTALL_DIR}/wpull

    echo Done
fi