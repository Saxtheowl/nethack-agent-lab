(ns cljdump.dumpdata
  "Serialises BotHack's own data structures to JSON so the Python port loads
  them verbatim instead of retyping the large tables (itemdata.clj / montype.clj)."
  (:require [bothack.itemtype :refer :all]
            [bothack.itemdata :refer :all]
            [bothack.itemid :refer :all]
            [bothack.montype :refer :all]
            [bothack.level :refer :all]
            [bothack.sokoban :refer :all]
            [bothack.util :refer :all]
            [clojure.string :as string]))

(defn- kw->str [k] (when k (name k)))

(defn- enc-key [k]
  (cond
    (keyword? k) (kw->str k)
    (map? k) (str "POS:" (:x k) ":" (:y k))
    :else (str k)))

;; ---- minimal JSON emitter, no external deps ----
(declare enc)

(defn- enc-map [m]
  (str "{"
       (->> m
            (map (fn [[k v]] (str (enc (enc-key k)) ":" (enc v))))
            (string/join ","))
       "}"))

(defn- enc-seq [coll]
  (str "[" (string/join "," (map enc coll)) "]"))

(defn enc [x]
  (cond
    (nil? x) "null"
    (true? x) "true"
    (false? x) "false"
    (string? x) (str "\"" (-> x
                              (string/replace "\\" "\\\\")
                              (string/replace "\"" "\\\"")
                              (string/replace "\n" "\\n")) "\"")
    (number? x) (str x)
    (char? x) (str "\"" (string/replace (str x) "\"" "\\\"") "\"")
    (keyword? x) (str "\"" (kw->str x) "\"")
    (map? x) (enc-map x)
    (or (vector? x) (list? x) (set? x) (seq? x)) (enc-seq (if (set? x) (sort-by str x) x))
    :else (str "\"" (str x) "\"")))

(defn- item-kind [item] (kw->str (typekw item)))

(defn- item->plain [item]
  (-> (into {} item)
      (assoc "kind" (item-kind item))
      (update "glyph" #(when % (str %)))))

(defn- attack->plain [a]
  (assoc (into {} a) "type" (kw->str (:type a))
         "damage-type" (kw->str (:damage-type a))))

(defn- monster->plain [m]
  (-> (into {} m)
      (update "glyph" #(when % (str %)))
      (update "color" kw->str)
      (update "alignment" kw->str)
      (update "gen-flags" #(sort (map kw->str %)))
      (update "attacks" #(map attack->plain %))
      (update "sounds" kw->str)
      (update "size" kw->str)
      (update "resistances" #(sort (map kw->str %)))
      (update "resistances-conferred" #(sort (map kw->str %)))
      (update "tags" #(sort (map kw->str %)))))

(defn- appearance->monster-plain [m]
  (into {} (for [[glyph colors] m]
             [(str glyph) (into {} (for [[color mt] colors]
                                     [(kw->str color) (:name mt)]))])))

(defn- bp->plain [bp]
  (let [bp (into {} bp)]
    (-> bp
        (update "branch" kw->str)
        (update "tag" kw->str)
        (update "role" kw->str)
        (update "features" #(into {} (for [[pos feat] %]
                                       [(enc-key pos) (kw->str feat)])))
        (update "monsters" #(into {} (for [[pos m] %]
                                       [(enc-key pos) (:name m)])))
        (update "cutoff-cols" #(when % (vec %)))
        (update "cutoff-rows" #(when % (vec %)))
        (update "undiggable-tiles" #(when % (mapv enc-key %)))
        (update "leader" #(when % (into {} (for [[k v] %] [k v])))))))

(defn- solutions-plain [solutions]
  (into {} (for [[tag counts] solutions]
             [(kw->str tag) (into {} (for [[n path] counts]
                                       [n (mapv (fn [[x y]] [x y]) path)]))])))

(defn- boulders-plain [b]
  (into {} (for [[tag positions] b]
             [(kw->str tag) (mapv #(vector (:x %) (:y %)) positions)])))

(defn- soko-items-plain [si]
  (into {} (for [[tag m] si]
             [(kw->str tag) (into {} (for [[pos name] m]
                                       [(enc-key pos) name]))])))

(defn -main [& _]
  (let [all-items (vec items)
        mon-types monster-types
        names-by-appearance
        (into (sorted-map)
              (for [a (keys item-names)]
                [a (vec (sort (item-names a)))]))
        appearance-candidates
        (into {}
              (for [a (sort (distinct (concat
                                         (keys item-names)
                                         (mapcat :appearances items))))]
                [a (mapv :name (initial-ids {:name a}))]))
        out {:item-kinds (sort (map kw->str (keys item-kinds)))
             :items (mapv item->plain all-items)
             :monster-types (mapv monster->plain mon-types)
             :appearance->monster (appearance->monster-plain appearance->monster)
             :appearance->monster-raw (appearance->monster-plain appearance->monster)
             :item-names (into {} (for [[k v] names-by-appearance] [k v]))
             :names (sort (vec names))
             :exclusive-appearances (sort (vec exclusive-appearances))
             :blind-appearances (into {} (for [[k v] blind-appearances]
                                           [k (:name v)]))
             :appearance-candidates appearance-candidates
             :plural->singular plural->singular
             :jap->eng jap->eng
             :blind-plurals blind-plurals
             :blueprints (mapv bp->plain blueprints)
             :sokoban-solutions (solutions-plain @#'bothack.sokoban/solutions)
             :sokoban-initial-boulders (boulders-plain initial-boulders)
             :sokoban-items (soko-items-plain @#'bothack.sokoban/soko-items)}]
    (println (enc out))))

(doseq [n (range 0)]
  (println n))