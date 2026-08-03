import 'package:flutter/material.dart';

// Shared across main.dart (registered on MaterialApp.navigatorObservers) and
// ShellScreen (subscribes via RouteAware.didPopNext) so returning to the
// shell after closing a reader can trigger a sync check — ShellScreen is
// only pushed once at app start, so its own initState() never re-fires on
// back-navigation (v2.5 Item 3).
final RouteObserver<ModalRoute<void>> routeObserver = RouteObserver<ModalRoute<void>>();
