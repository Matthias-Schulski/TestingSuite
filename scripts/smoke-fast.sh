#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(dirname "$0")/.."
mkdir -p /tmp/refurbish
export REFURB_SMB_URL=local:/
export REFURB_MOUNTPOINT=/tmp/refurbish
export REFURB_FAST=1
python3 -m refurb.main || true

