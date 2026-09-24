# Firmware Updates and Versions

The instrument firmware controls the behavior of the eviFluor Duo Fluorometer device itself. In day-to-day work, firmware version information matters most before rollout, during support, and after an update.

## Current Repository Snapshot

This repository currently contains the firmware image file:

- [firmware/evifluor-0.8.0.srec](https://hseag.github.io/evifluor/pre-release/firmware/evifluor-0.8.0.srec){: download="evifluor-0.8.0.srec" }

## What to Check in Practice

Before and after an update, confirm:

- which firmware version is currently installed on the device
- which firmware image was approved for the workflow
- whether the device and host software belong to the same validated release set

## Where to Find More Detail

- Use [Updating Firmware with eviManager](software-firmware-update.md) for the guided product-level update flow.
- Use [Python Low-Level API](python-low-level.md), [C# Low-Level API](csharp-low-level.md), or [C CLI](c-cli.md) when you need technical access to version queries and update commands.
