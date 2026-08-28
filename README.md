<h1>CoinFT</h1>

#### Reproduced from [CoinFT](https://coin-ft.github.io)

Fabrication and calibration process for the CoinFTs, RVL edition. 

Please refer to their [official website](https://coin-ft.github.io) for the complete guide, this README is only intended for changes on the sensor for RVL's particular setup. 


## Catalog
- [Facility](#facility)
- [Components](#components)
- [Equipment](#equipment)
- [Fabrication](#fabrication)
- [Calibration](#calibration)
- [Sensors](#sensors)


## Facility
You'll need access to [CRAFT](https://craftmicrofluidics.ca/status-access/), it's one of the facilities at UofT that offers rental services for a degas chamber and a spin coater. You'll need to register a new account using RVL's payment method which you can get from Phebe. You'll also need to complete the general safety trainings. After that, you'll need to submit a request for an orientation at the <i>device foundry</i>. Finally, you'll need to book a training for the spin coater. In this case, the degas chamber isn't listed on their website as a separate device, so you'll be able to use it without any additional training. 

## Components
1. [PCB files](https://github.com/coin-ft/coin-ft/tree/main/hardware_files) can be found here
   - Feel free to order more stencils but we already have 2
2. [PCB ordering instruction](https://docs.google.com/document/d/e/2PACX-1vSQ-6q2MDwoBn2g9_u95RpvHrBDzH095R--uHuNxioFIZdZOnJKnvnTMS7yw188D1-z9awBrU9pWYNI/pub#h.1vtfffbt8bd3)
3. There're some additional components needed to interface with the sensor:
   
| Item | Description | Qty | Unit Cost | Link |
|------|-------------|-----|-----------|------|
| 22 AWG wires | Signal wires | 1 | $20.50 | [link](https://www.amazon.ca/Fermerry-Stranded-Electric-Tinned-Copper/dp/B089CQHRDT/ref=asc_df_B089CQHRDT?mcid=0b5d253d161535158c73822bb20fdd6c&tag=googleshopc0c-20&linkCode=df0&hvadid=706725384432&hvpos=&hvnetw=g&hvrand=9278312934987397925&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9000945&hvtargid=pla-943841637568&hvocijid=9278312934987397925-B089CQHRDT-&hvexpln=0&gad_source=1&th=1) |
| 1.25mm 4-pin JST connectors | Only use the female connectors | 1 | $11 | [link](https://www.amazon.ca/dp/B0F32G9B13?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1) |
| 1.25mm 4-pin JST headers | Solder them onto the PCBs | 20 | $19.6 | [link](https://www.digikey.ca/en/products/detail/molex/0532610471/699096) 

We have a PSoC board and a Teensy 4.0 board in the lab, so you don't need to order additional ones.

4. 1200 Primer is intended to clean the surfaces of the PCB before applying the mold, the point of it is to improve adhesion. We were unable to find any 1200 Primer, so instead we used [99% IPA](https://www.amazon.ca/DELON-Isopropyl-Alcohol-percent-Rubbing/dp/B0DD4FSVT3/ref=asc_df_B0DD4FSVT3?mcid=d88a00897388302f8347b708339dfac0&tag=googleshopc0c-20&linkCode=df0&hvadid=706827341420&hvpos=&hvnetw=g&hvrand=6317822538146002152&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9000945&hvtargid=pla-2398414279154&hvocijid=6317822538146002152-B0DD4FSVT3-&hvexpln=0&gad_source=1&th=1). It helps ensure that the surfaces are free of dust and can somewhat improve adhesion. In this case, you don't need to use a fume hood when cleaning the surface with IPA.
5. The original silicone rubber layer was made using two types of materials: TAP Silicone RTV Mold-Making System and Smooth-On Mold Max 40. However, we were unable to find TAP Silicone, so we only have Mold Max 40. This is fine, the instructions said that either material can be used.
6. The following picture shows some more components that we'll need, which we already have in the lab:
 <img width="1159" height="657" alt="Screenshot 2026-08-27 at 10 46 31 AM" src="https://github.com/user-attachments/assets/0a19fd94-e526-4e32-bc47-3606e4bf1483" />
7. We are replacing the acrylic parts with 3D printed parts including the holder for the PCBs, the guide rings for the weights and the calibration base. The CAD files can be found in the `CAD` folder.
   

## Equipment
1. A soldering iron
2. A 3D printer


## Fabrication 
The [official hardware instructions](https://docs.google.com/presentation/d/1NiOAXyq2A7fU8aHAD35k3iYaZIU_IhwRRHh8g923IFc/edit?slide=id.g348a17224d2_0_90#slide=id.g348a17224d2_0_90) 
- Top:
   1. Sand and clean the PCBs (with IPA 99%) at Myhal
   2. Carry the PCBs in a Petri dish to CRAFT (at Bahen). Mix and degas the chemical mixtures (Mold Max 40 part A & B), then apply the mold.
   3. Leave the PCBs to cure at Myhal for 24 hours
- Bottom:
   1. Sand and clean the PCBs
   2. Bring the cured top PCB and the sanded bottom PCB to CRAFT.
   3. Mix and degas the chemical mixtures (1400 RPM for 2 minutes), then spin coat the bottom PCB at 3100 RPM for 1 minute and 20 seconds (you will have to experiment with the exact time)
   4. Place the top PCB on top of the bottom PCB and leave it to cure for 24 hours (or longer)
- Soldering:
  1. Solder the yellow shielding to GND (G) not SHD, do not follow their tutorial.
- Sanding: 
  <i>Do not sand too much!</i> 
The following picture shows the amount of sanding you should aim for. You can sand a little more, but try to get a more even exposure.

<img width="553" height="393" alt="IMG_2676" src="https://github.com/user-attachments/assets/a89fc3f7-6272-44ba-a69e-d36b84b660ac" />



## Calibration
CoinFT doesn't directly return FT values, instead it measures capacitance which we need to map to the corresponding FT values. So, we'll use the Bota SensOne FT sensors as the reference/ground truth to calibrate the CoinFT.

Bota sensors show fewer oscillations at lower frequencies, and for a sensitive device like CoinFT, it is preferable to operate the Bota sensors at a frequency of around 400Hz or less.
 
When collecting data to train the model, start with slower presses to get a sense of the sensors’ sensitivities and to ensure that the CoinFTs and Bota are properly synced.

For reference, ~15 training sets (30s each) of stationary objects + slow presses should give you results like this, with mean-squared error per axis (Newtons): Fx: 0.000512, Fy: 0.000391, and Fz: 0.053102
<img width="1000" height="1000" alt="CFT24_MLP_test_force_results" src="https://github.com/user-attachments/assets/09d0462e-7b05-477c-87a9-ca7d1947b70b" />

The PSoC board (the red one) should be used to flash and calibrate the CoinFT sensor. Once the board has been calibrated, remove all the soldered wires from the sensor and reconnect the signal connections to the Teensy board. [Link to the Teensy code](https://github.com/coin-ft/coin-ft/tree/main/hardware_files/Teensy)


## Sensors
As of September 2026, there are three fabricated CoinFT sensors in the lab labeled A, B and C.

I have uploaded the firmware for sensor A, B and C (they are ready to use) and trained individual models for sensors A and B, located in the `trained_model` folder.

The sensors may need to be recalibrated given that the rubber ages and becomes less elastic. If recalibration is needed, follow the instructions in README.md inside the `src` folder to collect and re-train the models.
