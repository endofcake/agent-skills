Your reasoning on the cache layout is sound, but the estimate omits storage costs. Each replica holds a full copy, so the fifty-gigabyte figure is per node and the cluster total is four hundred gigabytes. Budget for the cluster total.

Your estimate includes the warm-up window, so we can compare deploy costs directly. The window is ninety seconds on the current hardware. Keep it in the model.

You have clearly thought hard about eviction, but the policy is not stated. The code evicts by insertion order, which means the hottest keys leave first under load. Switch to least-recently-used eviction.
