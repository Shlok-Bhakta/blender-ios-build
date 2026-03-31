#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set -euo pipefail

if [ "$#" -ne 6 ]; then
  printf 'usage: %s <src_dir> <prefix> <host_triplet> <ogg_include> <sysroot> <min_version>\n' "$0" >&2
  exit 1
fi

src_dir="$1"
prefix="$2"
host_triplet="$3"
ogg_include="$4"
sysroot="$5"
min_version="$6"

cd "$src_dir"

export flac_cv_prog_cc_cross=yes
export CC="clang -target $host_triplet -isysroot $sysroot -miphoneos-version-min=$min_version"
export CXX="clang++ -target $host_triplet -isysroot $sysroot -miphoneos-version-min=$min_version -stdlib=libc++"
export CPPFLAGS="-I$ogg_include"

./configure \
  --host="$host_triplet" \
  --prefix="$prefix" \
  --disable-shared \
  --enable-static
