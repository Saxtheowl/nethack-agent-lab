(ns cljcmp.dbg-inv
  "Opt-in tracing of (:inventory player)'s iteration order and of the slot
  choose-food picks.  The order is what decides the tie between two food
  stacks of equal nutrition/weight, and it is not printed anywhere in
  BotHack's own logs.  Enabled with BOTHACK_INV_TRACE=<file>."
  (:require [clojure.string :as string]
            [bothack.bots.mainbot]
            [bothack.position]
            [bothack.tile]
            [bothack.dungeon]
            [bothack.player]))

(def ^:private trace-file (System/getenv "BOTHACK_INV_TRACE"))

(def ^:private arb-file (System/getenv "BOTHACK_ARB_TRACE"))

(defn install-arb! []
  (when arb-file
    (let [v (ns-resolve 'bothack.actions 'arbitrary-move)
          orig @v]
      (alter-var-root
        v (constantly
            (fn
              ([game level] ((deref v) game level false))
              ([game level diagonal?]
               (let [player (:player game)
                     nbrs (if diagonal?
                            (bothack.position/diagonal-neighbors level player)
                            (bothack.position/neighbors level player))
                     r (orig game level diagonal?)]
                 (spit arb-file
                       (format "ARB player=(%d,%d) diag=%s nbrs=%s -> %s%n"
                               (:x player) (:y player) diagonal?
                               (pr-str (vec (map (juxt :x :y) nbrs)))
                               (pr-str (some-> r :dir str)))
                       :append true)
                 r))))))))

(def ^:private blk-file (System/getenv "BOTHACK_BLOCKED_TRACE"))

(defn install-blocked! []
  (when blk-file
    (let [v (ns-resolve 'bothack.pathing 'fidget)
          orig @v]
      (alter-var-root
        v (constantly
            (fn
              ([game] ((deref v) game (bothack.dungeon/curlvl game)))
              ([game level] ((deref v) game level nil))
              ([game level target]
               (let [r (orig game level target)]
                 (spit blk-file
                       (format "FIDGET target=%s blocked=%s -> %s reasons=%s%n"
                               (pr-str (some-> target ((juxt :x :y))))
                               (pr-str (some-> target
                                               (->> (bothack.dungeon/at-curlvl game))
                                               :blocked))
                               (pr-str (some-> r bothack.util/typekw))
                               (pr-str (vec (map #(subs (str %) 0 (min 30 (count (str %))))
                                                 (:reason r)))))
                       :append true)
                 r))))))))

(def ^:private ex-file (System/getenv "BOTHACK_EXAMINE_TRACE"))

(defn install-examine! []
  (when ex-file
    (let [v (ns-resolve 'bothack.actions 'examine-tile)
          orig @v]
      (alter-var-root
        v (constantly
            (fn [game]
              (let [r (orig game)
                    t (bothack.dungeon/at-player game)]
                (when t
                  (spit ex-file
                        (format "turn=%s tile=(%s,%s) new-items=%s unknown=%s e=%s examined=%s -> look=%s%n"
                                (:turn game) (:x t) (:y t)
                                (pr-str (:new-items t))
                                (pr-str (bothack.tile/unknown? t))
                                (pr-str (bothack.tile/e? t))
                                (pr-str (:examined t))
                                (pr-str (boolean r)))
                        :append true))
                r)))))))

(def ^:private vis-file (System/getenv "BOTHACK_VISIBLE_TRACE"))
(def ^:private vis-n (atom 0))

