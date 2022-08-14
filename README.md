# wakeup

Analysis code for a study asking if people can intentionally wake up from sleep using lucid dreaming.

Participants were asked to complete one of the following tasks while lucid:
```
- As soon as you become lucid, clench your fists in the dream.
- As soon as you become lucid, try to wake up from the dream in this specific way: Close your eyes and think to yourself that when you open them, you will wake up.
- As soon as you become lucid, try to wake up from the dream in this specific way: Vocalize to your dream that you want to wake up and think to yourself that when you say it, you will wake up.
- As soon as you become lucid, try to wake up from the dream in this specific way: Focus your gaze on a single point in the dream and think to yourself that you will wake up.
```

```shell
# Clean and aggregate raw Qualtrics output.
python source2raw.py                # => derivatives/data.tsv & .json

# Export a trimmed datafile with the main data of interest.
python trim_data.py                 # => derivatives/data_trimmed.tsv & .json

# Describe the sample.
python sample.py -f age             # => results/sample_age.tsv & .png
python sample.py -f gender          # => results/sample_gender.tsv & .png
python sample.py -f Condition       # => results/sample_condition.tsv & .png
python sample.py -f recruitment     # => results/sample_recruitment.tsv & .png

# Inspect survey responses.
python inspection.py                # => results/inspection.png

# Run chi-squared analyses.
python chisquared.py -t wakeup      # => results/chisquared_wakeup.tsv & .png
python chisquared.py -t impact      # => results/chisquared_impact.tsv & .png

# Visualize baseline LD frequency and wakeup success.
python plot-baselineXwakeup.py      # => results/baselineXwakeup.png

```