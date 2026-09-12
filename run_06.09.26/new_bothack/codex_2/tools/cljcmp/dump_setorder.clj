(ns cljcmp.dump-setorder
  "Print the seq order of PersistentHashSets the bot actually builds, so the
  port's model of that order can be checked instead of assumed.  Menu answers
  reach NetHack as `(string/join options)` over such a set, so the order is
  observable behaviour."
  (:require [clojure.pprint]))

(defn- row [coll]
  {:in (vec (map str coll))
   :seq (apply str (seq (set coll)))
   :hasheq (vec (map hash coll))})

(defn -main [& _]
  (clojure.pprint/pprint
    {:cases
     (mapv row
           [[\x \G \i \g \A \o]
            [\A \G \g \i \o \x]
            [\a \b \c]
            [\a \b \c \d \e \f \g \h \i]
            [\A \B \C \a \b \c]
            [\1 \2 \3 \4 \5]
            [\x]
            [\x \G]
            [\G \x]
            [\i \g]
            [\a \A]])
     :string-cases
     (mapv row [["3a" "2b"] ["a" "b" "c"]])}))
