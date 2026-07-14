// Registers/unregisters ComicVault as the Windows handler for the
// comicvault:// custom URI scheme, so the web UI's Issue Detail cover link
// (comicvault://read/{id}) actually launches this app. Adapted from the
// app_links package's own example (windows_protocol.dart) — that pattern
// isn't part of app_links' published public API, only its example app, so
// it's vendored here rather than imported.
//
// Uses HKEY_CURRENT_USER (not HKEY_CLASSES_ROOT) so no admin elevation is
// needed and the change only affects the current Windows user.
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';
import 'package:win32/win32.dart';

class ProtocolHandlerService {
  static const _scheme = 'comicvault';
  static const _hive = HKEY_CURRENT_USER;
  static String get _regPrefix => 'SOFTWARE\\Classes\\$_scheme';

  bool get isSupported => Platform.isWindows;

  // Registers the running exe's own path as the comicvault:// handler,
  // passing the clicked URI through as "%1" (rewritten to the launched
  // process's argv, which app_links' GetLink() already knows how to read).
  void register() {
    if (!isSupported) return;
    final cmd = '"${Platform.resolvedExecutable}" "%1"';
    _setStringValue(_regPrefix, '', 'URL:Comicvault');
    _setStringValue(_regPrefix, 'URL Protocol', '');
    _setStringValue('$_regPrefix\\shell\\open\\command', '', cmd);
  }

  void unregister() {
    if (!isSupported) return;
    final key = TEXT(_regPrefix);
    try {
      RegDeleteTree(_hive, key);
    } finally {
      free(key);
    }
  }

  // Reads back the registered command and confirms it points at this exe —
  // not just "a key exists" (stale entries from a moved/rebuilt exe should
  // read as unregistered, prompting Tez to re-register).
  bool isRegistered() {
    if (!isSupported) return false;
    final cmd = _readStringValue('$_regPrefix\\shell\\open\\command', '');
    if (cmd == null) return false;
    return cmd.contains(Platform.resolvedExecutable);
  }

  void _setStringValue(String key, String valueName, String data) {
    final txtKey = TEXT(key);
    final txtValueName = TEXT(valueName);
    final txtData = TEXT(data);
    try {
      RegSetKeyValue(
        _hive,
        txtKey,
        txtValueName,
        REG_SZ,
        txtData,
        txtData.length * 2 + 2,
      );
    } finally {
      free(txtKey);
      free(txtValueName);
      free(txtData);
    }
  }

  String? _readStringValue(String key, String valueName) {
    final hKeyPtr = calloc<HANDLE>();
    final txtKey = TEXT(key);
    final txtValueName = TEXT(valueName);
    try {
      final openResult = RegOpenKeyEx(_hive, txtKey, 0, KEY_READ, hKeyPtr);
      if (openResult != ERROR_SUCCESS) return null;

      final hKey = hKeyPtr.value;
      final dataSizePtr = calloc<DWORD>();
      try {
        var queryResult = RegQueryValueEx(
          hKey,
          txtValueName,
          nullptr,
          nullptr,
          nullptr,
          dataSizePtr,
        );
        if (queryResult != ERROR_SUCCESS) return null;

        final dataSize = dataSizePtr.value;
        final dataPtr = calloc<BYTE>(dataSize);
        try {
          queryResult = RegQueryValueEx(
            hKey,
            txtValueName,
            nullptr,
            nullptr,
            dataPtr,
            dataSizePtr,
          );
          if (queryResult != ERROR_SUCCESS) return null;
          return dataPtr.cast<Utf16>().toDartString();
        } finally {
          free(dataPtr);
        }
      } finally {
        free(dataSizePtr);
        RegCloseKey(hKey);
      }
    } finally {
      free(hKeyPtr);
      free(txtKey);
      free(txtValueName);
    }
  }
}
