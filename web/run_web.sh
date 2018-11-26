#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

/usr/bin/supervisord -c /web/supervisor.conf