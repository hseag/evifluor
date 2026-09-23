# Opentrons OT-2 Liquid Handler Integration

## 1. Introduction

This document describes a practical starting point for integrating the eviFluor Duo Fluorometer Python software with an Opentrons OT-2 liquid handler.

## 2. Installation

### 2.1 Software Setup

1. [SSH](https://support.opentrons.com/en/articles/3287453-connecting-to-your-ot-2-with-ssh) into the OT-2.
2. Install the Python package with:

```bash
python -m pip install https://hseag.github.io/evifluor/api/python/dist/hse_evifluor-0.12.0-py3-none-any.whl
```

If the OT-2 has no internet connection, download the Python wheel to your computer:

[`hse_evifluor-0.12.0-py3-none-any.whl`](https://hseag.github.io/evifluor/api/python/dist/hse_evifluor-0.12.0-py3-none-any.whl){ download="hse_evifluor-0.12.0-py3-none-any.whl" }

and copy it to your OT-2:

```bash
scp -i ot2_ssh_key hse_evifluor-0.12.0-py3-none-any.whl root@YOUR_IP:
```

Then install it locally on the OT-2 with:

```bash
python -m pip install hse_evifluor-0.12.0-py3-none-any.whl
```

After the installation, restart the OT-2.

### 2.2 Hardware Setup

1. Connect the eviFluor Duo Fluorometer to the OT-2 with the USB cable.
2. Prepare the deck, labware, reagents, and cuvettes as specified in the user guide for the selected protocol.
3. Wait until the device power-on self-test is complete and the instrument is ready.

### 2.3 Labware

Download and install the custom eviFluor Duo Fluorometer labware definition in the Opentrons App before loading a protocol:

- [`hse_evifluor_pilot_left_20ul_tip_v2.json`](https://hseag.github.io/evifluor/integration_kits/opentrons-ot2/labware/hse_evifluor_pilot_left_20ul_tip_v2.json){ download="hse_evifluor_pilot_left_20ul_tip_v2.json" }

### 2.4 Protocols and User Guides

Install the selected protocol in the Opentrons App. The protocol-specific user guide is the authoritative source for its deck layout, run parameters, reagent volumes, and operating procedure. Only the public protocols are listed below; internal protocols are not part of this user documentation.

- [`evifluor_ot2_device_demo.py`](https://hseag.github.io/evifluor/integration_kits/opentrons-ot2/protocol/evifluor_ot2_device_demo.py){ download="evifluor_ot2_device_demo.py" }: Demonstrates eviFluor device control, from sample aspiration and cuvette handling to measurement and liquid return. It is an integration demonstration, not a validated assay workflow. See the [Device Demo user guide](evifluor_ot2_device_demo_user_guide.md).
- [`evifluor_ot2_dna_normalization.py`](https://hseag.github.io/evifluor/integration_kits/opentrons-ot2/protocol/evifluor_ot2_dna_normalization.py){ download="evifluor_ot2_dna_normalization.py" }: Measures DNA samples, determines a target concentration, and prepares normalized samples. Source samples are diluted 1:10 before assay preparation. See the [DNA Normalization user guide](evifluor_ot2_dna_normalization_user_guide.md).
- [`evifluor_ot2_dna_sample_measurement_diluted_1_10.py`](https://hseag.github.io/evifluor/integration_kits/opentrons-ot2/protocol/evifluor_ot2_dna_sample_measurement_diluted_1_10.py){ download="evifluor_ot2_dna_sample_measurement_diluted_1_10.py" }: First dilutes DNA samples 1:10, then measures the diluted samples and applies the dilution factor to report the original sample concentration. See the [DNA Test Sample Measurement (1:10 Dilution) user guide](evifluor_ot2_dna_sample_measurement_diluted_1_10_user_guide.md).
- [`evifluor_ot2_dna_sample_measurement_undiluted.py`](https://hseag.github.io/evifluor/integration_kits/opentrons-ot2/protocol/evifluor_ot2_dna_sample_measurement_undiluted.py){ download="evifluor_ot2_dna_sample_measurement_undiluted.py" }: Measures DNA samples directly, without applying a dilution factor to the reported concentration. See the [DNA Test Sample Measurement (Undiluted) user guide](evifluor_ot2_dna_sample_measurement_undiluted_user_guide.md).

## 3. Starting The Protocol

Before running a protocol for the first time, perform the [Labware Position Check](https://docs.opentrons.com/ot-2/calibration/labware-offsets/) and simulate the selected protocol in the Opentrons App.

For a real run, follow the selected protocol's user guide. After the run, review the OT-2 run log and the eviFluor Duo Fluorometer-exported results.
