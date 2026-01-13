using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;

namespace Hse.EviFluor
{
    /// <summary>
    /// Provides verification checks for various measurement types and conditions.
    /// </summary>
    public class Verification
    {
        /// <summary>
        /// Default minimum expected RFU value.
        /// </summary>
        public static readonly double DefaultExpectedMinRfu = 4.5;
        /// <summary>
        /// Minimum expected RFU value used for verification.
        /// </summary>
        public static double ExpectedMinRfu = DefaultExpectedMinRfu;

        /// <summary>
        /// Default maximum expected RFU value.
        /// </summary>
        public static readonly double DefaultExpectedMaxRfu = 35.0;
        /// <summary>
        /// Maximum expected RFU value used for verification.
        /// </summary>
        public static double ExpectedMaxRfu = DefaultExpectedMaxRfu;

        /// <summary>
        /// Default minimum expected LED power.
        /// </summary>
        public static readonly int DefaultExpectedMinLedPower = 32;
        /// <summary>
        /// Minimum expected LED power used for verification.
        /// </summary>
        public static int ExpectedMinLedPower = DefaultExpectedMinLedPower;

        /// <summary>
        /// Default maximum expected LED power.
        /// </summary>
        public static readonly int DefaultExpectedMaxLedPower = 222;
        /// <summary>
        /// Maximum expected LED power used for verification.
        /// </summary>
        public static int ExpectedMaxLedPower = DefaultExpectedMaxLedPower;

        /// <summary>
        /// Default multiplier used for calculating RFU thresholds when determining cuvette presence.
        /// </summary>
        public static readonly double DefaultRfuThresholdMultiplier = 2.0;
        /// <summary>
        /// Multiplier used for calculating RFU thresholds when determining cuvette presence.
        /// </summary>
        public static double RfuThresholdMultiplier = DefaultRfuThresholdMultiplier;

        /// <summary>
        /// Default maximum allowed signal before considering saturation.
        /// </summary>
        public static readonly double DefaultMaxSignal = 2499.0;
        /// <summary>
        /// Maximum allowed signal before considering saturation.
        /// </summary>
        public static double MaxSignal = DefaultMaxSignal;

        /// <summary>
        /// Default target signal value for standard high checks.
        /// </summary>
        public static readonly double DefaultStdHighTarget = 2000.0;
        /// <summary>
        /// Target signal value for standard high checks.
        /// </summary>
        public static double StdHighTarget = DefaultStdHighTarget;

        /// <summary>
        /// Default allowed deviation from the standard high target.
        /// </summary>
        public static readonly double DefaultStdHighDelta = 300;
        /// <summary>
        /// Allowed deviation from the standard high target.
        /// </summary>
        public static double StdHighDelta = DefaultStdHighDelta;

        /// <summary>
        /// Default threshold for detecting negative concentrations.
        /// </summary>
        public static readonly double DefaultThresholdNegativeConcentration = -0.1;
        /// <summary>
        /// Threshold for detecting negative concentrations.
        /// </summary>
        public static double ThresholdNegativeConcentration = DefaultThresholdNegativeConcentration;

        /// <summary>
        /// Enum representing various types of problems that may occur during verification.
        /// </summary>
        public enum ProblemId
        {
            /// <summary>
            /// Indicates that the sensor signal saturated.
            /// </summary>
            SATURATION = 1,

            /// <summary>
            /// A cuvette was expected.
            /// </summary>
            CUVETTE_MISSING = 2,

            /// <summary>
            /// Auto gain function failed.
            /// </summary>
            AUTO_GAIN_RESULT = 5,

            /// <summary>
            /// The signal level is not in the expected range (1700 - 2300 mV)
            /// </summary>
            WRONG_LEVEL = 6,

            /// <summary>
            /// The concentration is less than ThresholdNegativeConcentration
            /// </summary>
            NEGATIVE_CONCENTRATION = 7
        }

