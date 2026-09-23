# General overview

At a high level, an integration covers three layers:

1. Mechanical integration: Position the instrument, handle the cuvette, and teach the required positions.
2. Workflow integration: Coordinate liquid-handler movement with the eviFluor Duo Fluorometer measurement sequence.
3. Software and data integration: Trigger the software interface, collect results, and handle checks or warnings.

Most integration projects move through the same sequence:

1. Choose the software interface that best fits the host environment.
2. Set up and validate positioning and cuvette handling.
3. Implement and test the workflow with dry runs or simulation.
4. Validate the complete workflow on the target platform.

For more detailed integration guidance, see:

- [Available Interfaces](integration-interfaces.md)
- [Liquid Handler Requirements](integration-requirements.md)
- [Positioning and Teaching](integration-positioning.md)
- [Integration Paths](integration-paths.md)

