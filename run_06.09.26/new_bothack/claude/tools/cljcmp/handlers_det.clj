(ns cljcmp.handlers-det
  "Pin BotHack's handler tie-break order for comparison runs.

  The original keeps its handlers in a `clojure.data.priority-map` and its own
  docstring says \"for handlers of the same priority order of invocation is not
  specified\".  In practice the order is the hash order of `reify` objects,
  i.e. their *identity* hashes, so the original is not reproducible against
  itself: its first two actions are `Discoveries, Inventory` in one JVM run and
  `Inventory, Discoveries` in the next.

  Nothing here changes what the bot decides - it only makes the tie total, by
  appending a registration counter to each handler's priority, which is what
  the Python port does.  BotHack itself is not modified; the vars are rebound
  from the comparison harness."
  (:require [clojure.data.priority-map :as pm]
            [bothack.delegator :as delegator]
            [bothack.util :as util]))

(def ^:private reg-seq (atom 0))

(defn install!
  "Rebind new-delegator/register so that equal priorities keep registration
  order.  Idempotent-ish: call once, before the bot starts."
  []
  (reset! reg-seq 0)
  (alter-var-root
    #'delegator/new-delegator
    (constantly
      (fn [writer]
        (delegator/->Delegator writer (pm/priority-map-by compare) false))))
  (alter-var-root
    #'delegator/register
    (constantly
      (fn register*
        ([d handler] (register* d util/priority-default handler))
        ([d priority handler]
         ;; `switch` re-registers with the value it read back out of the map,
         ;; which is now [priority seq] - unwrap it
         ;; `update` is Clojure 1.7; this project is on 1.6 (BotHack's own
         ;; util.clj backports it, but not into this namespace)
         (let [p (if (vector? priority) (first priority) priority)]
           (assoc d :handlers
                  (assoc (:handlers d) handler [p (swap! reg-seq inc)]))))))))
