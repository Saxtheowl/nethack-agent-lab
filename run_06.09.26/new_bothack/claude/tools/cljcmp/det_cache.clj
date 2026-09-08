(ns cljcmp.det-cache
  "Deterministic-exploration-cache mode for comparison runs.

  BotHack fills `:explore-cache` with `(future (curlvl-exploration game))`, so
  the computation races with the agent threads that drive the bot.  That
  computation draws from the RNG (through `navigate` -> `pass-monster` ->
  `fidget` -> `arbitrary-move`), so **the original is not reproducible against
  itself**: replaying the same seed twice diverges (measured: seeds 40001,
  40004 and 40005 all differ from themselves within one game).

  This mode computes the same value **eagerly, on the calling thread**, and
  stores it in an already-completed future so that `deref`, `exploration-index`
  and `future-cancel` all keep working unchanged.  Nothing else about the bot
  is altered.

  This is a deliberate change of contract, not a bug fix: it defines a
  deterministic reference to compare against.  Captures recorded without it
  are not retroactively explained by it."
  (:require [bothack.pathing]
            [bothack.dungeon :refer [branch-key]]
            [bothack.util :refer [typekw]]
            [bothack.delegator :refer :all]
            [clojure.tools.logging :as log]))

(defn install! []
  (let [curlvl-exploration @(ns-resolve 'bothack.pathing 'curlvl-exploration)
        exploration-index @(ns-resolve 'bothack.pathing 'exploration-index)]
    (alter-var-root
      (ns-resolve 'bothack.pathing 'reset-exploration)
      (constantly
        (fn [bh]
          (let [loc (atom nil)
                save (atom false)]
            (reify
              DlvlChangeHandler
              (dlvl-changed [_ _ _]
                (reset! save true))
              ActionChosenHandler
              (action-chosen [_ action]
                (if-not (#{:call :name :discoveries :inventory :look :farlook}
                          (typekw action))
                  (when-let [f (:explore-cache @(:game bh))]
                    (if @save
                      (swap! (:game bh)
                             #(assoc-in % [:dungeon :levels
                                           (branch-key % (@loc 0))
                                           (@loc 1) :explored]
                                        (exploration-index %))))
                    (swap! (:game bh) assoc :explore-cache nil)
                    (future-cancel f))))
              AboutToChooseActionHandler
              (about-to-choose [_ game]
                (reset! loc [(:branch-id game) (:dlvl game)])
                ;; computed here, on this thread, before anything can race it
                (let [v (curlvl-exploration game)]
                  (swap! (:game bh) assoc :explore-cache
                         (doto (future v) deref)))))))))))
