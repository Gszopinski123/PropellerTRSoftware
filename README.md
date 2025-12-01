# PROPELLER TESTING RIG SOFTWARE

### Description

This software is used to interface with hardware that is connected to a Propeller Testing Rig. The point of this sofware is not only to interface, collect, log and provide analytics for the Propeller Testing but also to provide Quality of life with the implementation of a GUI. This Software was built on top of work already done by Brendan Cox. you can contact him at [here(Email)](brewcox@iu.edu).

### Goal

This project was my first chance to interact with researchers and do research as an undergraduate at Indiana University. I found this a easy way to learn how to interact with embedded systems while also sharpening my programming skills. I also wanted to help the researchers have a higher quality of life when working with software. I sought to dip my toes in research, interact with embedded systems, write software, and work on my programming skills through this research experience.

### Features

This Software provides a full GUI with multiple options to run code on the testing rig. It also provides a collection logger. This project also helps manage configuration files and data files for you allow you to accurately collect data and label it. The 3 versions are different attempts at better interacting with hardware and reducing code base where necessary.

### Build System
* Download the zip directory which can be done here.
* once downloaded there are 3 difference versions  
    * The First version v.0.0 is the most tested and is known to work
    * The Second version v.0.5 is the just an augmented version of v.0.0 it should work without errors
    * The Third version v.1.0 is the GUI version which has not been tested yet but is build around version v.0.0 and v.0.5

* To get started to use this software you should install the necessary libraries
 * ```pip3 install -r requirements.txt```
 * ```pip install -r requirements.txt```
 * The main difference is the version of pip you have
* once all libraries are down you should be able to run the software by running ```Driver.py``` or any of the files if you are using the non-GUI version

### Contributing

If you wish to contribute to this project, you can contact me at szopinski00@gmail.com, brewcox@iu.edu(Brendan Cox) or someone at the Aerospace Systems Laboratory at Indiana University at this [link](https://aerosyslab.com).


### Future Plans

No major plans at the moment(pending on work relevance). It would be a good idea to implement an analytics section as well as make progress bars or make incoming data more avaliable through the GUI.

