import 'dart:io';
import 'dart:typed_data';
import 'package:archive/archive_io.dart';
import 'package:file_selector/file_selector.dart';
import 'package:path/path.dart' as p;

const _imageExts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'};

const _cbzTypeGroup = XTypeGroup(label: 'Comic files', extensions: ['cbz']);

class LocalCbzService {
  // Pick a CBZ from device storage. Returns null if cancelled.
  Future<String?> pickFile() async {
    final file = await openFile(acceptedTypeGroups: [_cbzTypeGroup]);
    return file?.path;
  }

  // Returns sorted list of image file names inside the CBZ
  List<String> listPages(String filePath) {
    final bytes = File(filePath).readAsBytesSync();
    final archive = ZipDecoder().decodeBytes(bytes);
    final names = archive.files
        .where((f) => f.isFile && _imageExts.contains(p.extension(f.name).toLowerCase()))
        .map((f) => f.name)
        .toList()
      ..sort();
    return names;
  }

  // Extract a single page image by index; returns raw bytes
  Uint8List readPage(String filePath, int index) {
    final bytes = File(filePath).readAsBytesSync();
    final archive = ZipDecoder().decodeBytes(bytes);
    final names = archive.files
        .where((f) => f.isFile && _imageExts.contains(p.extension(f.name).toLowerCase()))
        .map((f) => f.name)
        .toList()
      ..sort();
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

  String titleFromPath(String filePath) => p.basenameWithoutExtension(filePath);
}
