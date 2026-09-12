(ns cljcmp.dump-hash
  "Dump the JVM's own hasheq values so the port's implementation of Clojure's
  hashing can be *verified* rather than guessed.

  Clojure set iteration order is the HAMT order of the elements' hasheq, and
  BotHack keeps monsters in sets (`hostile-threats` ends in `set`), so
  `find-first` over one of those sets picks a different monster if the order is
  wrong.  Reproducing that order needs `hasheq` for records, which is
  `(bit-xor type-hash (APersistentMap/mapHasheq record))`.

  Emitted as EDN on stdout:
    :calibration  hasheq of one value of every type a Monster field can hold
    :monster-type-hash  {monster name => (hash type-record)} for all 376 types
    :record-type-hash   {record class => the defrecord type-hash}
    :samples      real-shaped monsters with their hasheq and, for sets of them,
                  the order (seq) the JVM walks
  Nothing here changes BotHack: it only reads its data."
  (:require [clojure.pprint]
            [bothack.monster :as monster]
            [bothack.montype :as montype]
            [bothack.tile]))

(defn- type-hash
  "The defrecord type-hash is (hash classname-symbol) - recompute it the same
  way the macro did, so it can be checked against the record's own hasheq."
  [^Class c]
  (hash (symbol (.getName c))))

(defn- mon [& {:as kvs}]
  (monster/map->Monster (merge {:x 1 :y 1 :known 0 :glyph \d :color :white
                                :type nil :awake false :friendly false
                                :peaceful nil :remembered false}
                               kvs)))

(defn -main [& _]
  (let [dog (get-in montype/appearance->monster [\d :white])
        spider (get-in montype/appearance->monster [\s :gray])
        samples [(mon)
                 (mon :x 23 :y 18 :glyph \d :color :white :type dog
                      :awake true :known 4396 :first-known 4392
                      :fleeing false)
                 (mon :x 23 :y 19 :glyph \s :color :gray :type spider
                      :awake true :known 4396 :first-known 4392
                      :fleeing true)
                 (mon :peaceful true :remembered true :type spider)]
        s (set samples)]
    (clojure.pprint/pprint
      {:calibration
       {:nil (hash nil)
        :true (hash true)
        :false (hash false)
        :char-a (hash \a)
        :char-d (hash \d)
        :char-at (hash \@)
        :long-0 (hash 0)
        :long-1 (hash 1)
        :long-2 (hash 2)
        :long-17 (hash 17)
        :long-4396 (hash 4396)
        :long--1 (hash -1)
        :long-1000000 (hash 1000000)
        :kw-x (hash :x)
        :kw-y (hash :y)
        :kw-white (hash :white)
        :kw-known (hash :known)
        :kw-first-known (hash :first-known)
        :kw-fleeing (hash :fleeing)
        :kw-remembered (hash :remembered)
        :str-empty (hash "")
        :str-abc (hash "abc")
        :str-little-dog (hash "little dog")
        :vec-empty (hash [])
        :vec-1-2 (hash [1 2])
        :set-empty (hash #{})
        :set-kw (hash #{:a :b})
        :map-empty (hash {})
        :map-x1 (hash {:x 1})
        :mapentry-x1 (hash (first {:x 1}))
        :sym-monster (hash 'bothack.monster.Monster)}
       :record-type-hash
       {"bothack.monster.Monster" (type-hash bothack.monster.Monster)
        "bothack.tile.Tile" (type-hash bothack.tile.Tile)}
       :monster-type-hash
       ; keyed by name+glyph+color: three names (werejackal, werewolf,
       ; wererat) carry two distinct type records each, and keying by name
       ; alone would silently give one of them the other's hash
       (vec (for [t montype/monster-types]
              [(:name t) (str (:glyph t)) (str (:color t)) (hash t)]))
       :samples
       (vec (for [m samples]
              {:monster (pr-str (into {} m))
               :keys (vec (map (comp str key) (into {} m)))
               :map-hasheq (clojure.lang.APersistentMap/mapHasheq m)
               :hasheq (hash m)}))
       :set-order (vec (for [m (seq s)] [(:x m) (:y m) (str (:glyph m))
                                         (hash m)]))})))
