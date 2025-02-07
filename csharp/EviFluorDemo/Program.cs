
using Hse.EviFluor;
using System.Xml.Linq;

internal class Program
{
    Device device { get; set; }
    Factors? factors { get; set; }
    Measurement? measurementStdHigh { get; set; }
    Measurement? measurementStdLow { get; set; }

    StorageMeasurement storage { get; set; }

    public Program()
    {
        device = new Device();
        storage = new StorageMeasurement();
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

    void DisposeTip()
    {
        //Dispose the tip.
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

    void MeasureStandardHigh()
    {
        device.Baseline();

        if (device.IsCuvetteHolderEmpty() == true)
        {
            var volume = 10.5; //Cuvette volume in ul
            MoveCuvetteInCuvetteGuide();
            var air = device.FirstAirMeasurement();

            Dispense(volume);
            var sample = device.FirstSampleMeasurement();

            Aspirate(volume);
            MoveCuvetteOutOfCuvetteGuide();

            if (device.IsCuvetteHolderEmpty() == false)
            {
                throw new Exception("Cuvette is stuck in cuvette guide!");
            }

            measurementStdHigh = new Measurement(air, sample);

            Console.WriteLine($"measurementStdHigh:{measurementStdHigh}");

            storage.Append(measurementStdHigh, "stdhigh");
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
            var volume = 10.5; //Cuvette volume in ul
            MoveCuvetteInCuvetteGuide();
            var air = device.Measure();

            Dispense(volume);
            var sample = device.Measure();

            Aspirate(volume);
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

            factors = Measurement.CalculateFactors(
                0,   //Concentration of the standard low, usually 0.0
                10,  //Concentration of the standard high
                measurementStdLow, 
                measurementStdHigh);

            Console.WriteLine($"measurementStdLow:{measurementStdLow}");

            storage.Append(measurementStdHigh, "stdlow");
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

            Dispense(volume);
            var sample = device.Measure();

            Aspirate(volume);
            MoveCuvetteOutOfCuvetteGuide();

            if (device.IsCuvetteHolderEmpty() == false)
            {
                throw new Exception("Cuvette is stuck in cuvette guide!");
            }

            var measurement = new Measurement(air, sample);

            if (factors == null)
            {
                throw new Exception("Factors can't be null!");
            }

            var results = measurement.GetResults(factors);

            storage.AppendWithResults(measurement, results, comment);

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

                program.DisposeCuvette();
                program.DispenseToSample();
                program.DisposeTip();
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