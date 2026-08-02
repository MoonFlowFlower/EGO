# Call-chain audit requirement

The task-local successor must use one physical chain:

`public feature observation -> exact reference plan -> selected positional
action -> task-local world transition/noise -> organism/terminal update ->
public feedback -> exact posterior update -> stored row`.

Candidate functions accept only public slot features, organism values, previous
action and previous realized delta. Evaluator seed, packet/split, combination
index, global mechanism, local mode and future noise must not enter candidate
state or planning/update calls.

The private oracle/aligned arms remain evaluator-only. The current product
controller, engine, store, replay and default mode are not modified by this
capacity certificate.
