from bothack_new.world import World
from bothack_new.strategy import Strategy
from bothack_new.dialogue import Prompt
def test_snapshots_are_immutable_and_strategy_explores():
    old=World().observe(("@", "HP:10(20) Dlvl:3 T:7")); new=old.observe((".@", "HP:10(20) Dlvl:3 T:7"), "fresh message"); assert old.screen == ("@", "HP:10(20) Dlvl:3 T:7")
    assert old.hp == 10 and old.max_hp == 20 and old.level == 3
    assert old.game_turn == 7
    d=Strategy().decide(new,Prompt.GAME); assert d.keys and d.reason
    for _ in range(100):
        assert Strategy().decide(new,Prompt.GAME).keys

def test_food_letter_comes_from_prompt():
    world = World().observe(("Hungry", "What do you want to eat? [d or ?*]"))
    decision = Strategy().decide(world, Prompt.MENU)
    assert decision.keys == b"d"

def test_pager_is_advanced_before_menu_cancel():
    world = World().observe(("--More--",))
    assert Strategy().decide(world, Prompt.MENU).keys == b" "

def test_empty_food_is_a_one_shot_state():
    world = World().observe(("Hungry",), "You don't have anything to eat.")
    strategy = Strategy()
    assert strategy.decide(world, Prompt.GAME).keys == b"#pray\n"
    assert not world.food_search_started().food_unavailable

def test_adjacent_monster_gets_attacked():
    world = World().observe((".....", "..r@.", ".....", "HP:10(20)"))
    assert world.adjacent_monster_key() == b"h"

def test_visible_stair_is_a_navigation_target():
    world = World().observe((".....", "..@.>", ".....", "HP:10(20)"))
    assert world.stair_key() == b"u"

def test_nonalphabetic_monster_and_corridor_are_playable():
    world = World().observe(("########", "#@:#>..#", "########"))
    assert world.adjacent_monster_key() == b"l"
    world = World().observe(("########", "#@..>..#", "########"))
    assert world.stair_key() == b"u"

def test_stair_is_used_after_player_reaches_memorized_coordinate():
    world = World().observe((".....", "..@..", ".....", "HP:10(20)"))
    world = world.observe((".....", "..@..", ".....", "HP:10(20)"), "")
    world = world.__class__(**{**world.__dict__, "known_stairs": ((2, 1, ">"),)})
    assert world.stair_action() == b">"

def test_blind_critical_state_requests_emergency_prayer():
    world = World().observe(("Blind", "HP:6(18)"))
    assert Strategy().decide(world, Prompt.GAME).keys == b"#pray\n"

def test_fainting_critical_state_requests_emergency_prayer():
    world = World().observe(("Fainted", "HP:5(18)"))
    assert Strategy().decide(world, Prompt.GAME).keys == b"#pray\n"

def test_empty_food_and_hunger_prays_before_searching():
    world = World().observe(("Hungry", "HP:20(20)"), "You don't have anything to eat.")
    assert Strategy().decide(world, Prompt.GAME).keys == b"#pray\n"

def test_repeated_prayer_is_declined():
    world = World().observe(("Are you sure you want to pray? [yn]",))
    assert Strategy().decide(world, Prompt.START).keys == b"n"

def test_critical_recent_damage_reverses_last_direction():
    strategy = Strategy()
    world = World().observe(("@", "HP:6(20)"), "The jackal bites!")
    strategy.last_direction = b"l"
    assert strategy.decide(world, Prompt.GAME).keys == b"k"

def test_peaceful_attack_confirmation_is_declined_and_followed_by_escape():
    strategy = Strategy()
    world = World().observe(("Really attack the hobbit? [yn]",))
    assert strategy.decide(world, Prompt.START).keys == b"n"
    assert strategy.decide(World().observe(("@", "HP:20(20)")), Prompt.GAME).reason == "leave peaceful creature's square"

def test_fainted_state_does_not_send_movement():
    strategy = Strategy()
    world = World().observe(("Fainted", "HP:6(18)"))
    decision = strategy.decide(world, Prompt.GAME)
    assert decision.keys == b"#pray\n"
