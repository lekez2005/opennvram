#!/usr/bin/env python2.7
"""
Run a regresion test on a basic array
"""

from cam_test_base import CamTestBase, run_tests
import debug
from globals import OPTS


class PredecoderFlops(CamTestBase):


    def test_without_flop(self):

        from modules.hierarchical_predecode3x8 import hierarchical_predecode3x8 as pre3x8

        debug.info(2, "Testing 3x8 predecoder without flops")
        decoder = pre3x8(route_top_rail=True, use_flops=False)
        self.local_check(decoder)

    def test_with_flop(self):
        from modules.hierarchical_predecode3x8 import hierarchical_predecode3x8 as pre3x8

        debug.info(2, "Testing 3x8 predecoder without flops")
        decoder = pre3x8(route_top_rail=True, use_flops=True)
        self.local_check(decoder)

    def test_full_decoder_with_flops(self):
        from modules.hierarchical_decoder import hierarchical_decoder
        OPTS.decoder_flops = True
        decoder = hierarchical_decoder(32)
        self.local_check(decoder)


run_tests(__name__)