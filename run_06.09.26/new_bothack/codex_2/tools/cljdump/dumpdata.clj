(ns dumpdata
  "Dump BotHack's item/monster reference data to JSON so the Python port can
  use byte-identical data instead of a hand-transcription."
  (:require [clojure.string :as string]
            [bothack.itemdata :as idata]
            [bothack.itemtype :as it]
            [bothack.itemid :as itemid]
            [bothack.montype :as mt]
            [bothack.util :refer [typekw]])
  (:gen-class))

(defn- esc [s]
  (str \" (-> (str s)
              (string/replace "\\" "\\\\")
              (string/replace "\"" "\\\"")
              (string/replace "\n" "\\n")
              (string/replace "\t" "\\t")
              (string/replace "\r" "\\r"))
       \"))

(declare jsn)

(defn- jsn-map [m]
  (str "{\"__map__\":["
       (string/join "," (for [[k v] m] (str "[" (jsn k) "," (jsn v) "]")))
       "]}"))

(defn jsn [x]
  (cond
    (nil? x) "null"
    (true? x) "true"
    (false? x) "false"
    (keyword? x) (esc (name x))
    (char? x) (esc (str x))
    (string? x) (esc x)
    (number? x) (str x)
    (ratio? x) (str (double x))
    (set? x) (str "{\"__set__\":[" (string/join "," (map jsn x)) "]}")
    (map? x) (jsn-map x)
    (sequential? x) (str "[" (string/join "," (map jsn x)) "]")
    :else (throw (IllegalArgumentException. (str "cannot serialize " (type x) " " x)))))

(defn- item->map [i]
  (-> (into {} i)
      (assoc :kind (name (typekw i)))
      ; :monster is a MonsterType record - store just the name, re-linked in
      ; Python.  Absent keys must stay absent (merge-records uses contains?).
      ((fn [m] (if (contains? m :monster)
                 (assoc m :monster (:name (:monster m))) m)))
      ((fn [m] (if (contains? m :appearances)
                 (assoc m :appearances (if (:appearances m)
                                         (vec (:appearances m)))) m)))))

(declare -dump-levels)

(defn -main [& [outfile]]
  (let [data {:items (mapv item->map it/items)
              :generic-plurals idata/generic-plurals
              :blind-plurals it/blind-plurals
              :jap->eng it/jap->eng
              :exclusive-appearances idata/exclusive-appearances
              :scroll-appearances (vec idata/scroll-appearances)
              :potion-appearances (vec idata/potion-appearances)
              :amulet-appearances (vec idata/amulet-appearances)
              :spellbook-appearances (vec idata/spellbook-appearances)
              :wands-appearances (vec idata/wands-appearances)
              :ring-appearances (vec idata/ring-appearances)
              :armor-appearances (vec idata/armor-appearances)
              :stone-gems (vec idata/stone-gems)
              :gem-gems (vec idata/gem-gems)
              ; appearance => candidate ids in the exact order core.logic
              ; enumerates them (the Python port reuses this order so that
              ; item-weight/subtype of ambiguous appearances match)
              :appearance-names
              (let [apps (set (concat
                                (for [{:keys [appearances] :as i} it/items
                                      :when (not (and (:artifact i) (:base i)))
                                      a appearances] a)
                                (for [{:keys [appearances] :as i} it/items
                                      :when (not (and (:artifact i) (:base i)))
                                      a appearances
                                      n (itemid/item-names a)] n)))]
                (into {} (for [a apps]
                           [a (vec (map :name (itemid/initial-ids
                                                {:name a})))])))
              :monster-types (mapv #(into {} %) mt/monster-types)
              :shopkeepers mt/shopkeepers
              :role-ranks mt/role-ranks}]
    (spit (or outfile "bothack-data.json") (jsn data))
    (-dump-levels (string/replace (or outfile "bothack-data.json") "_data.json" "_leveldata.json"))
    (println "wrote" (or outfile "bothack-data.json")
             "items:" (count it/items)
             "monsters:" (count mt/monster-types))))

(defn -dump-levels [outfile]
  (require 'bothack.level 'bothack.sokoban 'bothack.dungeon 'bothack.position)
  (let [lvl (find-ns 'bothack.level)
        sok (find-ns 'bothack.sokoban)
        dun (find-ns 'bothack.dungeon)
        v (fn [ns n] (deref (ns-resolve ns (symbol n))))
        bp (fn [b] (-> b
                       (update-in [:monsters]
                                  #(when % (into {} (for [[p m] %] [p (:name m)]))))))
        data {:blueprints (mapv bp (v lvl "blueprints"))
              :wiztower-boundary (v lvl "wiztower-boundary")
              :wiztower-inner-boundary (v lvl "wiztower-inner-boundary")
              :wiztower-rect (v lvl "wiztower-rect")
              :geh-maze (v lvl "geh-maze")
              :oracle-position (v lvl "oracle-position")
              :soko-solutions (v sok "solutions")
              :soko-initial-boulders (v sok "initial-boulders")
              :soko-items (v sok "soko-items")
              :fake-wiztower-water (v dun "fake-wiztower-water")
              :fake-wiztower-portal (v dun "fake-wiztower-portal")
              :soko-recog (v dun "soko-recog")
              ;; Clojure's hash for every possible Position: the port needs it
              ;; to break clojure.data.priority-map ties in the pathfinder the
              ;; same way the original does (see docs/PORT.md)
              :position-hashes
              (vec (for [y (range 1 22) x (range 0 80)]
                     (hash ((deref (ns-resolve 'bothack.position 'position))
                            x y))))}]
    (spit outfile (jsn data))
    (println "wrote" outfile "blueprints:" (count (:blueprints data)))))
