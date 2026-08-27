1. Change var ID in the coinft_tune.py file to "train", "val" or "test" before data collection, it's preferable to have ~15 train sets, 3 val sets and a few test sets. 
2. Run sudo for every file


## Files
1. bota_sensor.py: verify hardware connection with the Bota sensor
2. coinft_MLP_train.py: train the model on the collected dataset
3. coinft_tune.py: data collection
4. CoinFT_V2_firmware.hex
5. data_processor.py: formats raw collected sensor data for training
6. ethercat_gen0.json: Bota sensor config