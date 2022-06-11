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
# Clean and aggregate raw Qualtrics output
python source2raw.py                # ==> derivatives/data.py

# Export a trimmed datafile with the main data of interest.
python trim_data.py                 # ==> derivatives/data_trimmed.py
```