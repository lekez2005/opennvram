#!/usr/bin/env python3
import json
import os
import sys
import argparse

from test_base import TestBase
from globals import OPTS

#-------------------------------------------------------------------------
# Command line processing
#-------------------------------------------------------------------------

class ArgumentParserWithCustomError(argparse.ArgumentParser):
  def error( self, msg = "" ):
    if ( msg ): print("\n ERROR: %s" % msg)
    print("")
    file = open( sys.argv[0] )
    for ( lineno, line ) in enumerate( file ):
      if ( line[0] != '#' ): sys.exit(msg != "")
      if ( (lineno == 2) or (lineno >= 4) ): print( line[1:].rstrip("\n") )

def parse_cmdline():
  p = ArgumentParserWithCustomError( add_help=False )

  # Standard command line arguments

  p.add_argument( "-h", "--help",    action="store_true" )

  # Additional commane line arguments for the simulator

  p.add_argument( "-g", "--view", default="verilog",
                  choices=["verilog", "db", "lef", "lib"] )

  p.add_argument( "-o", "--output", default = "."     ,
                                    action  = "store" )

  p.add_argument( "specs_filename" )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts

#-------------------------------------------------------------------------
# Subshell stuff
#-------------------------------------------------------------------------

def subshell( cmd ):

  # get shell's enviornment
  env = {}
  env.update(os.environ)

  process        = subprocess.Popen( cmd                     ,
                                     stdin  = subprocess.PIPE,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE,
                                     shell  = True           ,
                                     env    = env            )

  stdout, stderr = process.communicate()
  status         = process.returncode

  del process

  return stdout, stderr, status

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------

class BlSimulator(TestBase):
    baseline = False
    run_optimizations = True
    energy_sim = False

    def setUp(self):
        super(BlSimulator, self).setUp()

        self.corner = (OPTS.process_corners[0], OPTS.supply_voltages[0], OPTS.temperatures[0])

    def run_commands(self, use_pex, word_size, num_words):

        from modules.bitline_compute.bl_sram import BlSram
        from modules.bitline_compute.bs_sram import BsSram
        from modules.bitline_compute.baseline.baseline_sram import BaselineSram
        from energy_steps_generator import EnergyStepsGenerator
        from sim_steps_generator import SimStepsGenerator

        OPTS.use_pex = use_pex

        OPTS.word_size = word_size
        OPTS.num_words = num_words
        OPTS.words_per_row = 1

        OPTS.run_optimizations = self.run_optimizations

        if OPTS.serial:
            sram_class = BsSram
        elif OPTS.baseline:
            sram_class = BaselineSram
        else:
            sram_class = BlSram

        self.sram = sram_class(word_size=OPTS.word_size, num_words=OPTS.num_words, num_banks=1, name="sram1",
                               words_per_row=OPTS.words_per_row)
        self.sram.sp_write(OPTS.spice_file)

        #OPTS.pex_submodules = [self.sram.bank]

        # TODO you can define custom steps generators here following the pattern in EnergyStepsGenerator
        if OPTS.energy_sim:
            delay = EnergyStepsGenerator(self.sram, spfile=OPTS.spice_file, corner=self.corner, initialize=False)
        else:
            delay = SimStepsGenerator(self.sram, spfile=OPTS.spice_file, corner=self.corner, initialize=False)

        delay.trimsp = False

        OPTS.sense_amp_ref = 0.7
        OPTS.diff_setup_time = 0.2

        if OPTS.baseline:
            if OPTS.sense_amp_type == OPTS.MIRROR_SENSE_AMP:
                period = 1.1
                duty_cycle = 0.35
                OPTS.sense_trigger_delay = 0.2
            else:
                period = 1.8
                duty_cycle = 0.35
                OPTS.sense_trigger_delay = 0.6
        elif OPTS.serial:
            if OPTS.sense_amp_type == OPTS.MIRROR_SENSE_AMP:
                period = 1.1
                duty_cycle = 0.4
                OPTS.sense_trigger_delay = 0.2
            else:
                period = 2.2
                duty_cycle = 0.4
                OPTS.sense_trigger_delay = 0.7
        else:
            if OPTS.sense_amp_type == OPTS.MIRROR_SENSE_AMP:
                period = 1.5
                duty_cycle = 0.4
                OPTS.sense_trigger_delay = 0.25
            else:
                period = 2.2
                duty_cycle = 0.4
                OPTS.sense_trigger_delay = 0.7
        OPTS.verbose_save = False

        delay.period = period
        delay.duty_cycle = duty_cycle
        delay.read_period = period
        delay.write_period = period
        delay.read_duty_cycle = duty_cycle
        delay.write_duty_cycle = duty_cycle

        delay.slew = OPTS.slew_rate
        delay.setup_time = OPTS.setup_time

        delay.saved_nodes = []

        delay.prepare_netlist()

        delay.write_delay_stimulus()

        def dump_obj(x, f):
            for key in sorted(dir(x)):
                if type(getattr(x, key)).__name__ in ["str", "list", "int", "float"]:
                    f.write("{} = {}\n".format(key, getattr(x, key)))

        with open(os.path.join(OPTS.openram_temp, "config.py"), "w") as config_file:
            dump_obj(OPTS, config_file)
            config_file.write("\n\n")
            dump_obj(delay, config_file)

        delay.stim.run_sim()

    def test_schematic(self):
        use_pex = True
        OPTS.trim_netlist = False
        OPTS.run_drc = False
        OPTS.run_lvs = False
        OPTS.run_pex = False

        OPTS.top_level_pex = True

        OPTS.separate_vdd = False

        OPTS.energy_sim = BlSimulator.energy_sim

        self.run_commands(use_pex=use_pex, word_size=word_size, num_words=num_words)


if 'fixed_buffers' in sys.argv:
    BlSimulator.run_optimizations = False
    sys.argv.remove('fixed_buffers')
else:
    BlSimulator.run_optimizations = False  # for now just always use the hand-tuned values

word_size = 256
num_words = 128

if "serial" in sys.argv:
    folder_name = "serial"
elif "baseline" in sys.argv:
    folder_name = "baseline"
else:
    folder_name = "compute"

for arg in sys.argv:
    if "energy=" in arg:
        BlSimulator.energy_sim = arg[7:]

if "latched" in sys.argv:
    folder_name += "_latched"

openram_temp = os.path.join(os.environ["SCRATCH"])

temp_folder = os.path.join(openram_temp, "{}_{}_{}".format(folder_name, word_size, num_words))

BlSimulator.temp_folder = temp_folder

BlSimulator.run_tests(__name__)
