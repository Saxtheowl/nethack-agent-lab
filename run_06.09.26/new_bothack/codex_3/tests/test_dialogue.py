from bothack_new.dialogue import Prompt, Transaction, classify
def test_prompts_and_cancellation():
    assert classify("In what direction?") == Prompt.DIRECTION
    assert classify("There is already a game in progress. Do what?") == Prompt.START
    assert classify("Are you sure you want to pray? [yn]") == Prompt.START
    assert classify("Really attack the hobbit? [yn]") == Prompt.START
    assert classify("Beware, there will be no return! Still climb? [yn]") == Prompt.START
    tx=Transaction("dig",{Prompt.GAME},0); assert not tx.observe(Prompt.MENU); tx.cancel("stale frame"); assert not tx.observe(Prompt.GAME)
