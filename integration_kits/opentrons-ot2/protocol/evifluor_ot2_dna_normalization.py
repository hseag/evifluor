from opentrons import protocol_api
from opentrons.types import Point
import os
import sys
import math
from enum import Enum

metadata = {
    "apiLevel": "2.27",
    "protocolName": "eviFluor normalization",
    "author": "HSE AG",
    "version": "0.1-draft",
}

# -----------------------------------------------------------------------------
# Method constants from the DHF workflow
# -----------------------------------------------------------------------------
N_SAMPLES_MIN = 1
N_SAMPLES_MAX = 24
N_SAMPLES_DEFAULT = 1
MTP_START_WELLS = tuple(
    "{}{}".format(row, column)
    for column in range(1, 13)
    for row in "ABCDEFGH"
)
MTP_START_WELL_TO_OFFSET = {
    well: offset for offset, well in enumerate(MTP_START_WELLS)
}
MTP_START_WELL_CHOICES = [
    {"display_name": well, "value": well} for well in MTP_START_WELLS
]
MTP_START_WELL_DEFAULT = "A1"

V_SAMPLE_AVAILABLE_MIN = 20.0  # uL
V_SAMPLE_AVAILABLE_MAX = 60.0  # uL
V_SAMPLE_AVAILABLE_DEFAULT = 40.0  # uL

C_TARGET_AUTO = 0.0  # ng/uL
C_TARGET_MAX = 20.0  # ng/uL
C_TARGET_DEFAULT = 10.0  # ng/uL

V_END_MIN = 10.0  # uL
V_END_MAX = 60.0  # uL
V_END_DEFAULT = 30.0  # uL

V_PIPETTING_MIN = 2.0  # uL
V_DEAD_SAMPLE = 5.0  # uL
V_DEAD_TUBE = 20.0  # uL
V_SAMPLE_DILUTION = 2.0  # uL
V_DILUENT_DILUTION = 18.0  # uL
V_DILUTED_ASSAY = 2.0  # uL
V_WS_ASSAY = 38.0  # uL
DILUTION_FACTOR = (V_DILUENT_DILUTION + V_SAMPLE_DILUTION) / V_SAMPLE_DILUTION
MIX_CYCLES_DILUTION = 6
MIX_CYCLES_ASSAY = 6
MIX_CYCLES_NORMALIZATION = 5
V_MIX = 19.0  # uL
MIX_OFFSET_Z_ASPIRATE = 1.0  # mm
MIX_OFFSET_X_TUBE = 1.0  # mm
MIX_OFFSET_Z_DISPENSE_TUBE = 4.0  # mm
MIX_OFFSET_X_MTP = 0.5  # mm
MIX_OFFSET_Z_DISPENSE_MTP_ASSAY = 3.0  # mm
MIX_OFFSET_Z_DISPENSE_MTP_DILUTION = 2.0  # mm
MIX_OFFSET_Z_DISPENSE_MTP_NORMALIZATION_MIN = 2.0  # mm
MIX_OFFSET_Z_DISPENSE_MTP_NORMALIZATION_LIQUID_LEVEL = -1.0  # mm
V_CUVETTE_MEASUREMENT_LOAD = 15.0  # uL
N_MEASUREMENTS_PER_STANDARD = 2
INCUBATION_TIME = 120  # s

# eviFluor integration values used by the supplied demo.
# Verify these values against the released eviFluor method before validation.
STANDARD_HIGH_CONCENTRATION = 10.0  # ng/uL
SETTLING_TIME = 5.0  # s
KIT = "QubitTM_1X_dsDNA_High_Sensitivity_HS"
SAFETY_HEIGHT = 40  # mm

# Current assay design discussed for the 1:10 dilution. Keep this explicit so it
# can be changed when the validated eviFluor range is finalized.
MEASUREMENT_MIN_NG_UL = 0.0  # ng/uL
MEASUREMENT_MAX_NG_UL = 12.0  # ng/uL

SAFELOCK_1_5ML_MIN_Z_OVER_BOTTOM = 1.0  # mm
SAFELOCK_1_5ML_DEFAULT_Z_OVER_LIQUID_LEVEL = -3.0  # mm
SAFELOCK_1_5ML_PROFILE = (
    (0.0, 0.0),
    (1.0, 6.0),
    (2.0, 15.0),
    (3.0, 26.0),
    (5.0, 56.0),
    (7.0, 97.0),
    (10.0, 179.0),
    (14.0, 325.0),
    (19.0, 567.0),
    (25.0, 940.0),
    (30.0, 1255.0),
    (35.0, 1571.0),
    (40.0, 1886.0),
)

