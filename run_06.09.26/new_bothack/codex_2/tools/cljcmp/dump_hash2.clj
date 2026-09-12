(ns cljcmp.dump-hash2
  "Second calibration pass: the intermediate values of keyword/symbol hashing,
  so the port's implementation can be pinned down instead of guessed."
  (:require [clojure.pprint]))

(defn -main [& _]
  (clojure.pprint/pprint
    (into (sorted-map)
          (for [n ["x" "y" "known" "white" "fleeing" "first-known"
                   "remembered" "bothack.monster.Monster"]]
            [n {:huc (clojure.lang.Murmur3/hashUnencodedChars n)
                :str-hashcode (.hashCode n)
                :sym-hasheq (.hasheq (symbol n))
                :sym-hashcode (.hashCode (symbol n))
                :kw-hasheq (.hasheq (keyword n))
                :kw-hashcode (.hashCode (keyword n))
                :hash-kw (hash (keyword n))
                :hash-sym (hash (symbol n))}]))))
