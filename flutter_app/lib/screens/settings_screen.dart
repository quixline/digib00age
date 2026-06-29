import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/settings_service.dart';

class SettingsScreen extends StatefulWidget {
  final SettingsService settings;
  final ApiService api;

  const SettingsScreen({
    super.key,
    required this.settings,
    required this.api,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;
  String _testResult = '';
  bool _testing = false;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.settings.serverUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    setState(() {
      _testing = true;
      _testResult = '';
    });
    final testApi = ApiService(url);
    final ok = await testApi.checkConnection();
    setState(() {
      _testing = false;
      _testResult = ok ? 'Connected successfully' : 'Could not connect — check URL and server';
    });
  }

  void _save() {
    final url = _urlController.text.trim();
    widget.settings.serverUrl = url;
    widget.api.baseUrl = url;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Settings saved')),
    );
    Navigator.of(context).pop(true); // signal that URL changed
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Server', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          TextField(
            controller: _urlController,
            decoration: const InputDecoration(
              labelText: 'ComicVault server URL',
              hintText: 'http://192.168.1.10:9424',
              border: OutlineInputBorder(),
            ),
            keyboardType: TextInputType.url,
            autocorrect: false,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: _testing ? null : _testConnection,
                icon: _testing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.wifi_find),
                label: const Text('Test connection'),
              ),
              const SizedBox(width: 12),
              if (_testResult.isNotEmpty)
                Expanded(
                  child: Text(
                    _testResult,
                    style: TextStyle(
                      color: _testResult.startsWith('Connected')
                          ? Colors.greenAccent
                          : Colors.redAccent,
                      fontSize: 13,
                    ),
                  ),
                ),
            ],
          ),
          const Divider(height: 32),
          Text('Reading', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          _ReadingModeTile(settings: widget.settings),
          const Divider(height: 32),
          Text(
            'ComicVault v1.0',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 24),
          FilledButton(onPressed: _save, child: const Text('Save')),
        ],
      ),
    );
  }
}

class _ReadingModeTile extends StatefulWidget {
  final SettingsService settings;
  const _ReadingModeTile({required this.settings});

  @override
  State<_ReadingModeTile> createState() => _ReadingModeTileState();
}

class _ReadingModeTileState extends State<_ReadingModeTile> {
  late String _mode;

  @override
  void initState() {
    super.initState();
    _mode = widget.settings.readingMode;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Default reading mode'),
        const SizedBox(height: 6),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(value: 'scroll', label: Text('Scroll'), icon: Icon(Icons.swap_vert)),
            ButtonSegment(value: 'page', label: Text('Page'), icon: Icon(Icons.chrome_reader_mode)),
          ],
          selected: {_mode},
          onSelectionChanged: (v) {
            setState(() => _mode = v.first);
            widget.settings.readingMode = v.first;
          },
        ),
      ],
    );
  }
}
