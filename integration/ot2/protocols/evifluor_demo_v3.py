from opentrons import protocol_api
import os
import sys
from enum import Enum

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

metadata = {'apiLevel': '2.24', 
            'protocolName': 'eviFluor Demo V3',
            'author': 'DaZw'}
            
safety_height = 40
KIT_NAMES = [
    {"display_name" : "Default",  "value" : "Default"},
    {"display_name" : "qubit_hs", "value" :"QubitTM_1X_dsDNA_High_Sensitivity_HS"},
    {"display_name" : "qubit_br", "value" :"QubitTM_1X_dsDNA_Broad_Range_BR"},
]
    
class Speed(Enum):
    CUVETTE_PICKUP_DOWN  = 10.0
    CUVETTE_PICKUP_UP    = 10.0
    CUVETTE_MEASURE_DOWN = 30.0
    CUVETTE_MEASURE_UP   = 30.0

class Instrument:
    
    def __init__(self, protocol):
        self.protocol   = protocol
        

        self.workdeck   = { 'sample_plate'    : protocol.load_labware('corning_96_wellplate_360ul_flat',    '5'),
                            'evifluor'        : protocol.load_labware('hse_evifluor_pilot_left_20ul_tip_v1','4'),
                            'tiprack_20'      : protocol.load_labware('opentrons_96_filtertiprack_20ul',    '6'),
                          }
        
        self.workdeck   = dotdict(self.workdeck)
        
        self.cuvette_well_index     = 1        
        
        if not protocol.is_simulating():
            path = '/var/lib/jupyter/notebooks/runs/evifluor'
            os.makedirs(path, exist_ok=True)
            self.run = evifluor.Run(
                self.protocol.params.nr_of_std_low,
                self.protocol.params.nr_of_std_high,
                self.protocol.params.concentration_high,
                path = path,
                kit = evifluor.kits.Default.factory(self.protocol.params.kit),
                settling_time = self.protocol.params.settling_time,
            )

        self.pipette20_x1   = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[self.workdeck.tiprack_20])
        self.cuvette_source = self.workdeck.evifluor
        
    def error_handling(self):
        if self.protocol.params.pause_on_error:
            if self.run.verification.failed():
                self.protocol.pause("An error or a warning occurred!")

    def tip_pickup(self):
        self.pipette20_x1.pick_up_tip()

    def tip_drop(self):
        self.pipette20_x1.drop_tip()
    
    def sample_aspirate(self, volume, position, height=1):
        well = self.workdeck.sample_plate.wells()[position]
        self.pipette20_x1.aspirate(volume, well.bottom(height))

    def cuvette_pickup(self):
        well = self.cuvette_source.wells()[self.cuvette_well_index]
        self.cuvette_well_index = self.cuvette_well_index + 1
        self.pipette20_x1.move_to(well.top())
        self.pipette20_x1.move_to(location = well.bottom(), speed = Speed.CUVETTE_PICKUP_DOWN.value, publish = False)
        self.protocol.delay(seconds = 0.5)
        self.pipette20_x1.move_to(location = well.top(),                   speed = Speed.CUVETTE_PICKUP_UP.value, publish = False)
        self.pipette20_x1.move_to(location = well.top(z = safety_height), publish = False)

    def check_if_cuvette_holder_is_empty(self):
        if not self.protocol.is_simulating():
            if not self.run.check_empty():
                self.protocol.pause("Cuvette holder is not empty! Fix it and go ahead.")

    def move_over_cg(self):
        cuvette_guide  = self.workdeck.evifluor.well('A20')
        self.pipette20_x1.move_to(location = cuvette_guide.top(z = safety_height), publish = False)
        
    def move_into_cg(self): 
        cuvette_guide  = self.workdeck.evifluor.well('A20')
        self.pipette20_x1.move_to(location = cuvette_guide.top(z = safety_height), publish = False)
        self.pipette20_x1.move_to(location = cuvette_guide.top(), publish = False)
        self.check_if_cuvette_holder_is_empty()

        self.pipette20_x1.move_to(location = cuvette_guide.top(), publish = False)
        self.pipette20_x1.move_to(location = cuvette_guide.bottom(), speed = Speed.CUVETTE_MEASURE_DOWN.value, publish = False)
        
    def move_out_of_cg(self):
        cuvette_guide  = self.workdeck.evifluor.well('A20')
        self.pipette20_x1.move_to(location = cuvette_guide.top(), speed = Speed.CUVETTE_MEASURE_UP.value, publish = False)
        self.pipette20_x1.move_to(location = cuvette_guide.top(z = safety_height), publish = False)
                
    def comment(self, position):
        row = position % 8
        col = position // 8
        row_map = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        
        if position < self.protocol.params.nr_of_std_high:
            sample_type = "Standard high"
        elif position < self.protocol.params.nr_of_std_high + self.protocol.params.nr_of_std_low:
            sample_type = "Standard low"
        else:
            sample_type = "Sample"
    
        return "{}@{}{}".format(sample_type, row_map[row], col+1)
   
    def measure_with_1_channel(self, sample):
        VOLUME = 10.5 #ul
        EXTRA  = 0.5  #ul
        
        self.move_over_cg()        
        self.move_into_cg()
        if not self.protocol.is_simulating():
            self.run.measure(self.comment(sample))
            self.error_handling()
            
        self.pipette20_x1.dispense(VOLUME)
        if not self.protocol.is_simulating():
            self.run.measure(self.comment(sample))      
            self.error_handling()
            
        self.move_out_of_cg()
        self.pipette20_x1.aspirate(VOLUME + EXTRA)

    def aspirate_from_sample_plate_and_measure(self):
        VOLUME = 12
      
        for position in range(self.protocol.params.nr_of_std_high + self.protocol.params.nr_of_std_low + self.protocol.params.number_of_samples):
            self.tip_pickup()
            self.sample_aspirate(VOLUME, position)
            self.cuvette_pickup()
            self.measure_with_1_channel(position)
            self.tip_drop()


