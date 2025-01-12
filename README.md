This project is a port of [OpenRAM](https://github.com/VLSIDA/OpenRAM) focusing on generation and simulation-based characterizations of post-CMOS, or non-volatile, or unconventional CMOS-based memories. While [OpenRAM](https://github.com/VLSIDA/OpenRAM) focuses on conventional CMOS 6T-based SRAMs (including multi-port support), this project is more research-focused, with an emphasis on post-layout simulation-based read/write/search timing characterizations.

# BASIC SETUP

Please look at the OpenRAM ICCAD paper in the upstream repository:
https://github.com/VLSIDA/OpenRAM/blob/stable/OpenRAM_ICCAD_2016_paper.pdf. A more complete OpenRAM documentation is available at https://github.com/VLSIDA/OpenRAM/blob/stable/docs/source/index.md. 

The OpenRAM compiler has very few dependencies:
* ngspice-26 (or later) or HSpice I-2013.12-1 (or later) or CustomSim 2017 (or later) or Spectre 15 (or later)
* Python 3.6 and higher
* Python numpy (and scipy if using optimized buffer stages)
* [libpsf](https://github.com/lekez2005/libpsf) if running simulations using spectre or hspice
* a setup script for each technology
* a technology directory for each technology with the base cells

If you want to perform DRC and LVS, you will need either:
* Calibre (for FreePDK45 or SCMOS)
* Magic + Netgen (for Skywater 130 and SCMOS)
* klayout (DRC) (for Skywater 130)

You must set three environment variables: 
* OPENRAM_HOME should point to the compiler source directory. 
* OPENERAM_TECH should point to a root technology directory that contains subdirs of all other technologies.
* SCRATCH should point to the directory where temporary files are saved e.g. `/tmp/<USER>`
For example, in bash, add to your .bashrc:
```
  export OPENRAM_HOME="$HOME/OpenRAM/compiler"
  export OPENRAM_TECH="$HOME/OpenRAM/technology"
  export SCRATCH=/tmp/<USER>
```
For example, in csh/tcsh, add to your .cshrc/.tcshrc:
```
  setenv OPENRAM_HOME "$HOME/OpenRAM/compiler"
  setenv OPENRAM_TECH "$HOME/OpenRAM/technology"
  setenv SCRATCH "/tmp/<USER>
```
### FreePDK45 Setup
If you are using FreePDK, you should also have that set up and have the
environment variable point to the PDK. 
For example, in bash, add to your .bashrc:
```
  export FREEPDK45="/bsoe/software/design-kits/FreePDK45"
```
For example, in csh/tcsh, add to your .tcshrc:
```
  setenv FREEPDK45 "/bsoe/software/design-kits/FreePDK45"
```
We do not distribute the PDK, but you may get it from:
    https://www.eda.ncsu.edu/wiki/FreePDK45:Contents

### SCMOS Setup
If you are using SCMOS, you should install Magic and netgen from:
	http://opencircuitdesign.com/magic/
	http://opencircuitdesign.com/netgen/
In addition, you will need to install the MOSIS SCMOS rules for scn3me_subm 
that are part of QFlow:
	http://opencircuitdesign.com/qflow/

### Sky130 Setup
If you intend to simulate ReRAM devices using the Sky130 process, you need to install
- Sky130 Hspice model. This model enables Spice simulations using either Spectre or Hspice simulators. These simulators can in turn simulate the Verilog-A-based ReRAM device model. To install: 
  - Download the tar.gz spice model [file](https://github.com/lekez2005/open_pdks/releases/download/1.0.306/hspice-model.tar.bz2)
  - Extract the tar.gz file to a directory
    - `mkdir hspice`
    - `tar -xf hspice-model.tar.bz2 -C hspice`
  - Copy the hspice directory to the Sky130 PDK directory
    - `cp -r hspice/ $PDK_ROOT_130/sky130B/libs.tech/hspice/`
- [libpsf](https://github.com/lekez2005/libpsf) to enable post-simulation functionality verification

# DIRECTORY STRUCTURE

* compiler - openram compiler itself (pointed to by OPENRAM_HOME)
  * compiler/characterizer - timing characterization code
  * compiler/gdsMill - GDSII reader/writer
  * compiler/router - detailed router
  * compiler/tests - unit tests
    - / - standard logic rule sram. Simulate using 21_simulation_test.py
    - /horizontal - unit tests for horizontal orientation modules
    - /push_rules - push rules sram. Simulate using top-level 21_simulation_test.py
    - /cam - 10T CAM implementation. Simulate using 21_cam_simulation_test.py
    - /mram - SOT-MRAM and SOTFET-MRAM implementations. Simulate using 21_mram_simulation_test.py
    - /reram - Sky130 ReRAM implementation. Includes Sky130 caravel wrapper implementation. Simulate using 21_reram_simulation_test.py
    - /bitline_compute - 6T SRAM and 1T1S SOTFET bitline compute implementations. Simulate using 21_bitline_simulation_test.py
    - /characterizer - Module characterization for estimating input/output capacitance and drive strengths for use in buffer stage optimization and analytical delay estimation
    
  
* technology - openram technology directory (pointed to by OPENRAM_TECH)
  * technology/freepdk45 - example configuration library for freepdk45 technology node
  * technology/scn3me_subm - example configuration library SCMOS technology node
  * technology/sky130 - example configuration library for sky130 technology node
  * technology/scripts - command line scripts for importing and exporting custom modules from magic/cadence/pdf


# UNIT TESTS

Regression testing  performs a number of tests for all modules in OpenRAM.

Use the command:
```
   python regress.py
```
To run a specific test:
```
   python {unit test}.py 
```
The unit tests take the same arguments as openram.py itself. 

To increase the verbosity of the test, add one (or more) -v options:
```
   python tests/00_code_format_check_test.py -v -t freepdk45
```
To specify a particular technology use "-t <techname>" such as
"-t scn3me_subm". The default for a unit test is freepdk45 whereas
the default for openram.py is specified in the configuration file.

A regression daemon script that can be used with cron is included in
a separate repository at https://github.com/mguthaus/openram-daemons
```
   regress_daemon.py
   regress_daemon.sh
```
This updates a git repository, checks out code, and sends an email
report with status information.

# CREATING CUSTOM TECHNOLOGIES

All setup scripts should be in the setup_scripts directory under the
$OPENRAM_TECH directory.  Please look at the following file for an
example of what is needed for OpenRAM:
```
  $OPENRAM_TECH/freepdk45/tech/setup_openram.py
```
Each setup script should be named as: setup_openram.py and placed within the corresponding technology's 'tech' directory.

Each specific technology (e.g., freepdk45) should be a subdirectory
(e.g., $OPENRAM_TECH/freepdk45) and include certain folders and files:
  1. gds_lib folder with all the .gds (premade) library cells. At a
     minimum this includes:
     * cell_6t.gds (the unit bitcell)
     * ms_flop.gds (width should be the same pitch as the bitcell)
     * ms_flop_clk_buf.gds (height should be at least as high as a 3 input-NAND gate)
     * sense_amp.gds (the sense amp module, same width as cell_6t.gds)
     * write_driver.gds (the write driver module, same width as cell_6t.gds)
     * tri_gate.gds
  2. sp_lib folder with all the .sp (premade) library netlists for the above cells.
  3. layers.map 
  4. A valid tech Python module (tech directory with __init__.py and tech.py) with:
     * References in tech.py to spice models
     * DRC/LVS rules needed for dynamic cells and routing
     * Layer information
     * etc.

# DEBUGGING

When OpenRAM runs, it puts files in a temporary directory that is
shown in the banner at the top. Like:
```
  /tmp/openram_mrg_18128_temp/
```
This is where simulations and DRC/LVS get run so there is no network
traffic. The directory name is unique for each person and run of
OpenRAM to not clobber any files and allow simultaneous runs. If it
passes, the files are deleted. If it fails, you will see these files:
* temp.gds is the layout
* (.mag files if using SCMOS)
* temp.sp is the netlist
* test1.drc.err is the std err output of the DRC command
* test1.drc.out is the standard output of the DRC command
* test1.drc.results is the DRC results file
* test1.lvs.err is the std err output of the LVS command
* test1.lvs.out is the standard output of the LVS command
* test1.lvs.results is the DRC results file

Depending on your DRC/LVS tools, there will also be:
* _calibreDRC.rul_ is the DRC rule file (Calibre)
* dc_runset is the command file (Calibre)
* extracted.sp (Calibre)
* run_lvs.sh is a Netgen script for LVS (Netgen)
* run_drc.sh is a Magic script for DRC (Magic)
* <topcell>.spice (Magic)

If DRC/LVS fails, the first thing is to check if it ran in the .out and
.err file. This shows the standard output and error output from
running DRC/LVS. If there is a setup problem it will be shown here.

If DRC/LVS runs, but doesn't pass, you then should look at the .results
file. If the DRC fails, it will typically show you the command that was used
to run Calibre or Magic+Netgen. 

To debug, you will need a layout viewer. I prefer to use Glade 
on my Mac, but you can also use Calibre, Magic, etc. 

1. Calibre

   Start the Calibre DESIGNrev viewer in the temp directory and load your GDS file:
```
  calibredrv temp.gds
```
   Select Verification->Start RVE and select the results database file in
   the new form (e.g., test1.drc.db). This will start the RVE (results
   viewer). Scroll through the check pane and find the DRC check with an
   error.  Select it and it will open some numbers to the right.  Double
   click on any of the errors in the result browser. These will be
   labelled as numbers "1 2 3 4" for example will be 4 DRC errors.

   In the viewer ">" opens the layout down a level.

2. Glade

   You can view errors in Glade as well. I like this because it is on my laptop.
   You can get it from:  http://www.peardrop.co.uk/glade/

   To remote display over X windows, you need to disable OpenGL acceleration or use vnc
   or something. You can disable by adding this to your .bashrc in bash:
```
  export GLADE_USE_OPENGL=no
```
   or in .cshrc/.tcshrc in csh/tcsh:
```
  setenv GLADE_USE_OPENGAL no
```
   To use this with the FreePDK45 or SCMOS layer views you should use the
   tech files. Then create a .glade.py file in your user directory with
   these commands to load the technology layers:
```
ui().importCds("default",
"/Users/mrg/techfiles/freepdk45/display.drf",
"/Users/mrg/techfiles/freepdk45/FreePDK45.tf", 1000, 1,
"/Users/mrg/techfiles/freepdk45/layers.map")
```
   Obviously, edit the paths to point to your directory. To switch
   between processes, you have to change the importCds command (or you
   can manually run the command each time you start glade).

   To load the errors, you simply do Verify->Import Calibre Errors select
   the .results file from Calibre.

3. Magic

   Magic is only supported in SCMOS and Sky130. You will need to install the MOSIS SCMOS rules
   and Magic from: http://opencircuitdesign.com/ for SCMOS

   When running DRC or extraction, OpenRAM will load the GDS file, save
   the .ext/.mag files, and export an extracted netlist (.spice).

4. It is possible to use other viewers as well, such as:
   * LayoutEditor http://www.layouteditor.net/ 


# Example to output/input .gds layout files from/to Cadence

1. To create your component layouts, you should stream them to
   individual gds files using our provided layermap and flatten
   cells. For example,
```
  strmout -layerMap layers.map -library sram -topCell $i -view layout -flattenVias -flattenPcells -strmFile ../gds_lib/$i.gds
```
2. To stream a layout back into Cadence, do this:
```
  strmin -layerMap layers.map -attachTechFileOfLib NCSU_TechLib_FreePDK45 -library sram_4_32 -strmFile sram_4_32.gds
```
   When you import a gds file, make sure to attach the correct tech lib
   or you will get incorrect layers in the resulting library.

