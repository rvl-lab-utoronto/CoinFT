## Notes
1. Run sudo for every file
2. The Bota sensor is collecting data at 400Hz.
3. Both sensors stop collecting at the same time, the collected dataset is then trimmed by `trim_duration` from the end of the episode, ensuring that the timestamps are synced. <i>The sensors are NOT hardware synced</i>. 
4. The total collection time is `trim_duration` + 5s
5. You will need to intentionally twist the top PCB around the Z-axis to collect sufficient data for training the Z-axis torque (ie Mz), otherwise the trained model may not be accurate. 


## Run
`sudo python3 coinft_tune.py --data_type train --bota_rate 400 --trim_duration 30`
- data_type: train, test or val 
- bota_rate: default 400Hz
- trim_duration: length of each episode, default 30s

Formats the collected data. Run this after all data has been collected:
`sudo python3 data_processor.py`

Train the model:
`sudo python3 coinft_MLP_train.py`

To run CoinFT live:
`sudo python3 live_eval.py --model_dir sensor_A --recording_time 30`
for models located in the `/trained_model/sensor_A` folder


## Models
1. `/trained_model/sensor_A` is trained on 18 datasets, 22 steps each, 30s per episode, with Bota's frequency set to 400 Hz.


## Files
1. bota_sensor.py: verify hardware connection with the Bota sensor
2. coinft_MLP_train.py: train the model on the collected dataset
3. coinft_tune.py: data collection
4. CoinFT_V2_firmware.hex
5. data_processor.py: formats raw collected sensor data for training
6. ethercat_gen0.json: Bota sensor config