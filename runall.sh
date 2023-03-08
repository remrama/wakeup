## Run all scripts in sequence to reproduce results.
##
## $ bash runall.sh

set -e

# Clean and aggregate raw Qualtrics output.
python source2raw.py                #=> derivatives/data.tsv

# Describe the sample.
python sample.py -f age             #=> results/sample_age.tsv/png
python sample.py -f gender          #=> results/sample_gender.tsv/png
python sample.py -f Condition       #=> results/sample_condition.tsv/png
python sample.py -f recruitment     #=> results/sample_recruitment.tsv/png

# Inspect survey responses.
python inspection.py                #=> results/inspection.png

# Run chi-squared analyses.
python chisquared.py -t wakeup      #=> results/chisquared_wakeup.tsv/png
python chisquared.py -t impact      #=> results/chisquared_impact.tsv/png

# Visualize baseline LD frequency and wakeup success.
python plot-baselineXwakeup.py      #=> results/baselineXwakeup.png
