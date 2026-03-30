#!/usr/bin/perl
# SPDX-FileCopyrightText: 2026 Blender Authors
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Patch brotli CMakeLists.txt to disable CLI tool install on iOS cross-compile

my $cmakeLists = $ARGV[0] or die "Usage: $0 <CMakeLists.txt>\n";
die "File not found: $cmakeLists\n" unless -f $cmakeLists;

local $/;
open my $fh, '<', $cmakeLists or die "Cannot open $cmakeLists: $!\n";
my $content = <$fh>;
close $fh;

# Comment out the install block for the brotli CLI executable
$content =~ s{
    install\(\s*\n\s*TARGETS\s+brotli\s*\n\s*RUNTIME\s+DESTINATION\s+\"[^\"]+\"\s*\n\s*\)
}{
    # PATCHED for iOS: disabled brotli CLI tool install
    # (original install block removed)
}gsmx;

open my $out, '>', $cmakeLists or die "Cannot write $cmakeLists: $!\n";
print $out $content;
close $out;

print "Patched: $cmakeLists\n";
exit 0;