(defn install-visible! []
  (when vis-file
    (let [v (ns-resolve 'bothack.fov 'visible?)
          orig @v]
      (alter-var-root
        v (constantly
            (fn
              ([game pos] ((deref v) game (bothack.dungeon/curlvl game) pos))
              ([game level pos]
               (let [r (orig game level pos)]
                 (when (and (= 5 (:x pos)) (= 18 (:y pos))
                            (< 1340 (or (:turn game) 0)) (< @vis-n 60))
                   (swap! vis-n inc)
                   (spit vis-file
                         (format "turn=%s player=(%s,%s) pos=(5,18) in-fov=%s lit=%s -> %s%n  fov=%s%n  transp=%s%n  glyphs=%s%n"
                                 (:turn game) (:x (:player game)) (:y (:player game))
                                 (pr-str (boolean (bothack.fov/in-fov? game pos)))
                                 (pr-str (boolean (bothack.dungeon/lit? (:player game) level pos)))
                                 (pr-str (boolean r))
                                 (pr-str (vec (for [y (range 14 21)]
                                                (vec (for [x (range 0 13)]
                                                       (if (get-in game [:fov y x]) 1 0))))))
                                 (pr-str (vec (for [y (range 14 21)]
                                                (vec (for [x (range 0 13)]
                                                       (if (bothack.tile/transparent?
                                                             (get-in level [:tiles y x])) 1 0))))))
                                 (pr-str (vec (for [y (range 14 21)]
                                                (apply str (for [x (range 0 13)]
                                                             (or (:glyph (get-in level [:tiles y x])) \space)))))))
                         :append true))
                 r))))))))

(def ^:private upd-file (System/getenv "BOTHACK_UPDTILE_TRACE"))
(def ^:private upd-n (atom 0))

(defn install-updtile! []
  (when upd-file
    (let [v (ns-resolve 'bothack.handlers 'update-at-player-when-known)
          orig @v]
      (alter-var-root
        v (constantly
            (fn [bh update-fn & args]
              (let [g @(:game bh)]
                (when (and (< 1340 (or (:turn g) 0)) (< @upd-n 40))
                  (swap! upd-n inc)
                  (spit upd-file
                        (format "REGISTER turn=%s player=(%s,%s)%n"
                                (:turn g) (:x (:player g)) (:y (:player g)))
                        :append true)))
              (apply orig bh
                     (fn [tile & as]
                       (when (and (< 1340 (or (:turn @(:game bh)) 0))
                                  (< @upd-n 40))
                         (swap! upd-n inc)
                         (spit upd-file
                               (format "  FIRE tile=(%s,%s)%n" (:x tile) (:y tile))
                               :append true))
                       (apply update-fn tile as))
                     args)))))))

(def ^:private ni-file (System/getenv "BOTHACK_NEWITEMS_TRACE"))
(def ^:private ni-x (Integer/parseInt (or (System/getenv "BOTHACK_NEWITEMS_X") "5")))
(def ^:private ni-y (Integer/parseInt (or (System/getenv "BOTHACK_NEWITEMS_Y") "18")))

(defn- ni-tile [c]
  (if (:dungeon c)
    (bothack.position/at (bothack.dungeon/curlvl c) ni-x ni-y)
    (when (:tiles c) (bothack.position/at c ni-x ni-y))))

(defn- ni-frames []
  (->> (.getStackTrace (Thread/currentThread))
       (map str)
       (filter #(.contains ^String % "bothack"))
       (remove #(.contains ^String % "dbg_inv"))
       (take 10)
       (string/join " <- ")))

(defn install-newitems! []
  (when ni-file
    (let [v (ns-resolve 'bothack.dungeon 'update-at)
          orig @v]
      (alter-var-root
        v (constantly
            (fn [c pos f & args]
              (let [before (when (and (= ni-x (:x pos)) (= ni-y (:y pos)))
                             (ni-tile c))
                    r (apply orig c pos f args)]
                (when before
                  (let [after (ni-tile r)]
                    (when (not= (:new-items before) (:new-items after))
                      (spit ni-file
                            (format "turn=%s kind=%s new-items %s -> %s :: %s%n"
                                    (pr-str (:turn c))
                                    (if (:dungeon c) "game" "level")
                                    (pr-str (:new-items before))
                                    (pr-str (:new-items after))
                                    (ni-frames))
                            :append true))))
                r)))))))

(defn install! []
  (install-arb!)
  (install-newitems!)
  (install-updtile!)
  (install-visible!)
  (install-examine!)
  (install-blocked!)
  (when trace-file
    (let [v (ns-resolve 'bothack.bots.mainbot 'choose-food)
          orig @v]
      (alter-var-root
        v (constantly
            (fn [game]
              (let [r (orig game)
                    inv (get-in game [:player :inventory])]
                (spit trace-file
                      (format "choose-food -> %s   order=%s%n"
                              (pr-str (some-> r first str))
                              (pr-str (vec (map str (keys inv)))))
                      :append true)
                r)))))))
