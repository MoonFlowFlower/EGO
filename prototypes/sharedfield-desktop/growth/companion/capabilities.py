"""Describe fixed interfaces, without a table of permitted task categories."""
def capabilities():
    return {'source':'fixed_body_and_harness_interfaces',
            'observations':['inspect','inspect_area','observe_items','search','recall'],
            'actions':['approach','follow','stop','pickup_items','craft','collect','give','place_at','place_many','recover_inventory'],
            'composition':'The model can observe, plan a bounded coordinate layout, and compose these primitives. No built-in building planner or house template.',
            'verification':'Inventory effects, pickup entities, explicit world block/air positions. Counts alone do not establish an entire structure.',
            'collection':'collect mines blocks by type and verifies inventory gain; it cannot target and verify demolition of a particular coordinate.',
            'initiative':'An explicit standing delegation can enable self-selected projects and finite behavior trees. Projects and policy revisions persist; restart/stop require a new delegation. Autonomous effects currently cover crafting, inventory recovery and explicitly bounded coordinate placement.',
            'limits':{'decisions_per_turn':64,'seconds_per_turn':900,'placement_batch_targets':8,'world_verification_targets':128,
                      'generated_code':False,'arbitrary_commands':False,'placement_navigation_breaks_or_places':False}}
