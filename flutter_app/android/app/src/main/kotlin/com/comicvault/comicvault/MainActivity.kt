package com.comicvault.comicvault

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File
import java.io.FileOutputStream

// Handles local CBZ picking natively instead of via file_selector, which loads
// the entire picked document into a single Java byte array before returning
// it to Dart — comic archives commonly run 300+ MB and blow past Android's
// default 256 MB per-app heap ceiling (BUG-020). This streams the picked
// document straight to a cache file in fixed-size chunks, so memory use stays
// flat regardless of file size. Uses a broad "*/*" filter rather than a
// cbz-specific MIME type — Android's MIME mapping for .cbz has drifted across
// files depending on when each was indexed (some application/x-cbz, some
// application/vnd.comicbook+zip), and filtering on either one silently hides
// files with the other from being selectable (also BUG-020). The app's own
// ZipDecoder already validates the picked file's actual content afterward.
class MainActivity : FlutterActivity() {
    private val channelName = "comicvault/local_file_picker"
    private val pickCbzRequestCode = 4242
    private var pendingResult: MethodChannel.Result? = null

    // BUG-017: FlutterActivity's default behavior auto-forwards any
    // ACTION_VIEW intent's data as a raw route push (Navigator.pushNamed on
    // the URI's path) before app_links' own uriLinkStream/getInitialLink
    // ever sees it — since a literal file path like
    // "/storage/emulated/0/Download/foo.cbz" isn't a registered route, that
    // crashes with "Could not find a generator for route" and swallows the
    // intent entirely. Disabling it lets app_links (see main.dart
    // _handleLink) be the single path that receives incoming intents.
    override fun shouldHandleDeeplinking(): Boolean = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName).setMethodCallHandler { call, result ->
            if (call.method == "pickCbz") {
                pendingResult = result
                val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                    type = "*/*"
                    addCategory(Intent.CATEGORY_OPENABLE)
                }
                startActivityForResult(intent, pickCbzRequestCode)
            } else if (call.method == "resolveSharedUri") {
                // BUG-017: a .cbz opened from outside the app (file manager
                // "Open With") arrives as a content:// URI via the intent
                // filter in AndroidManifest.xml; this resolves it to a local
                // cache path the same way pickCbz does, reusing copyToCache.
                val uriString = call.arguments as? String
                if (uriString == null) {
                    result.error("RESOLVE_SHARED_URI_FAILED", "No URI provided", null)
                } else {
                    Thread {
                        try {
                            val path = copyToCache(Uri.parse(uriString))
                            runOnUiThread { result.success(path) }
                        } catch (e: Exception) {
                            runOnUiThread { result.error("RESOLVE_SHARED_URI_FAILED", e.message, null) }
                        }
                    }.start()
                }
            } else {
                result.notImplemented()
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode != pickCbzRequestCode) {
            super.onActivityResult(requestCode, resultCode, data)
            return
        }
        val result = pendingResult
        pendingResult = null
        val uri = data?.data
        if (resultCode != Activity.RESULT_OK || uri == null) {
            result?.success(null)
            return
        }
        Thread {
            try {
                val path = copyToCache(uri)
                runOnUiThread { result?.success(path) }
            } catch (e: Exception) {
                runOnUiThread { result?.error("PICK_CBZ_FAILED", e.message, null) }
            }
        }.start()
    }

    private fun copyToCache(uri: Uri): String {
        val name = queryDisplayName(uri) ?: "picked_${System.currentTimeMillis()}.cbz"
        val outFile = File(cacheDir, name)
        contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Unable to open input stream for $uri" }
            FileOutputStream(outFile).use { output ->
                val buffer = ByteArray(64 * 1024)
                var read: Int
                while (input.read(buffer).also { read = it } != -1) {
                    output.write(buffer, 0, read)
                }
            }
        }
        return outFile.absolutePath
    }

    private fun queryDisplayName(uri: Uri): String? {
        contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (idx >= 0 && cursor.moveToFirst()) {
                return cursor.getString(idx)
            }
        }
        return null
    }
}
