/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

namespace blender {

inline void BPY_platform_configure(PyConfig &config)
{
  /* iOS app bundles are immutable and no terminal owns the standard streams. */
  config.write_bytecode = 0;
  config.buffered_stdio = 0;
}

inline PyStatus BPY_platform_configure_executable(PyConfig &config)
{
  /* CPython's AppleFrameworkLoader resolves extension frameworks relative to
   * sys.executable. iOS has no standalone Python executable. */
  return PyConfig_SetBytesString(&config, &config.executable, BKE_appdir_program_path());
}

inline void BPY_platform_import_smoke()
{
  if (BLI_getenv("BLENDER_IOS_PYTHON_SMOKE") == nullptr) {
    return;
  }
  const int smoke_result = PyRun_SimpleString(
      "import bpy, bz2, ctypes, lzma, sqlite3, ssl\n"
      "import numpy as np\n"
      "import zstandard as zstd\n"
      "import tempfile\n"
      "from pathlib import Path\n"
      "from _bpy_internal.http import downloader as http_dl\n"
      "assert bpy.app.version[:2] == (5, 2)\n"
      "assert np.__version__ == '2.3.4'\n"
      "assert np.array([1, 2, 3]).sum() == 6\n"
      "assert np.linalg.det(np.eye(2)) == 1.0\n"
      "assert zstd.__version__ == '0.25.0'\n"
      "_zstd_payload = b'Blender iOS zstandard smoke'\n"
      "_zstd_compressed = zstd.ZstdCompressor().compress(_zstd_payload)\n"
      "assert zstd.ZstdDecompressor().decompress(_zstd_compressed) == _zstd_payload\n"
      "del _zstd_compressed, _zstd_payload\n"
      "assert http_dl._background_worker_kind == 'thread'\n"
      "_http_metadata = http_dl.MetadataProviderFilesystem(\n"
      "    Path(tempfile.gettempdir()) / 'blender-ios-http-smoke')\n"
      "_http_options = http_dl.DownloaderOptions(\n"
      "    _http_metadata, 1, {'User-Agent': 'Blender iOS smoke'})\n"
      "_http_worker = http_dl.BackgroundDownloader(_http_options, lambda *args: None)\n"
      "_http_worker.start()\n"
      "assert _http_worker.is_subprocess_alive\n"
      "_http_worker.shutdown()\n"
      "assert _http_worker.is_shutdown_complete\n"
      "del _http_worker, _http_options, _http_metadata\n");
  if (smoke_result == 0) {
    fprintf(stderr, "BLENDER_IOS_PYTHON_READY=5.2\n");
    fprintf(stderr, "BLENDER_IOS_NUMPY_READY=2.3.4\n");
    fprintf(stderr, "BLENDER_IOS_ZSTANDARD_READY=0.25.0\n");
    fprintf(stderr, "BLENDER_IOS_HTTP_READY=thread\n");
  }
  else {
    PyErr_Print();
    fprintf(stderr, "BLENDER_IOS_PYTHON_FAILED\n");
  }
}

}  // namespace blender