        /// <summary>
        /// Flags that provide context-sensitive hints for verification checks.
        /// </summary>
        [Flags]
        public enum Hints
        {
            /// <summary>
            /// No hint.
            /// </summary>
            NONE = 0,

            /// <summary>
            /// A cuvette is expected.
            /// </summary>
            MUST_HAVE_CUVETTE = 1,

            /// <summary>
            /// Signal for standard high (~2000 +- 200 mV) expected.
            /// </summary>
            STD_HIGH = 2
        }

        /// <summary>
        /// Represents a single verification result entry within the <see cref="Verification"/> process.
        /// </summary>
        /// <remarks>
        /// Each entry consists of a <see cref="Verification.ProblemId"/> indicating the type of problem detected,
        /// and an associated data object (e.g., a measurement or result) that caused the issue.
        /// </remarks>
        public class Entry : IJsonSerializable
        {
            /// <summary>
            /// Gets the problem type that this entry represents.
            /// </summary>
            public ProblemId Problem { get; }

            /// <summary>
            /// Gets the data object associated with the problem (e.g., a measurement or result).
            /// </summary>
            public object Data { get; }

            /// <summary>
            /// Initializes a new instance of the <see cref="Entry"/> class.
            /// </summary>
            /// <param name="problem">The specific problem identifier.</param>
            /// <param name="data">The data related to the problem, such as a measurement.</param>
            public Entry(ProblemId problem, object data)
            {
                Problem = problem;
                Data = data;
            }

            /// <summary>
            /// Returns a string that represents the current verification entry.
            /// </summary>
            /// <returns>A string describing the problem type and the associated data.</returns>
            public override string ToString()
            {
                return $"{Problem}({(int)Problem}) {Data}";
            }

            /// <summary>
            /// Converts this entry into a JSON object containing the problem ID, its name, and the serialized data (if available).
            /// </summary>
            /// <returns>A <see cref="JsonNode"/> representing the verification entry.</returns>
            public JsonNode ToJson()
            {
                var json = new JsonObject
                {
                    ["problem_id"] = (int)Problem,
                    ["description"] = Problem.ToString()
                };

                if (Data is IJsonSerializable serializable)
                {
                    json["data"] = serializable.ToJson();
                }

                return json;
            }
        }

        private readonly List<Entry> entries = new();

        /// <summary>
        /// Provides string representation of all entries.
        /// </summary>
        public override string ToString() => $"entries:{string.Join(", ", entries)}";

        /// <summary>
        /// Indicates whether the verification passed without any issues.
        /// </summary>
        public bool Success() => entries.Count == 0;

        /// <summary>
        /// Indicates whether the verification encountered one or more issues.
        /// </summary>
        public bool Failed() => entries.Count > 0;

        /// <summary>
        /// Checks if a specific problem has been detected.
        /// </summary>
        public bool HasProblem(ProblemId id) =>
            entries.Exists(entry => entry.Problem == id);

        /// <summary>
        /// List of all detected problems.
        /// </summary>
        public List<Entry> Entries => entries;

        /// <summary>
        /// Checks the result of an auto-gain operation.
        /// </summary>
        public bool Check(AutoGainResult autoGainResult, Hints hints = Hints.NONE)
        {
            if (!autoGainResult.Found)
            {
                entries.Add(new Entry(ProblemId.AUTO_GAIN_RESULT, autoGainResult));
                return false;
            }
            return true;
        }

        /// <summary>
        /// Checks the validity of a single measurement based on saturation and expected behavior.
        /// </summary>
        public bool Check(SingleMeasurement sm, Hints hints = Hints.NONE)
        {
            bool result = true;

            if (sm.Channel470.Value >= MaxSignal)
            {
                entries.Add(new Entry(ProblemId.SATURATION, sm));
                result = false;
            }

            if (hints.HasFlag(Hints.MUST_HAVE_CUVETTE))
            {
                if (!HasCuvette(sm))
                {
                    entries.Add(new Entry(ProblemId.CUVETTE_MISSING, sm));
                    result = false;
                }
            }

            if (hints.HasFlag(Hints.STD_HIGH))
            {
                if (sm.Channel470.Value < (StdHighTarget - StdHighDelta) || sm.Channel470.Value > (StdHighTarget + StdHighDelta))
                {
                    entries.Add(new Entry(ProblemId.WRONG_LEVEL, sm));
                    result = false;
                }
            }

            return result;
        }

