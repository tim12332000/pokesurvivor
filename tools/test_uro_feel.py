"""Compatibility entry for Uro's current moving-body / reaction / echo contract.

The old single-contact and refreshed-thin-ice behavior was replaced by real
fracture waves and independent counters. Its pre-change evidence remains under
.omx/state/duet-fracture/uro/before; do not regenerate it from the new runtime.
"""
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('URO_FRACTURE_OUT',os.environ.get('URO_FEEL_OUT',str(ROOT/'.omx/state/duet-fracture/uro/feel')))
from test_uro_fracture import main

if __name__=='__main__':main()
