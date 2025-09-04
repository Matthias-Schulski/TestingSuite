#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."/live-build

sudo lb clean || true

sudo lb config \
  --distribution bookworm \
  --mirror-bootstrap http://deb.debian.org/debian \
  --mirror-binary http://deb.debian.org/debian \
  --debian-installer false \
  --architectures amd64 \
  --binary-images iso-hybrid \
  --bootappend-live "boot=live components quiet" \
  --linux-flavours amd64 \
  --memtest none \
  --firmware-chroot true

echo "Building live image (this may take a while)..."
sudo lb build

echo "Build complete. Artifacts in live-build/"
