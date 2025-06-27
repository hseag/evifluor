# evifluor

The eviFluor module is  ultra-compact 2-channel fluorometer. 
For more information see https://www.hseag.com/evifluor-duo-factsheet. To control the eviFluor module HSE AG provides software interfaces in C or C#.

## Measuring procedure in short
1. Pick up a tip with your liquid handler
2. Aspirate at least 10.0 &#956;l of sample
3. Pick up a cuvette
4. Move the cuvette over the eviFluor module
5. Insert the cuvette into the eviFluor module
6. Measure the empty cuvette
7. Dispense approximately 10.0 &#956;l sample into the cuvette
8. Measure the cuvette with sample
9. Calculate the concentration of the sample
10. Move the cuvette out off the eviFluor module
11. Dispose the tip with attached cuvette
12. Repeat steps 1-12 until all samples are processed

The C# documentation can be found [here](csharp/doc/api/Hse.EviDense.html).
