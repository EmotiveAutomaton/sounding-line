# EVENT IDLE WAKE POLICY 20261108

**Hypothesis.** Can the operating session stop waking on hourly timers while retaining event delivery, unattended recovery and all running work?

**METHOD.** Apply the curator's explicit November 8 cadence change to the existing durable watcher, preserve all event paths and outbox records, retire the identified calendar that recreated hourly deadlines, and start a pinned calendar-only successor with identical milestone dates and copied completed marker bytes. Test the exact inactivity boundary, reset on activity or acknowledgement, ordinary completion delivery and calendar behavior; verify a subsequent live watcher scan and calendar heartbeat.

**Found.** Wakeups now follow events or four hours of owner inactivity; hourly build deadlines and fixed health timers are retired, with research jobs and result notifications preserved.

Four focused software tests pass. The inactivity fallback is 14,400 seconds from the latest real owner activity, completed acknowledgement or previous idle check. It is not a fixed four-hour periodic deadline. Routine events no longer wait for a scheduled build check; active-owner suppression and existing urgent-event handling remain. Terminal, failure, disappearance and campaign-milestone watches remain registered. An accepted or pending scientific event is not acknowledged by this configuration change.

The original calendar source, immutable plan, owner and completed daily marker remain retained. Its exact native process was intentionally replaced because it would otherwise recreate the hourly timer. The successor preserves every milestone date and the existing marker bytes. Research workers and the durable watcher were not restarted; original research plans were checked unchanged. The watcher subsequently scanned with the new configuration, the successor emitted a live event/idle heartbeat, and both fixed schedules remain absent. No existing timer event required cancellation at installation.

The current AGENTS instruction and operations guide explicitly supersede amendment I's hourly timing, the fixed six-hour cadence and older skill/closure-helper scheduling defaults. Existing scientific authority, gear, resource guards, spending limits, full write-through and final-packet reporting remain in force. The calendar's current native pointer and migration/rollback evidence remain private. No publication or new scientific test is introduced.

**Means.** Let event delivery and the resettable four-hour inactivity fallback wake the owner. Do not recreate hourly or half-hourly build schedules or fixed health timers. Continue authorized build and recovery work when an event or inactivity wake requires it; preserve all unfinished campaign obligations.
