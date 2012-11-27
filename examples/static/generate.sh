#!/bin/bash
# -l option is for include runtime lib in output
# -b is the base dir of the templates
# -o is output file
jsjinja -l -b templates -o templates.js templates/*