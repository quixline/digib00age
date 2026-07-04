import 'dart:io';
import 'package:archive/archive_io.dart';
import 'package:flutter/services.dart';
import 'package:path/path.dart' as p;

const _imageExts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'};

const _localFilePickerChannel = MethodChannel('comicvault/local_file_picker');

class LocalCbzService {
  // Pick a CBZ from device storage. Returns null if cancelled.
  //
  // Uses a native MethodChannel (MainActivity.kt) instead of file_selector —
  // see BUG-020 (docs/BUGS.md / archive/bugs-fixed-archive.md) for why:
  // file_selector loads the whole picked file into memory before returning
  // it, which crashes on comic archives over ~250MB, and its MIME-type
  // filtering silently hides valid .cbz files whose OS-assigned MIME type
  // doesn't match. The native side streams to a cache file and accepts any
  // file type, leaving validation to this class's own archive read below.
  Future<String?> pickFile() async {
    return _localFilePickerChannel.invokeMethod<String>('pickCbz');
  }

  // listPages()/readPage() are both called once per page while a comic is
  // open (LocalReaderScreen._load()). Without caching, each call re-read and
  // re-decoded the entire archive from disk — for a 40-page, 346MB issue,
  // that's 40 full reads/decodes of the whole file, not 40 reads of one page
  // each. That was cheap to miss while file_selector's own OOM crash (see
  // above) killed the app before any of this ever ran; fixing that surfaced
  // this as a second bug — the repeated decoding built up enough memory/CPU
  // pressure that Android's low-memory killer terminated the app ~45s in,
  // instead of the same file_selector-level instant crash. One decode per
  // file, reused for every page, fixes both the redundant I/O and the
  // pressure it caused.
  String? _cachedPath;
  Archive? _cachedArchive;
  List<String>? _cachedNames;

  Archive _archiveFor(String filePath) {
    if (_cachedPath == filePath && _cachedArchive != null) return _cachedArchive!;
    final bytes = File(filePath).readAsBytesSync();
    _cachedArchive = ZipDecoder().decodeBytes(bytes);
    _cachedPath = filePath;
    _cachedNames = null;
    return _cachedArchive!;
  }

  List<String> _namesFor(String filePath) {
    final archive = _archiveFor(filePath);
    final cached = _cachedNames;
    if (cached != null) return cached;
    final names = archive.files
        .where((f) => f.isFile && _imageExts.contains(p.extension(f.name).toLowerCase()))
        .map((f) => f.name)
        .toList()
      ..sort();
    _cachedNames = names;
    return names;
  }

  // Returns sorted list of image file names inside the CBZ
  List<String> listPages(String filePath) => _namesFor(filePath);

  // Extract a single page image by index; returns raw bytes
  Uint8List readPage(String filePath, int index) {
    final archive = _archiveFor(filePath);
    final names = _namesFor(filePath);
    if (index < 0 || index >= names.length) {
      throw RangeError.index(index, names, 'page');
    }
    final file = archive.findFile(names[index])!;
    return file.content as Uint8List;
  }

  // Extract cover thumbnail bytes (first page)
  Uint8List? readCover(String filePath) {
    try {
      return readPage(filePath, 0);
    } catch (_) {
      return null;
    }
  }

  // Releases the cached archive (the decoded page directory, plus whichever
  // pages have been decompressed and cached so far) once a comic is closed.
  // LocalCbzService is a single long-lived instance for the app's whole
  // session, so without this the archive for a large CBZ would stay
  // resident in memory for as long as the app runs, not just while it's
  // open (part of BUG-020 — see archive/bugs-fixed-archive.md).
  void clear() {
    _cachedPath = null;
    _cachedArchive = null;
    _cachedNames = null;
  }

  String titleFromPath(String filePath) => p.basenameWithoutExtension(filePath);
}
