#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

set -euo pipefail

if [ "$#" -ne 7 ]; then
  printf 'usage: %s <src_dir> <prefix> <host_triplet> <ogg_include> <ogg_lib> <sysroot> <min_version>\n' "$0" >&2
  exit 1
fi

src_dir="$1"
prefix="$2"
host_triplet="$3"
ogg_include="$4"
ogg_lib="$5"
sysroot="$6"
min_version="$7"

cd "$src_dir"

export CC="clang -target $host_triplet -isysroot $sysroot -miphoneos-version-min=$min_version"
export CXX="clang++ -target $host_triplet -isysroot $sysroot -miphoneos-version-min=$min_version -stdlib=libc++"
export CPPFLAGS="-I$ogg_include"
export LDFLAGS="-L$ogg_lib"

./configure \
  --host="$host_triplet" \
  --prefix="$prefix" \
  --with-ogg-includes="$ogg_include" \
  --with-ogg-libraries="$ogg_lib" \
  --disable-shared \
  --enable-static
