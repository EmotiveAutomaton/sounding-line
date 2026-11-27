# Does a steady room level predict when laughter starts?

In the 75 ICSI meetings the intervals for absolute change, mean level and a high followed by a fall all included zero. Every AMI meeting had an untimed laugh annotation, preventing a separate AMI estimate. ICSI, room, absolute change = -0.0558938 [-0.238486, 0.134813] (75 meetings).

Estimate laugh starts per half minute using the preceding room sound and speech pace. Exclude annotated laughs from both predictors, hold prior laughter and fit within meetings. Use 2,000 whole-meeting resamples. The coefficients are on the log count scale.

Sound level and speech pace stand in for stress. Laughs are loud and cluster in time. Excluding a whole meeting for an untimed laugh removed the entire AMI sample.

Both corpus counts and every fitted coefficient are reported. No ICSI sound-only fit or AMI model met the registered model requirements. Code 12 records an unavailable fit.

[Seven-part report and all released figures](../../../docs/exchange/r48/RML1.md).