        /// <summary>
        /// Checks the validity of a first air measurement result.
        /// </summary>
        public bool Check(FirstAirMeasurementResult fam, Hints hints = Hints.NONE)
        {
            bool r1 = Check(fam.MinMeasurement, Hints.MUST_HAVE_CUVETTE);
            bool r2 = Check(fam.MaxMeasurement, Hints.MUST_HAVE_CUVETTE);
            return r1 && r2;
        }

        /// <summary>
        /// Checks the validity of a first sample measurement result.
        /// </summary>
        public bool Check(FirstSampleMeasurementResult fsm, Hints hints = Hints.NONE)
        {
            bool r1 = Check(fsm.AutoGainResult, hints);
            bool r2 = Check(fsm.Measurement, Hints.MUST_HAVE_CUVETTE | Hints.STD_HIGH);
            return r1 && r2;
        }

        /// <summary>
        /// Checks the validity of a full measurement (air and sample).
        /// </summary>
        public bool Check(Measurement m, Hints hints = Hints.NONE)
        {
            bool r1 = Check(m.air, Hints.MUST_HAVE_CUVETTE);
            bool r2 = Check(m.sample, hints | Hints.MUST_HAVE_CUVETTE);
            return r1 && r2;
        }

        /// <summary>
        /// Validates the computed concentration against negative thresholds.
        /// </summary>
        /// <returns><c>true</c> if concentration ≥ <see cref="ThresholdNegativeConcentration"/>; otherwise <c>false</c>.</returns>
        public bool Check(Results results, Hints hints = Hints.NONE)
        {
            if (results.Concentration < ThresholdNegativeConcentration)
            {
                entries.Add(new Entry(ProblemId.NEGATIVE_CONCENTRATION, results));
                return false;
            }
            return true;
        }

        /// <summary>
        /// Generic check dispatcher that routes different types to the appropriate check method.
        /// </summary>
        public bool Check(object obj, Hints hints = Hints.NONE)
        {
            return obj switch
            {
                AutoGainResult agr => Check(agr, hints),
                SingleMeasurement sm => Check(sm, hints),
                FirstAirMeasurementResult fam => Check(fam, hints),
                FirstSampleMeasurementResult fsm => Check(fsm, hints),
                Measurement m => Check(m, hints),
                Results r => Check(r, hints),
                _ => throw new ArgumentException($"Unsupported class {obj.GetType()}")
            };
        }

        /// <summary>
        /// Converts all entries to a JSON array.
        /// </summary>
        public JsonArray ToJson()
        {
            JsonArray array = new();
            foreach (var entry in entries)
            {
                array.Add(entry.ToJson());
            }
            return array;
        }

        /// <summary>
        /// Heuristic test for cuvette presence based on LED power and expected RFU interpolation
        /// scaled by <see cref="RfuThresholdMultiplier"/>.
        /// </summary>
        private bool HasCuvette(SingleMeasurement sm)
        {
            int ledPower = sm.Channel470.LedPower;
            if (ExpectedMaxLedPower == ExpectedMinLedPower)
                throw new InvalidOperationException("LED power interpolation division by 0");

            // Interpolated expected value
            double slope = (ExpectedMaxRfu - ExpectedMinRfu) / (ExpectedMaxLedPower - ExpectedMinLedPower);
            double expectedRfu = slope * (ledPower - ExpectedMinLedPower) + ExpectedMinRfu;

            return sm.Delta() > expectedRfu * RfuThresholdMultiplier;
        }
    }
}
