# Compatibility

eviFluor Duo Fluorometer is designed for automation environments rather than stand-alone benchtop use. In practice, compatibility should be viewed on three levels: mechanics, workflow, and software.

## Currently Documented Compatibility

- A documented reference integration is available for the [Opentrons OT-2](integration-kits/opentrons-ot2/index.md).
- The software stack currently includes [Python](python.md), [C#](csharp.md), [C CLI](c-cli.md), and [Python REST](python-rest.md) integration paths.
- The workflow model assumes prepared standards and samples that are transferred into disposable cuvettes for measurement.

## What Another Liquid Handler Needs

Another platform can be a good fit when it can:

- pick up, move, insert, and discard the cuvette repeatably
- coordinate those motions with the eviFluor Duo Fluorometer measurement sequence
- run or call one of the supported software interfaces
- retain and process the generated measurement results

## What Compatibility Does Not Mean

Compatibility does not automatically mean that every liquid handler is already validated. A technical integration and assay validation step is still required for each target platform outside the OT-2 reference setup.

Use [Integration Overview](integration-overview.md) for the next step if you are evaluating a new platform.
