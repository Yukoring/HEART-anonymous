# Real-robot execution logs

One file per run of the Farm experiment reported in Table V: five scenes,
three methods, three trials each (45 runs). `run10` has two files because the
first attempt aborted before the arm moved, when the perception module failed
to register a tomato's location; `attempt2` is the run that was scored.

    run<NN>_scene<S>_<method>_trial<T>.txt

Each file records the plan that was executed, whether every action completed
(`success`), why the run ended (`end_reason`), and per-action execution time.
A pick is recorded as failed when the action aborts or the gripper closes
empty. Videos of the runs are on the project page.
