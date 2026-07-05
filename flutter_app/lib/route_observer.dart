import 'package:flutter/material.dart';

// Shared across main.dart (registered on MaterialApp.navigatorObservers) and
// LibraryScreen (subscribes via RouteAware.didPopNext) so returning to the
// library after closing a reader can trigger a sync check — LibraryScreen is
// only pushed once at app start, so its own initState() never re-fires on
// back-navigation (v2.5 Item 3).
final RouteObserver<ModalRoute<void>> routeObserver = RouteObserver<ModalRoute<void>>();
