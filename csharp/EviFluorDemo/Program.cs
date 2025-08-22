
using Hse.EviFluor;
using Hse.EviFluor.Kits;
using System.Data;
using System.Xml.Linq;

internal class Program
{
    Device device { get; set; }
    Factors? factors { get; set; }

    Verification verification { get; set; }
    Measurement? measurementStdHigh { get; set; }
    Measurement? measurementStdLow { get; set; }

    StorageMeasurement storage { get; set; }

    private static readonly double CuvetteVolume = 10.0; //ul

    public Program()
    {
        device = new Device();
        storage = new StorageMeasurement();
        verification = new Verification();
        var sn = device.SerialNumber();
        Console.WriteLine($"Found eviFluor module SN{sn}");
    }

    void PickupTip()
    {
        //The liquid handler picks up a tip.

    }
    void AspirateFromSample()
    {
        //Aspirate at least 11ul sample.
    }

    void PickUpCuvette()
    {
        //Pick up with the tip a cuvette.
    }

    void MoveOverCuvetteGuide()
    {
        //Move the tip with the cuvette over the eviDense cuvette guide.
    }

    void DisposeCuvette()
    {
        //Dispose the cuvette when you want to use the sample further.
    }

    void DispenseToSample()
    {
        //Dispense the sample back.
    }

    void DisposeTipWithAttachedCuvette()
    {
        //Dispose the tip with attached cuvette.
    }

    void MoveCuvetteInCuvetteGuide()
    {
        //Move the tip/sample/cuvette combination over the cuvette guide.
    }

    void Dispense(double volume)
    {
        //Dispense the given volume into the cuvette
    }

    void Aspirate(double volume)
    {
        //Transfer the given sample volume from the cuvette back into the tip.
    }

    void MoveCuvetteOutOfCuvetteGuide()
    {
        //Move the cuvette out of the cuvette guide.
    }

    void ErrorHandling(Verification? verification)
    {
        if (verification == null)
            return;

        if(verification.Failed())
        {
            if(verification.HasProblem(Verification.ProblemId.CUVETTE_MISSING))
            {
                Console.WriteLine("Error: Cuvette missing!");
            }

            if (verification.HasProblem(Verification.ProblemId.SATURATION))
            {
                Console.WriteLine("Error: Signal saturated; invalid measurement!");
            }

            if (verification.HasProblem(Verification.ProblemId.AUTO_GAIN_RESULT))
            {
                Console.WriteLine("Error: The auto-gain failed; perhaps there was no standard high in the cuvette?");
            }

            if (verification.HasProblem(Verification.ProblemId.WRONG_LEVEL))
            {
                Console.WriteLine("Error: The auto-gain failed; perhaps there was no standard high in the cuvette?");
            }

            if (verification.HasProblem(Verification.ProblemId.NEGATIVE_CONCENTRATION))
            {
                Console.WriteLine("Error: The measurement is invalid — the concentration is negative!");
            }
        }
    }

    void MeasureStandardHigh()
    {
        device.Baseline();

        if (device.IsCuvetteHolderEmpty() == true)
        {
            MoveCuvetteInCuvetteGuide();
            var air = device.FirstAirMeasurement();
            verification.Check(air);
            ErrorHandling(verification);

            Dispense(CuvetteVolume);
            var sample = device.FirstSampleMeasurement();
            verification.Check(sample);
            ErrorHandling(verification);

            Aspirate(CuvetteVolume);
            MoveCuvetteOutOfCuvetteGuide();

            if (device.IsCuvetteHolderEmpty() == false)
            {
                throw new Exception("Cuvette is stuck in cuvette guide!");
            }

            measurementStdHigh = new Measurement(air, sample);
            verification.Check(measurementStdHigh);
            ErrorHandling(verification);

            Console.WriteLine($"measurementStdHigh:{measurementStdHigh}");

            var logging = device.Logging();

            storage.Append(measurementStdHigh, "stdhigh", logging, verification);
        }
        else
        {
            throw new Exception("Cuvette guide must be empty!");
        }
    }

    void MeasureStandardLow()
    {
        device.Baseline();

        if (device.IsCuvetteHolderEmpty() == true)
        {
            MoveCuvetteInCuvetteGuide();
            var air = device.Measure();
            verification.Check(air);
            ErrorHandling(verification);

            Dispense(CuvetteVolume);
            var sample = device.Measure();
            verification.Check(sample);
            ErrorHandling(verification);

            Aspirate(CuvetteVolume);
            MoveCuvetteOutOfCuvetteGuide();

            if (device.IsCuvetteHolderEmpty() == false)
            {
                throw new Exception("Cuvette is stuck in cuvette guide!");
            }

            if(measurementStdHigh == null)
            {
                throw new Exception("measurementStdHigh can't be null!");
            }

            measurementStdLow = new Measurement(air, sample);
            verification.Check(measurementStdLow);
            ErrorHandling(verification);

            factors = Measurement.CalculateFactors(
                0,   //Concentration of the standard low, usually 0.0
                10,  //Concentration of the standard high
                measurementStdLow, 
                measurementStdHigh);

            for (int i = 0; i < storage.Count; i++)
            {
                if (!storage[i].HasResults())
                {
                    storage[i].ApplyResults(factors);
                }
            }

            Console.WriteLine($"measurementStdLow:{measurementStdLow}");

            var logging = device.Logging();

            storage.Append(measurementStdHigh, "stdlow", logging, verification);
        }
        else
        {
            throw new Exception("Cuvette guide must be empty!");
        }
    }

    void MeasureSample(string comment)
    {
        device.Baseline();

        if (device.IsCuvetteHolderEmpty() == true)
        {
            var volume = 10.5; //Cuvette volume in ul
            MoveCuvetteInCuvetteGuide();
            var air = device.Measure();
            verification.Check(air);
            ErrorHandling(verification);

            Dispense(volume);
            var sample = device.Measure();
            verification.Check(sample);
            ErrorHandling(verification);

            Aspirate(volume);
            MoveCuvetteOutOfCuvetteGuide();

            if (device.IsCuvetteHolderEmpty() == false)
            {
                throw new Exception("Cuvette is stuck in cuvette guide!");
            }

            var measurement = new Measurement(air, sample);
            verification.Check(measurement);
            ErrorHandling(verification);

            if (factors == null)
            {
                throw new Exception("Factors can't be null!");
            }

            var results = measurement.GetResults(factors, new Quant_iT_dsDNA_HS()); //For Quant-iT dsDNA High Sensitivity Assay Kit
            verification.Check(results);
            ErrorHandling(verification);

            var logging = device.Logging();

            storage.AppendWithResults(measurement, results, comment, logging, verification);

            Console.WriteLine($"{measurement}:{measurement}");
            Console.WriteLine($"{comment} : {results}");
        }
        else
        {
            throw new Exception("Cuvette guide must be empty!");
        }
    }

    static int Main(string[] args)
    {
        try
        {
            Program program = new Program();

            int sampleCount = 3;

            for (int sample = 0; sample < sampleCount; sample++)
            {
                program.PickupTip();
                program.AspirateFromSample();
                program.PickUpCuvette();
                program.MoveOverCuvetteGuide();
                program.verification = new Verification();

                switch (sample)
                {
                    case 0:
                        program.MeasureStandardHigh();
                        break;

                    case 1:
                        program.MeasureStandardLow();
                        break;

                    default:
                        program.MeasureSample($"Sample #{sample}");
                        break;
                }

                program.DisposeTipWithAttachedCuvette();
            }

            program.storage.Save("data-evifluor.json");
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.ToString());
            return 1;
        }
        return 0;
    }
}