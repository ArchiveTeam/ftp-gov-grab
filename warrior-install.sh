#!/bin/sh -e


if ! sudo pip freeze | grep -q requests
then
  echo "Installing Requests"
  if ! sudo pip install requests
  then
    exit 1
  fi
fi


# V wpull V

VERSION='1.2'
TARBALL_32='wpull-1.2-linux-i686-3.4.3-20150508185459.zip'
CHECKSUM_32=9bb26c21e4904c92d530455646365d0f
TARBALL_64='wpull-1.2-linux-x86_64-3.4.3-20150508185423.zip'
CHECKSUM_64=114819ff3231fb7903f1c7c0a0ab416c
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
