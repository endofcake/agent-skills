<!-- One positive per contrast rule, then near-misses. A line's expected counted
rule ids sit in a trailing comment; a line with no comment expects none. -->

The cache is not just a speedup, it changes the failure mode. <!-- expect: CF001 -->

The cache is not only faster but also safer. <!-- expect: CF001 -->

This is more than just a cache. <!-- expect: CF002 -->

More than a cache, it is a contract. <!-- expect: CF002 -->

The boundary is situational, not fixed per pair. <!-- expect: CF003 -->

The job runs weekly, never on demand. <!-- expect: CF004 -->

Read the log rather than guessing. <!-- expect: CF005 -->

This is not a cache. <!-- expect: CF006 -->

It does not simply retry. <!-- expect: CF007 -->

It's not a bug, it's a contract. <!-- expect: CF008 -->

The delay is not really latency — it is backpressure. <!-- expect: CF009 PG001 -->

The flag is not merely cosmetic. <!-- expect: CF010 -->

It really does not simply retry. <!-- expect: CF007 IT002 (the intensifier outside the frame still counts) -->

Whether or not the job runs, the log is written.

The report is not the edit.

The token is factually wrong and the retry does nothing.

The phrase "not just X" is a tell.

The draft read "the cache is not just a speedup for the read path, it is the only thing keeping the write path within budget". <!-- expect: CF001 (quote over 80 characters stays in scope) -->
