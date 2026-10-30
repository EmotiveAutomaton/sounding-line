# D5 source adapter: authenticating the actual upstream plan receipt

Second engineering correction; original module, tests, native completion and
source capsule are retained. The original loader expected a top-level plan
checksum. PMAP's actual terminal records it under `outputs['PLAN.json']`.

The successor changes only that lookup. It retains the required exact plan hash,
all source/identity checks, transforms, census and CPU allowance. Its tests add
the actual producer-loader boundary, a changed-plan refusal and one real complete
session replay as an integration check, with no scientific score. Both original
test invocations, the first native check and all recovery validation remain charged.
No further automatic engineering retry remains after this correction.

## DESIGN CHECK

LESSONS sections 3–5 read for this build. Under NULL and ALTERNATIVE an authentic
producer receipt passes; changed plan bytes refuse before data use. Constructed
native reentry and fresh-process replay must still pass. No effect, scientific
calibration, identification score or new admission threshold is introduced.
