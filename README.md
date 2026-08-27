<h1>CoinFT</h1>

#### Reproduced from [CoinFT](https://coin-ft.github.io)

Fabrication and calibration process for the CoinFTs RVL edition. 


## Catalog
- [Facility](#facility)
- [Components](#components)
- [Fabrication](#fabrication)
- [Calibration](#calibration)
- [Files](#files)



## Facility
You'll need access to [CRAFT](https://craftmicrofluidics.ca/status-access/), it's one of the facilities at UofT that offers rental services for a degas chamber and a spin coater. You'll need to register a new account using RVL's payment method which you can get from Phebe. You'll also need to complete the general safety trainings. After that, you'll need to submit a request for an orientation at the device foundry. Finally, you'll need to book a training for the spin coater. In this case, the degas chamber isn't listed on their website as a separate device, so you'll be able to use it without any additional training. 

## Components
1. [PCB files](https://github.com/coin-ft/coin-ft/tree/main/hardware_files) can be found here
   - Feel free to order more stencils but we already have 
2. [PCB ordering instruction](https://docs.google.com/document/d/e/2PACX-1vSQ-6q2MDwoBn2g9_u95RpvHrBDzH095R--uHuNxioFIZdZOnJKnvnTMS7yw188D1-z9awBrU9pWYNI/pub#h.1vtfffbt8bd3)
3. There're some additional components needed to interface with the sensor:
   
| Item | Description | Qty | Unit Cost | Link |
|------|-------------|-----|-----------|------|
| 22 AWG wires | Signal wires | 1 | $20.50 | [link](https://www.amazon.ca/Fermerry-Stranded-Electric-Tinned-Copper/dp/B089CQHRDT/ref=asc_df_B089CQHRDT?mcid=0b5d253d161535158c73822bb20fdd6c&tag=googleshopc0c-20&linkCode=df0&hvadid=706725384432&hvpos=&hvnetw=g&hvrand=9278312934987397925&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9000945&hvtargid=pla-943841637568&hvocijid=9278312934987397925-B089CQHRDT-&hvexpln=0&gad_source=1&th=1) |
| 1. | 830-point solderless | 1 | $6.50 | [link](https://www.amazon.ca/dp/B0F32G9B13?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1) |
| Resistor 220Ω | 1/4W carbon film | 5 | $0.10 | [link](https://example.com) |
| LED | 5mm red | 5 | $0.15 | [link](https://example.com) | 

https://www.amazon.ca/dp/B0F32G9B13?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1

Some modifications had to be made for the components used for making the CoinFTs. 
1. 



## Fabrication 
Please refer to the [official hardware instructions](https://docs.google.com/presentation/d/1NiOAXyq2A7fU8aHAD35k3iYaZIU_IhwRRHh8g923IFc/edit?slide=id.g348a17224d2_0_90#slide=id.g348a17224d2_0_90) for the complete guide, this README is only intended for changes on the sensor for RVL's particular setup. 