def run(protocol: protocol_api.ProtocolContext):

    if not protocol.is_simulating():
        sys.path.insert(0,'/var/lib/jupyter/notebooks')
        global evifluor
        from hse import evifluor
        
    assert protocol.params.nr_of_std_high + protocol.params.nr_of_std_low + protocol.params.number_of_samples <= 96, "The sum of <standard high> + <standard low> + <Number of samples> must be less or equal 96."
        
    i = Instrument(protocol)
  
    if not protocol.is_simulating():
        i.run.device.logging() # delete all log messages until now
        i.run.storage.add_dict("parameters", { 'number_of_samples'  : protocol.params.number_of_samples, 
                                               'nr_of_std_high'     : protocol.params.nr_of_std_high,
                                               'nr_of_std_low'      : protocol.params.nr_of_std_low,
                                               'concentration_high' : protocol.params.concentration_high,
                                               'kit'                : protocol.params.kit,
                                               'settling_time'      : protocol.params.settling_time,
                                               'protocol'           : metadata['protocolName']
                                             })
                                                         
    i.aspirate_from_sample_plate_and_measure()
    
    if not protocol.is_simulating():
        i.run.export_as_csv()

def add_parameters(parameters):

    parameters.add_int(
        variable_name="nr_of_std_high",
        display_name="Number of standard high",
        description="Number of samples which are standard high. They must be at position A1, A2, ..",
        default = 1,
        minimum = 1,
        maximum = 4
    )

    parameters.add_int(
        variable_name="nr_of_std_low",
        display_name="Number of standard low",
        description="Number of samples with buffer only. They must follow the standard high samples",
        default = 1,
        minimum = 1,
        maximum = 4
    )

    parameters.add_int(
        variable_name="number_of_samples",
        display_name="Number of samples",
        description="The sum of <standard high> + <standard low> + <Number of samples> must be less or equal 96.",
        default = 1,
        minimum = 1,
        maximum = 94
    )

    parameters.add_float(
        variable_name="concentration_high",
        display_name="Concentration Std High",
        description="Concentration Std High",
        default=10.0,
        minimum = 1,
        maximum = 4000
    )

    parameters.add_float(
        variable_name="settling_time",
        display_name="Settling time",
        description="Settling time override in seconds.",
        default=5.0,
        minimum = 0,
        maximum = 60
    )

    parameters.add_str(
        variable_name="kit",
        display_name="Kit",
        description="eviFluor kit used for result calculation and timing.",
        default="Default",
        choices=KIT_NAMES
    )
    
    parameters.add_bool(
        variable_name="pause_on_error",
        display_name="Pause on error",
        description="Pause on error",
        default=False
    )

    


