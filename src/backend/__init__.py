import os
import sys

# Vendored ComicTagger subset (comicapi/comictalker/comictaggerlib) - see
# dev/docs/comictagger-vendoring-scope.md. Package names are kept identical
# to upstream on purpose, so ct_bridge.py's existing `import comicapi` etc.
# need no changes - only resolution order. Insert at the front of sys.path
# so this vendored copy always wins over a pip-installed "comictagger"
# distribution that may still be present during the incremental cutover
# (dropped in a later step of the port).
_VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if _VENDOR_DIR not in sys.path:
    sys.path.insert(0, _VENDOR_DIR)
