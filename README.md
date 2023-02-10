# wakeup

Analysis code for a study asking if people can intentionally wake up from sleep through lucid dreaming.

### General files

- `environment.yaml` can be used to construct the Python environment
- `config.json` has general parameter options that apply to multiple scripts
- `utils.py` has general functions that are useful to multiple scripts

### Data analysis

```shell
# Clean and aggregate raw Qualtrics output.
python source2raw.py                #=> derivatives/data.tsv

# Export a trimmed datafile with the main data of interest.
python trim_data.py                 #=> derivatives/data_trimmed.tsv

# Describe the sample.
python sample.py -f age             #=> results/sample_age.tsv (png)
python sample.py -f gender          #=> results/sample_gender.tsv (png)
python sample.py -f Condition       #=> results/sample_condition.tsv (png)
python sample.py -f recruitment     #=> results/sample_recruitment.tsv (png)

# Inspect survey responses.
python inspection.py                #=> results/inspection.png

# Run chi-squared analyses.
python chisquared.py -t wakeup      #=> results/chisquared_wakeup.tsv (png)
python chisquared.py -t impact      #=> results/chisquared_impact.tsv (png)

# Visualize baseline LD frequency and wakeup success.
python plot-baselineXwakeup.py      #=> results/baselineXwakeup.png
```