# Inverted from VWR_211-0297_c_PCR96_skirted.xml. The XML's HeightZ runs
# downwards from the well top; this profile runs upwards from the well bottom.
PCR_96_WELL_MIN_Z_OVER_BOTTOM = 1.0  # mm
PCR_96_WELL_DEFAULT_Z_OVER_LIQUID_LEVEL = -1.0  # mm
PCR_96_WELL_PROFILE = (
    (0.0, 0.0),
    (1.2, 4.0),
    (2.8, 12.0),
    (4.3, 24.0),
    (5.9, 38.0),
    (7.5, 57.0),
    (9.0, 81.0),
    (10.6, 109.0),
    (11.7, 131.0),
    (12.8, 155.0),
    (13.9, 180.0),
    (15.0, 206.0),
)

# Deck positions according to the workdeck drawing in the DHF document.
SLOT_TUBE_RACK = "1"
SLOT_NORM = "3"
SLOT_SAMPLE = "2"
SLOT_MIX = "8"
SLOT_PARKING_TIPS = "9"
SLOT_FRESH_TIPS = "6"
SLOT_EVIFLUOR = "7"
SLOT_DILUTED = "5"


class Speed(Enum):
    CUVETTE_PICKUP_DOWN = 10.0
    CUVETTE_PICKUP_UP = 10.0
    CUVETTE_MEASURE_DOWN = 30.0
    CUVETTE_MEASURE_UP = 30.0


class VolumeProfiledContainer:
    def __init__(
        self,
        name,
        min_z_over_bottom=SAFELOCK_1_5ML_MIN_Z_OVER_BOTTOM,
        default_z_over_liquid_level=SAFELOCK_1_5ML_DEFAULT_Z_OVER_LIQUID_LEVEL,
        profile=SAFELOCK_1_5ML_PROFILE,
    ):
        self.name = name
        self.min_z_over_bottom = float(min_z_over_bottom)
        self.default_z_over_liquid_level = float(default_z_over_liquid_level)
        self.profile = tuple((float(height), float(volume)) for height, volume in profile)
        self.max_volume_ul = self.profile[-1][1]
        self.volume_ul = 0.0

    def set_volume(self, volume_ul):
        volume_ul = float(volume_ul)
        if volume_ul < 0:
            raise ValueError("{} volume must be >= 0 uL".format(self.name))
        if volume_ul > self.max_volume_ul:
            raise ValueError(
                "{} volume exceeds supported profile range ({:.1f} uL)".format(
                    self.name, self.max_volume_ul
                )
            )
        self.volume_ul = volume_ul

    def reduce_volume(self, volume_ul):
        volume_ul = float(volume_ul)
        if volume_ul < 0:
            raise ValueError("{} reduction must be >= 0 uL".format(self.name))
        if volume_ul > self.volume_ul:
            raise ValueError(
                "{} does not contain enough liquid for {:.1f} uL".format(
                    self.name, volume_ul
                )
            )
        self.volume_ul -= volume_ul

    def add_volume(self, volume_ul):
        self.set_volume(self.volume_ul + float(volume_ul))

    def liquid_level_height(self, volume_ul=None):
        if volume_ul is None:
            volume_ul = self.volume_ul
        if volume_ul <= self.profile[0][1]:
            return self.profile[0][0]

        for (height0, volume0), (height1, volume1) in zip(self.profile, self.profile[1:]):
            if volume_ul <= volume1:
                fraction = (volume_ul - volume0) / (volume1 - volume0)
                return height0 + fraction * (height1 - height0)

        return self.profile[-1][0]

    def z_over_bottom(self, z_over_liquid_level=None):
        if z_over_liquid_level is None:
            z_over_liquid_level = self.default_z_over_liquid_level

        target_height = self.liquid_level_height() + float(z_over_liquid_level)
        return max(self.min_z_over_bottom, target_height)


class SafeLock15MlTube(VolumeProfiledContainer):
    def __init__(
        self,
        name,
        min_z_over_bottom=SAFELOCK_1_5ML_MIN_Z_OVER_BOTTOM,
        default_z_over_liquid_level=SAFELOCK_1_5ML_DEFAULT_Z_OVER_LIQUID_LEVEL,
        profile=SAFELOCK_1_5ML_PROFILE,
    ):
        super().__init__(name, min_z_over_bottom, default_z_over_liquid_level, profile)


class Pcr96Well(VolumeProfiledContainer):
    def __init__(
        self,
        name,
        min_z_over_bottom=PCR_96_WELL_MIN_Z_OVER_BOTTOM,
        default_z_over_liquid_level=PCR_96_WELL_DEFAULT_Z_OVER_LIQUID_LEVEL,
        profile=PCR_96_WELL_PROFILE,
    ):
        super().__init__(name, min_z_over_bottom, default_z_over_liquid_level, profile)


