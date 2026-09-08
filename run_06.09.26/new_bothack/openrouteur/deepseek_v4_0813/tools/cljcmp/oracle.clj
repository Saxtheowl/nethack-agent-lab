(ns cljcmp.oracle
  "Differential-test oracle: runs original BotHack functions on serialised (EDN)
  inputs and prints EDN results, one per line, prefixed with RESULT:."
  (:require [bothack.util :refer :all]
            [bothack.position :refer :all]
            [bothack.frame :refer :all]
            [bothack.item :refer :all]
            [bothack.itemtype :refer :all]
            [bothack.itemid :refer :all]
            [bothack.montype :refer :all]
            [bothack.monster :refer :all]
            [bothack.tile :refer :all]
            [clojure.string :as string]
            [clojure.edn :as edn]))

(defn emit [x]
  (println (str "RESULT:" (pr-str x)))
  (flush))

(defn op-position [args]
  (let [[op & more] args]
    (case (keyword op)
      :distance (emit (distance (edn/read-string (first more))
                                (edn/read-string (second more))))
      :manhattan (emit (distance-manhattan (edn/read-string (first more))
                                           (edn/read-string (second more))))
      :towards (emit (towards (edn/read-string (first more))
                              (edn/read-string (second more))))
      :adjacent (emit (adjacent? (edn/read-string (first more))
                                 (edn/read-string (second more))))
      :in-direction (emit (some-> (in-direction (edn/read-string (first more))
                                                (keyword (second more)))
                                  position-map))
      :neighbors (emit (mapv position-map
                             (neighbors (edn/read-string (first more)))))
      :valid (emit (valid-position? (edn/read-string (first more))))
      (emit :unknown-op))))

(defn op-util [args]
  (let [[op & more] args]
    (case (keyword op)
      :effective-str (emit (effective-str (first more)))
      :last-word (emit (last-word (first more)))
      (emit :unknown-op))))

(defn op-item [args]
  (let [[op & more] args]
    (case (keyword op)
      :parse-label (emit (parse-label (first more)))
      :item-type (emit (item-type (label->item (first more))))
      :item-subtype (emit (item-subtype (label->item (first more))))
      :item-weight (emit (item-weight (label->item (first more))))
      :appearance-of (emit (appearance-of (label->item (first more))))
      :initial-ids (emit (mapv :name (initial-ids (label->item (first more)))))
      :corpse (emit (boolean (corpse? (label->item (first more)))))
      :container (emit (container? (label->item (first more))))
      (emit :unknown-op))))

(defn op-monster [args]
  (let [[op & more] args]
    (case (keyword op)
      :name->monster (emit (or (name->monster (first more)) :nil))
      :typename (emit (or (get-in (name->monster (first more)) [:name]) :nil))
      (emit :unknown-op))))

(defn op-tile [args]
  (let [[op & more] args
        g (last (first more))
        color (let [c (second more)] (if (= c "nil") nil (keyword c)))]
    (case (keyword op)
      :monster-glyph (emit (boolean (monster-glyph? g)))
      :monster (emit (boolean (monster? g color)))
      :item (emit (boolean (item? g color)))
      (emit :unknown-op))))

(defn -main [& _]
  (let [in (java.io.BufferedReader. *in*)]
    (loop []
      (when-let [line (.readLine in)]
        (let [[op & args] (string/split line #"\t" -1)]
          (when-not (empty? line)
            (try
              (case op
                "position" (op-position args)
                "util" (op-util args)
                "item" (op-item args)
                "monster" (op-monster args)
                "tile" (op-tile args)
                (emit (str :unknown-op " <" op ">")))
              (catch Throwable e
                (emit (str "ERROR:" (.getMessage e))))))
          (recur)))))
  (System/exit 0))