def split_transfer(total_volume, max_volume=19.0):
    """Calculate N equal P20-friendly sub-transfers.

    Returns ``(n_transfers, transfer_volume)``. The minimum number of
    transfers is selected so that every transfer has the same volume and no
    transfer exceeds ``max_volume``. This avoids small residual transfers.

    Examples:
        18 uL -> (1, 18.0)
        20 uL -> (2, 10.0)
        38 uL -> (2, 19.0)
        40 uL -> (3, 13.333...)
    """
    total_volume = float(total_volume)
    max_volume = float(max_volume)

    if total_volume <= 0:
        return 0, 0.0
    if max_volume <= 0:
        raise ValueError("max_volume must be greater than 0")

    n_transfers = math.ceil(total_volume / max_volume)
    transfer_volume = total_volume / n_transfers
    return n_transfers, transfer_volume


class SparkleProtocol:
    def __init__(self, protocol):
        self.protocol = protocol
        self.n_samples = protocol.params.n_samples
        self.mtp_start_well = str(protocol.params.mtp_start_well)
        self.mtp_offset = MTP_START_WELL_TO_OFFSET[self.mtp_start_well]
        self.v_sample_available = float(protocol.params.v_sample_available)
        self.c_target = float(protocol.params.c_target)
        self.v_end = float(protocol.params.v_end)
        self.pause_on_error = bool(protocol.params.pause_on_error)

        self.diluted = protocol.load_labware(
            "opentrons_96_wellplate_200ul_pcr_full_skirt", SLOT_DILUTED
        )
        self.mix = protocol.load_labware(
            "opentrons_96_wellplate_200ul_pcr_full_skirt", SLOT_MIX
        )
        self.norm = protocol.load_labware(
            "opentrons_96_wellplate_200ul_pcr_full_skirt", SLOT_NORM
        )
        self.sample = protocol.load_labware(
            "opentrons_96_wellplate_200ul_pcr_full_skirt", SLOT_SAMPLE
        )
        self.tubes = protocol.load_labware(
            "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", SLOT_TUBE_RACK
        )
        self.fresh_tips = protocol.load_labware(
            "opentrons_96_filtertiprack_20ul", SLOT_FRESH_TIPS
        )
        # Parking rack starts EMPTY and is intentionally not registered as a tip rack.
        self.parking_tips = protocol.load_labware(
            "opentrons_96_filtertiprack_20ul", SLOT_PARKING_TIPS
        )
        self.evifluor = protocol.load_labware(
            "hse_evifluor_pilot_left_20ul_tip_v2", SLOT_EVIFLUOR
        )

        self.p20 = protocol.load_instrument(
            "p20_single_gen2", "left", tip_racks=[self.fresh_tips]
        )

        self.diluent_dilution = self.tubes["A1"]
        self.diluent_normalization = self.tubes["B1"]
        self.ws = self.tubes["C1"]
        self.standard_high = self.tubes["A2"]
        self.standard_low = self.tubes["B2"]
        self.standard_high_assay = self.tubes["A3"]
        self.standard_low_assay = self.tubes["B3"]

        self.diluent_dilution_tube = SafeLock15MlTube("Dilution diluent")
        self.diluent_normalization_tube = SafeLock15MlTube("Normalization diluent")
        self.ws_tube = SafeLock15MlTube("Working solution")
        self.standard_high_tube = SafeLock15MlTube("Standard high")
        self.standard_low_tube = SafeLock15MlTube("Standard low")
        self.standard_high_assay_tube = SafeLock15MlTube("Standard high assay")
        self.standard_low_assay_tube = SafeLock15MlTube("Standard low assay")

        self.diluent_dilution_tube.set_volume(V_DEAD_TUBE + (self.n_samples * V_DILUENT_DILUTION))
        self.diluent_normalization_tube.set_volume(
            V_DEAD_TUBE + (self.n_samples * max(0.0, self.v_end - V_PIPETTING_MIN))
        )
        self.ws_tube.set_volume(V_DEAD_TUBE + ((self.n_samples + 2) * V_WS_ASSAY))
        self.standard_high_tube.set_volume(V_DEAD_TUBE + V_DILUTED_ASSAY)
        self.standard_low_tube.set_volume(V_DEAD_TUBE + V_DILUTED_ASSAY)
        self.standard_high_assay_tube.set_volume(V_WS_ASSAY + V_DILUTED_ASSAY)
        self.standard_low_assay_tube.set_volume(V_WS_ASSAY + V_DILUTED_ASSAY)

        well_slice = slice(self.mtp_offset, self.mtp_offset + self.n_samples)
        self.sample_wells = self.sample.wells()[well_slice]
        self.diluted_wells = self.diluted.wells()[well_slice]
        self.mix_wells = self.mix.wells()[well_slice]
        self.norm_wells = self.norm.wells()[well_slice]
        self.sample_well_liquids = [
            Pcr96Well("SAMPLE {}".format(well.well_name)) for well in self.sample_wells
        ]
        for liquid in self.sample_well_liquids:
            liquid.set_volume(self.v_sample_available)
        self.diluted_well_liquids = [
            Pcr96Well("DILUTED {}".format(well.well_name)) for well in self.diluted_wells
        ]
        self.mix_well_liquids = [
            Pcr96Well("MIX {}".format(well.well_name)) for well in self.mix_wells
        ]
        self.norm_well_liquids = [
            Pcr96Well("NORM {}".format(well.well_name)) for well in self.norm_wells
        ]
        self.parking_positions = self.parking_tips.wells()[: self.n_samples]
        self.standard_parking_positions = self.parking_tips.wells()[
            self.n_samples : self.n_samples + 2
        ]

        self.cuvette_source = self.evifluor
        self.cuvette_well_index = 1  # retained from supplied eviFluor demo
        self.measurements = []

        if not protocol.is_simulating():
            sys.path.insert(0, "/var/lib/jupyter/notebooks")
            global evifluor
            from hse import evifluor

            path = "/var/lib/jupyter/notebooks/runs/evifluor"
            os.makedirs(path, exist_ok=True)
            self.evifluor_run = evifluor.Run(
                N_MEASUREMENTS_PER_STANDARD,
                N_MEASUREMENTS_PER_STANDARD,
                STANDARD_HIGH_CONCENTRATION,
                path=path,
                settling_time=SETTLING_TIME,
                kit=evifluor.kits.Default.factory(KIT)
            )
            self.evifluor_run.device.logging()
            self.evifluor_run.storage.add_dict(
                "parameters",
                {
                    "number_of_samples": self.n_samples,
                    "Vsample_available_ul": self.v_sample_available,
                    "Ctarget_ng_ul": self.c_target,
                    "Vend_ul": self.v_end,
                    "dilution_factor": DILUTION_FACTOR,
                    "protocol": metadata["protocolName"],
                },
            )

    # ------------------------------------------------------------------
    # Generic liquid handling
    # ------------------------------------------------------------------
    def report_tube_setup(self):
        self.protocol.comment(
            "Tube setup [uL]: A1 dilution diluent {:.1f}, B1 normalization diluent {:.1f} (max), C1 working solution {:.1f}, A2 standard high {:.1f}, B2 standard low {:.1f}; A3/B3 receive 40.0 uL standard assays".format(
                self.diluent_dilution_tube.volume_ul,
                self.diluent_normalization_tube.volume_ul,
                self.ws_tube.volume_ul,
                self.standard_high_tube.volume_ul,
                self.standard_low_tube.volume_ul,
            )
        )

    def aspirate_with_tracking(
        self,
        volume,
        source,
        source_height=1.0,
        source_container=None,
        source_z_over_liquid_level=None,
    ):
        if source_container is None:
            self.p20.aspirate(volume, source.bottom(source_height))
            return

        aspiration_height = source_container.z_over_bottom(source_z_over_liquid_level)
        self.p20.aspirate(volume, source.bottom(aspiration_height))
        source_container.reduce_volume(volume)

    def dispense_with_tracking(
        self,
        volume,
        dest,
        dest_height=1.0,
        dest_container=None,
    ):
        self.p20.dispense(volume, dest.bottom(dest_height))
        if dest_container is not None:
            dest_container.add_volume(volume)

    def transfer_with_current_tip(
        self,
        volume,
        source,
        dest,
        source_height=1.0,
        dest_height=1.0,
        source_container=None,
        dest_container=None,
        source_z_over_liquid_level=None,
    ):
        n_transfers, transfer_volume = split_transfer(volume)
        for _ in range(n_transfers):
            self.aspirate_with_tracking(
                transfer_volume,
                source,
                source_height=source_height,
                source_container=source_container,
                source_z_over_liquid_level=source_z_over_liquid_level,
            )
            self.dispense_with_tracking(
                transfer_volume,
                dest,
                dest_height=dest_height,
                dest_container=dest_container,
            )

    def mix_well(
        self,
        well,
        cycles=5,
        volume=V_MIX,
        offset_x=MIX_OFFSET_X_TUBE,
        offset_z_dispense=MIX_OFFSET_Z_DISPENSE_TUBE,
    ):
        """Mix from the bottom center to an offset dispense position."""
        volume = min(volume, V_MIX)
        aspirate_pos = well.bottom(MIX_OFFSET_Z_ASPIRATE)
        dispense_pos = well.bottom(offset_z_dispense).move(
            Point(x=offset_x, y=0, z=0)
        )
        self.p20.dynamic_mix(
            aspirate_start_location=aspirate_pos,
            dispense_start_location=dispense_pos,
            repetitions=cycles,
            volume=volume,
            aspirate_flow_rate=self.p20.flow_rate.aspirate * 4,
            dispense_flow_rate=self.p20.flow_rate.dispense * 8,
        )

    # ------------------------------------------------------------------
    # eviFluor functions adapted from evifluor_ot2_device_demo.py
    # ------------------------------------------------------------------
    def error_handling(self):
        if self.pause_on_error and not self.protocol.is_simulating():
            if self.evifluor_run.verification.failed():
                self.protocol.pause("An eviFluor error or warning occurred.")

    def cuvette_pickup(self):
        well = self.cuvette_source.wells()[self.cuvette_well_index]
        self.cuvette_well_index += 1
        self.p20.move_to(well.top())
        self.p20.move_to(
            location=well.bottom(),
            speed=Speed.CUVETTE_PICKUP_DOWN.value,
            publish=False,
        )
        self.protocol.delay(seconds=0.5)
        self.p20.move_to(
            location=well.top(), speed=Speed.CUVETTE_PICKUP_UP.value, publish=False
        )
        self.p20.move_to(location=well.top(z=SAFETY_HEIGHT), publish=False)

    def check_if_cuvette_holder_is_empty(self):
        if not self.protocol.is_simulating():
            if not self.evifluor_run.check_empty():
                self.protocol.pause("Cuvette holder is not empty. Fix it and resume.")

    def move_over_cg(self):
        guide = self.evifluor.well("A20")
        self.p20.move_to(location=guide.top(z=SAFETY_HEIGHT), publish=False)

    def move_into_cg(self):
        guide = self.evifluor.well("A20")
        self.p20.move_to(location=guide.top(z=SAFETY_HEIGHT), publish=False)
        self.p20.move_to(location=guide.top(), publish=False)
        self.check_if_cuvette_holder_is_empty()
        self.p20.move_to(location=guide.bottom(), speed=Speed.CUVETTE_MEASURE_DOWN.value, publish=False)

    def move_out_of_cg(self):
        guide = self.evifluor.well("A20")
        self.p20.move_to(location=guide.top(), speed=Speed.CUVETTE_MEASURE_UP.value, publish=False)
        self.p20.move_to(location=guide.top(z=SAFETY_HEIGHT), publish=False)

    def measure_loaded_cuvette(self, label):
        """
        Measure a cuvette using the sequence from the supplied demo.

        The caller must already have >= 11 uL liquid in the tip. The DHF workflow
        specifies 15 uL aspiration, leaving sufficient excess in the tip.

        Returns the value returned by the second evifluor.Run.measure() call.
        """
        VOLUME = 10.5
        EXTRA = 0.5

        self.move_over_cg()
        self.move_into_cg()
        if not self.protocol.is_simulating():
            self.evifluor_run.measure(label)
            self.error_handling()

        self.p20.dispense(VOLUME)
        result = None
        if not self.protocol.is_simulating():
            verification, result = self.evifluor_run.measure(label)
            self.error_handling()

        self.move_out_of_cg()
        self.p20.aspirate(VOLUME + EXTRA)
        return result

    # ------------------------------------------------------------------
    # DHF workflow
    # ------------------------------------------------------------------
    def prefill_diluted(self):
        self.protocol.comment("1. Pre-fill DILUTED plate")
        self.p20.pick_up_tip()
        for dest, dest_container in zip(self.diluted_wells, self.diluted_well_liquids):
            self.transfer_with_current_tip(
                V_DILUENT_DILUTION,
                self.diluent_dilution,
                dest,
                source_container=self.diluent_dilution_tube,
                dest_container=dest_container,
            )
        self.p20.drop_tip()

    def prefill_mix(self):
        self.protocol.comment("2. Pre-fill MIX plate and standard assay tubes")
        self.p20.pick_up_tip()
        for dest, dest_container in zip(self.mix_wells, self.mix_well_liquids):
            self.transfer_with_current_tip(
                V_WS_ASSAY,
                self.ws,
                dest,
                source_container=self.ws_tube,
                dest_container=dest_container,
            )
        for dest in (self.standard_high_assay, self.standard_low_assay):
            self.transfer_with_current_tip(
                V_WS_ASSAY,
                self.ws,
                dest,
                source_container=self.ws_tube,
            )
        self.p20.drop_tip()

    def prepare_sample_assays_and_park_tips(self):
        self.protocol.comment("3. Prepare sample dilutions and fluorescence assays")
        for (
            sample,
            sample_container,
            diluted,
            diluted_container,
            mix,
            mix_container,
            parking,
        ) in zip(
            self.sample_wells,
            self.sample_well_liquids,
            self.diluted_wells,
            self.diluted_well_liquids,
            self.mix_wells,
            self.mix_well_liquids,
            self.parking_positions,
        ):
            self.p20.pick_up_tip()
            self.aspirate_with_tracking(
                V_SAMPLE_DILUTION, sample, source_container=sample_container
            )
            self.dispense_with_tracking(
                V_SAMPLE_DILUTION, diluted, dest_container=diluted_container
            )
            self.mix_well(
                diluted,
                cycles=MIX_CYCLES_DILUTION,
                offset_x=MIX_OFFSET_X_MTP,
                offset_z_dispense=MIX_OFFSET_Z_DISPENSE_MTP_DILUTION,
            )
            self.aspirate_with_tracking(
                V_DILUTED_ASSAY, diluted, source_container=diluted_container
            )
            self.dispense_with_tracking(
                V_DILUTED_ASSAY, mix, dest_container=mix_container
            )
            self.mix_well(
                mix,
                cycles=MIX_CYCLES_ASSAY,
                offset_x=MIX_OFFSET_X_MTP,
                offset_z_dispense=MIX_OFFSET_Z_DISPENSE_MTP_ASSAY,
            )
            # Place used sample-specific tip into the empty parking rack.
            self.p20.drop_tip(parking)

    def prepare_standards_and_park_tips(self):
        self.protocol.comment("4. Prepare standard assays and park standard-specific tips")
        standard_setups = (
            (
                self.standard_high,
                self.standard_high_tube,
                self.standard_high_assay,
                self.standard_high_assay_tube,
            ),
            (
                self.standard_low,
                self.standard_low_tube,
                self.standard_low_assay,
                self.standard_low_assay_tube,
            ),
        )
        for (source, source_tube, dest, dest_tube), parking in zip(
            standard_setups, self.standard_parking_positions
        ):
            self.p20.pick_up_tip()
            self.aspirate_with_tracking(
                V_DILUTED_ASSAY, source, source_container=source_tube
            )
            self.p20.dispense(V_DILUTED_ASSAY, dest.bottom(1.0))
            self.mix_well(
                dest,
                cycles=MIX_CYCLES_ASSAY,
                offset_x=MIX_OFFSET_X_TUBE,
                offset_z_dispense=MIX_OFFSET_Z_DISPENSE_TUBE,
            )
            self.p20.drop_tip(parking)

    def incubate(self):
        self.protocol.comment("5. Incubate")
        self.protocol.delay(seconds=INCUBATION_TIME)

    def measure_standard(self, source, source_tube, label, parking=None):
        if parking is None:
            self.p20.pick_up_tip()
        else:
            self.p20.pick_up_tip(parking)
        self.aspirate_with_tracking(
            V_CUVETTE_MEASUREMENT_LOAD,
            source,
            source_container=source_tube,
        )
        self.cuvette_pickup()
        result = self.measure_loaded_cuvette(label)
        self.p20.drop_tip()
        return result

    def measure_standards(self):
        self.protocol.comment("6. Measure standards")
        standard_measurements = (
            (
                self.standard_high_assay,
                self.standard_high_assay_tube,
                self.standard_parking_positions[0],
                "Standard high",
            ),
            (
                self.standard_low_assay,
                self.standard_low_assay_tube,
                self.standard_parking_positions[1],
                "Standard low",
            ),
        )
        for source, source_tube, parking, label in standard_measurements:
            self.measure_standard(source, source_tube, label, parking=parking)
            self.measure_standard(source, source_tube, label)

    def measure_samples(self):
        self.protocol.comment("7. Measure samples")
        concentrations = []
        for index, (source_well, mix_well, mix_container, parking) in enumerate(
            zip(
                self.sample_wells,
                self.mix_wells,
                self.mix_well_liquids,
                self.parking_positions,
            ),
            start=1,
        ):
            # Pick up the exact sample-specific tip parked in step 4.
            self.p20.pick_up_tip(parking)
            self.aspirate_with_tracking(
                V_CUVETTE_MEASUREMENT_LOAD,
                mix_well,
                source_container=mix_container,
            )
            self.cuvette_pickup()
            result = self.measure_loaded_cuvette(
                "Normalized@{}".format(source_well.well_name)
            )
            self.p20.drop_tip()

            concentrations.append(result.concentration if result is not None else None)
            self.measurements.append(
                {
                    "sample_index": index,
                    "well": source_well.well_name,
                    "result": result,
                }
            )
        return concentrations

    def calculate_original_concentrations(self, measured):
        self.protocol.comment("8. Calculate original sample concentrations")
        return [None if c is None else c * DILUTION_FACTOR for c in measured]

    def maximum_common_target(self, original_concentrations):
        """Highest target satisfying upper-volume constraints for every sample."""
        limits = []
        usable_sample = self.v_sample_available - V_SAMPLE_DILUTION - V_DEAD_SAMPLE
        max_v_sample = min(self.v_end - V_PIPETTING_MIN, usable_sample)
        if max_v_sample < V_PIPETTING_MIN:
            return None
        for c in original_concentrations:
            if c is None or c <= 0:
                continue
            c_measured = c / DILUTION_FACTOR
            if not (MEASUREMENT_MIN_NG_UL <= c_measured <= MEASUREMENT_MAX_NG_UL):
                continue
            limits.append(c * max_v_sample / self.v_end)
        return min(limits) if limits else None

    def automatic_target_failure_reason(self, concentration):
        if concentration is None:
            return "eviFluor concentration unavailable"
        if concentration <= 0:
            return "non-positive concentration"

        measured_concentration = concentration / DILUTION_FACTOR
        if not (
            MEASUREMENT_MIN_NG_UL
            <= measured_concentration
            <= MEASUREMENT_MAX_NG_UL
        ):
            return "measurement outside validated range"
        return "no valid maximum common target concentration"

    def write_normalization_csv(self, c_target, plans):
        """Write normalization results to a CSV file.
        
        Derives the filename from self.evifluor_run._filename by replacing
        the .json extension with -normalization.csv.
        """
        if self.protocol.is_simulating():
            return
        
        import csv
        
        if not hasattr(self.evifluor_run, '_filename') or self.evifluor_run._filename is None:
            self.protocol.comment("WARNING: evifluor_run._filename not available, skipping normalization CSV export")
            return
        
        # Derive CSV filename from evifluor measurement filename
        base_filename = self.evifluor_run._filename
        if base_filename.endswith('.json'):
            csv_filename = base_filename[:-5] + '-normalization.csv'
        else:
            csv_filename = base_filename + '-normalization.csv'
        
        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = [
                    'sample_index',
                    'well',
                    'Csample_ng_ul',
                    'Ctarget_ng_ul',
                    'Vsample_ul',
                    'Vdiluent_ul',
                    'valid',
                    'status',
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                
                for plan in plans:
                    writer.writerow({
                        'sample_index': plan['index'] + 1,  # 1-based for CSV
                        'well': plan['well'],
                        'Csample_ng_ul': plan['Csample_ng_ul'],
                        'Ctarget_ng_ul': c_target,
                        'Vsample_ul': plan['Vsample_ul'],
                        'Vdiluent_ul': plan['Vdiluent_ul'],
                        'valid': plan['valid'],
                        'status': plan['status'],
                    })
            
            self.protocol.comment("Normalization results exported to: {}".format(csv_filename))
        except Exception as e:
            self.protocol.comment("ERROR: Failed to write normalization CSV: {}".format(str(e)))

    def calculate_normalization(self, original_concentrations):
        self.protocol.comment("9. Calculate and validate normalization volumes")
        c_target = self.c_target
        if c_target == C_TARGET_AUTO:
            c_target = self.maximum_common_target(original_concentrations)
            if c_target is None:
                plans = [
                    {
                        "index": index,
                        "well": self.sample_wells[index].well_name,
                        "Csample_ng_ul": concentration,
                        "Ctarget_ng_ul": None,
                        "Vsample_ul": None,
                        "Vdiluent_ul": None,
                        "valid": False,
                        "status": self.automatic_target_failure_reason(concentration),
                    }
                    for index, concentration in enumerate(original_concentrations)
                ]
                self.write_normalization_csv(None, plans)
                return None, plans
            self.protocol.comment("Calculated maximum common target: {:.4f} ng/uL".format(c_target))

        plans = []
        for idx, c_sample in enumerate(original_concentrations):
            valid = True
            reasons = []
            v_sample = None
            v_diluent = None

            if c_sample is None:
                valid = False
                reasons.append("eviFluor concentration unavailable")
            elif c_sample <= 0:
                valid = False
                reasons.append("non-positive concentration")
            else:
                v_sample = c_target * self.v_end / c_sample
                v_diluent = self.v_end - v_sample

                if v_sample < V_PIPETTING_MIN:
                    valid = False
                    reasons.append("Vsample < Vpipetting_min")
                if v_sample > self.v_end:
                    valid = False
                    reasons.append("Vsample > Vend")
                if v_sample + V_SAMPLE_DILUTION + V_DEAD_SAMPLE > self.v_sample_available:
                    valid = False
                    reasons.append("insufficient source sample volume")
                if v_diluent < V_PIPETTING_MIN:
                    valid = False
                    reasons.append("Vdiluent < Vpipetting_min")

                c_measured = c_sample / DILUTION_FACTOR
                if not (MEASUREMENT_MIN_NG_UL <= c_measured <= MEASUREMENT_MAX_NG_UL):
                    valid = False
                    reasons.append("measurement outside validated range")

            plans.append(
                {
                    "index": idx,
                    "well": self.sample_wells[idx].well_name,
                    "Csample_ng_ul": c_sample,
                    "Ctarget_ng_ul": c_target,
                    "Vsample_ul": v_sample,
                    "Vdiluent_ul": v_diluent,
                    "valid": valid,
                    "status": "OK" if valid else "; ".join(reasons),
                }
            )
        
        # Export results to CSV
        self.write_normalization_csv(c_target, plans)
        
        return c_target, plans

    def normalize(self, plans):
        valid_plans = [p for p in plans if p["valid"]]
        invalid_plans = [p for p in plans if not p["valid"]]

        for p in invalid_plans:
            self.protocol.comment("SKIP {}: {}".format(p["well"], p["status"]))

        self.protocol.comment("10. Transfer normalization diluent")
        if valid_plans:
            self.p20.pick_up_tip()
            for p in valid_plans:
                dest = self.norm_wells[p["index"]]
                dest_container = self.norm_well_liquids[p["index"]]
                self.transfer_with_current_tip(
                    p["Vdiluent_ul"],
                    self.diluent_normalization,
                    dest,
                    source_container=self.diluent_normalization_tube,
                    dest_container=dest_container,
                )
            self.p20.drop_tip()

        self.protocol.comment("11. Transfer original SAMPLE for normalization")
        for p in valid_plans:
            src = self.sample_wells[p["index"]]
            dest = self.norm_wells[p["index"]]
            src_container = self.sample_well_liquids[p["index"]]
            dest_container = self.norm_well_liquids[p["index"]]
            self.p20.pick_up_tip()
            self.transfer_with_current_tip(
                p["Vsample_ul"],
                src,
                dest,
                source_container=src_container,
                dest_container=dest_container,
            )
            normalization_offset_z_dispense = max(
                MIX_OFFSET_Z_DISPENSE_MTP_NORMALIZATION_MIN,
                dest_container.liquid_level_height(self.v_end - V_MIX)
                + MIX_OFFSET_Z_DISPENSE_MTP_NORMALIZATION_LIQUID_LEVEL,
            )
            self.mix_well(
                dest,
                cycles=MIX_CYCLES_NORMALIZATION,
                offset_x=MIX_OFFSET_X_MTP,
                offset_z_dispense=normalization_offset_z_dispense,
            )
            self.p20.drop_tip()

    def export_results(self, c_target, plans):
        """Use the existing eviFluor CSV export and add normalization data to storage."""
        if self.protocol.is_simulating():
            return

        self.evifluor_run.storage.add_dict(
            "normalization",
            {
                "Ctarget_ng_ul": c_target,
                "Vend_ul": self.v_end,
                "samples": plans,
            },
        )
        # The supplied demo already exposes this as the supported CSV export path.
        self.evifluor_run.export_as_csv()


def run(protocol: protocol_api.ProtocolContext):
    p = SparkleProtocol(protocol)

    # Basic setup checks derived from the DHF limits.
    assert N_SAMPLES_MIN <= p.n_samples <= N_SAMPLES_MAX
    assert p.mtp_start_well in MTP_START_WELL_TO_OFFSET
    assert p.mtp_offset + p.n_samples <= len(p.sample.wells())
    assert V_SAMPLE_AVAILABLE_MIN <= p.v_sample_available <= V_SAMPLE_AVAILABLE_MAX
    assert V_END_MIN <= p.v_end <= V_END_MAX
    assert C_TARGET_AUTO <= p.c_target <= C_TARGET_MAX

    p.report_tube_setup()

    p.prefill_diluted()
    p.prefill_mix()
    p.prepare_sample_assays_and_park_tips()
    p.prepare_standards_and_park_tips()
    p.incubate()
    p.measure_standards()
    measured = p.measure_samples()
    original = p.calculate_original_concentrations(measured)
    c_target, plans = p.calculate_normalization(original)

    if plans:
        p.normalize(plans)
        p.export_results(c_target, plans)


def add_parameters(parameters):
    parameters.add_int(
        variable_name="n_samples",
        display_name="Number of samples",
        description="Number of samples in the SAMPLE plate.",
        default=N_SAMPLES_DEFAULT,
        minimum=N_SAMPLES_MIN,
        maximum=N_SAMPLES_MAX,
    )

    parameters.add_str(
        variable_name="mtp_start_well",
        display_name="MTP start well",
        description="First PCR plate well. Samples follow the order A1, B1, ..., H12.",
        default=MTP_START_WELL_DEFAULT,
        choices=MTP_START_WELL_CHOICES,
    )

    parameters.add_float(
        variable_name="v_sample_available",
        display_name="Available sample volume",
        description="Amount of original sample available per SAMPLE well [uL].",
        default=V_SAMPLE_AVAILABLE_DEFAULT,
        minimum=V_SAMPLE_AVAILABLE_MIN,
        maximum=V_SAMPLE_AVAILABLE_MAX,
    )

    parameters.add_float(
        variable_name="c_target",
        display_name="Target concentration",
        description="Target concentration [ng/uL]. Enter 0 for maximum common concentration.",
        default=C_TARGET_DEFAULT,
        minimum=C_TARGET_AUTO,
        maximum=C_TARGET_MAX,
    )

    parameters.add_float(
        variable_name="v_end",
        display_name="Final normalized volume",
        description="Final volume of each normalized sample [uL].",
        default=V_END_DEFAULT,
        minimum=V_END_MIN,
        maximum=V_END_MAX,
    )

    # Retained from the supplied eviFluor demo because it controls runtime behavior,
    # although it is not part of the DHF user-parameter table.
    parameters.add_bool(
        variable_name="pause_on_error",
        display_name="Pause on eviFluor error",
        description="Pause the OT-2 run when eviFluor reports an error or warning.",
        default=False,
    )
