;; Test-only oracle. Runs the unmodified BotHack Clojure code. GPL-2.0.
(require '[clojure.edn :as edn]
         '[clojure.walk :as walk]
         '[bothack.position :as p]
         '[bothack.frame :as f]
         '[bothack.item :as i]
         '[bothack.itemtype :as it]
         '[bothack.itemdata :as data]
         '[bothack.itemid :as itemid]
         '[bothack.montype :as m]
         '[bothack.monster :as monster]
         '[bothack.scraper :as scraper]
         '[bothack.sokoban :as soko]
         '[bothack.player :as player]
         '[bothack.tile :as tile]
         '[bothack.pathing :as pathing]
         '[bothack.term :as term]
         '[bothack.bots.mainbot :as mainbot]
         '[bothack.bothack :as bh]
         '[bothack.util :as u])

(defn action-input [[kind args]]
  (let [ctor (ns-resolve 'bothack.actions (symbol (str "->" kind)))
        args (mapv #(if (and (map? %) (:character %)) (first (:character %)) %) args)
        args (cond
               (= kind "Repeated") (assoc args 0 (action-input (first args)))
               (#{"Wear" "PutOn" "Remove" "TakeOff"} kind)
               (assoc args 0 (if (char? (first args)) (first args) (first (first args))))
               (#{"Attack" "Move" "FarmAttack" "Kick" "Close" "Open" "Chat"} kind)
               (assoc args 0 (keyword (first args)))
               :else args)]
    (apply @ctor args)))

(defn player-input [input]
  (-> input
      (update-in [:intrinsics] #(set (map keyword %)))
      (update-in [:state] #(set (map keyword %)))
      (update-in [:race] keyword)))

(defn inventory-input [entries]
  (into {} (for [[slot label contents] entries]
             [(first slot) (cond-> (i/label->item label)
                            contents (assoc :items (mapv i/label->item contents)))])))

(def terminal (atom nil))
(defn reset-terminal []
  (reset! terminal (doto (proxy [de.mud.terminal.vt320] [80 24]
                           (write [b]) (sendTelnetCommand [cmd]))
                    (.setTerminalID "xterm"))))

(defn tile-input [t]
  (-> t
      (update-in [:glyph] #(when % (first %)))
      (update-in [:item-glyph] #(when % (first %)))
      (update-in [:color] #(when % (keyword %)))
      (update-in [:item-color] #(when % (keyword %)))
      (update-in [:feature] #(when % (keyword %)))
      (update-in [:engraving-type] #(when % (keyword %)))
      (update-in [:tags] #(set (map keyword %)))))

(defn identified [names facts]
  (let [game (reduce (fn [g [kind appearance a b c]]
                       (case kind
                         "discovery" (itemid/add-discovery g appearance a)
                         "cost" (itemid/add-observed-cost g appearance a b (boolean c))
                         "property" (itemid/add-prop-discovery g appearance (keyword a)
                                      (if (string? b) (keyword b) b))
                         "used" (update-in g [:used-names] conj appearance)
                         "forget" (itemid/forget-names g appearance)))
                     {:discoveries (itemid/new-discoveries) :used-names #{}} facts)]
    (into {} (for [name names] [name (itemid/possible-names game {:name name})]))))

(defn plain [x]
  (cond
    (keyword? x) (name x)
    (char? x) (str x)
    (map? x) (into {} (for [[k v] x] [(plain k) (plain v)]))
    (set? x) (vec (sort-by pr-str (map plain x)))
    (sequential? x) (mapv plain x)
    :else x))

(defn world-level [label branch tags patches]
  (reduce (fn [level [x y values]]
            (bothack.dungeon/update-at level (p/position x y) merge
              (into {} (for [[k v] values]
                         [k (cond
                              (= k :tags) (set (map keyword v))
                              (#{:feature :color :room :branch-id} k) (when v (keyword v))
                              (= k :glyph) (first v)
                              :else v)]))))
          (assoc (bothack.level/new-level label (keyword branch)) :tags (set (map keyword tags))) patches))

(defn level-summary [level]
  {:tiles (mapv (fn [row] (mapv #(select-keys % [:x :y :glyph :feature :undiggable :seen :walked :searched :room :tags]) row)) (:tiles level))
   :monsters (vec (:monsters level)) :tags (:tags level)})

(defn tracker-monster [{:keys [x y name turn glyph color] :as input}]
  (merge (if name
           (assoc (monster/known-monster x y (m/name->monster name)) :remembered false)
           (monster/new-monster x y (or turn 10) (first glyph) (when color (keyword color))))
         (cond-> (dissoc input :name :glyph :color)
           (= "update" (:peaceful input)) (assoc :peaceful :update))))

(defn dispatch [{:keys [op args]}]
  (case op
    :game-events (let [messages (first args)
                       game (atom (-> (bothack.game/new-game)
                                      (assoc :dlvl "Dlvl:1" :turn 100)
                                      (update-in [:player] merge {:x 40 :y 10 :hp 20 :state #{} :intrinsics #{}})
                                      (bothack.dungeon/ensure-curlvl)))
                       context (bh/map->BotHack {:game game})
                       calls (atom []) pending (atom [])]
                   (with-redefs [bothack.actions/update-inventory (fn [_] (swap! calls conj "inventory") context)
                                 bothack.actions/possible-autoid (fn [_ slot] (swap! calls conj ["autoid" slot]) context)
                                 bothack.actions/update-tile (fn [_] (swap! calls conj "tile") context)
                                 bothack.actions/update-discoveries (fn [_] (swap! calls conj "discoveries") context)
                                 bothack.handlers/update-on-known-position (fn [_ f & args]
                                                                            (swap! calls conj "position")
                                                                            (swap! pending conj [f args]) context)
                                 bothack.handlers/update-before-action (fn [_ f & args]
                                                                        (swap! calls conj "before")
                                                                        (swap! pending conj [f args]) context)]
                     (let [handler (if (second args)
                                     (bothack.action/handler (action-input (second args)) context)
                                     (bothack.game/game-handler context))]
                       (doseq [message messages] (bothack.delegator/message handler message))
                       (doseq [[f args] @pending] (apply swap! game f args))
                       {:player (:player @game) :level (level-summary (bothack.dungeon/curlvl @game))
                        :prayer (:last-prayer @game) :angry (:god-angry @game) :calls @calls})))
    :game-maps (let [initial (bothack.game/new-game)]
                 (second (reduce (fn [[game results] input]
                                   (let [frame (f/map->Frame (update-in input [:colors]
                                                             #(mapv (fn [row] (mapv (fn [c] (when c (keyword c))) row)) %)))
                                         status (@#'scraper/parse-botls (f/botls frame))
                                         updated (-> game
                                                     (assoc :frame frame)
                                                     (@#'bothack.game/update-by-botl status)
                                                     (update-in [:player] merge (:cursor frame))
                                                     (bothack.dungeon/ensure-curlvl)
                                                     (@#'bothack.game/update-map frame))]
                                     [updated (conj results {:level (level-summary (bothack.dungeon/curlvl updated))
                                                             :player (:player updated) :fov (mapv vec (:fov updated))})]))
                                 [initial []] (first args))))
    :track (let [[p old-input new-input] args
                 p (player-input p)
                 level (assoc (bothack.level/new-level "Dlvl:1" :main)
                              :tiles (mapv (fn [row] (mapv #(assoc % :feature :floor :glyph \.) row))
                                           (:tiles (bothack.level/new-level "Dlvl:1" :main))))
                 game (-> (bothack.game/new-game)
                          (assoc :player p :dlvl "Dlvl:1" :fov (vec (repeat 22 (vec (repeat 80 true)))))
                          (bothack.dungeon/add-level level))
                 populate (fn [inputs] (reduce bothack.dungeon/reset-monster game (map tracker-monster inputs)))
                 result (bothack.tracker/track-monsters (populate new-input) (populate old-input))]
             (vec (sort-by (juxt :x :y) (bothack.dungeon/curlvl-monsters result))))
    :fresh-deaths (let [[name turn deaths] args
                        corpse-type (m/name->monster name)
                        tile {:deaths (mapv (fn [[t name]] [t {:type (when name (m/name->monster name))}]) deaths)}]
                    (boolean (@#'bothack.tracker/only-fresh-deaths? tile corpse-type turn)))
    :blueprint (let [[index patches] args
                     blueprint (nth bothack.level/blueprints index)
                     level (world-level (or (:dlvl blueprint) "Dlvl:5") (name (:branch blueprint)) [] patches)]
                 (level-summary (@#'bothack.dungeon/apply-blueprint level blueprint)))
    :world-infer (let [[label branch tags patches method] args
                       level (world-level label branch tags patches)
                       game (-> (bothack.game/new-game)
                                (assoc :dlvl label :branch-id (keyword branch))
                                (assoc-in [:player :role] :valkyrie)
                                (bothack.dungeon/add-level level))]
                   (case method
                     "tags" (bothack.dungeon/curlvl-tags (bothack.dungeon/infer-tags game))
                     "blueprint" (level-summary (bothack.dungeon/curlvl (bothack.dungeon/level-blueprint game)))))
    :world-data {:blueprints (mapv (fn [b] (cond-> b
                                           (:features b) (update-in [:features] vec)
                                           (:monsters b) (update-in [:monsters] vec))) bothack.level/blueprints)
                 :geh-maze bothack.level/geh-maze
                 :soko-recog bothack.dungeon/soko-recog
                 :fake-wiztower-water bothack.dungeon/fake-wiztower-water
                 :wiztower-boundary bothack.level/wiztower-boundary
                 :wiztower-inner-boundary bothack.level/wiztower-inner-boundary
                 :shop-types bothack.tile/shop-types}
    :dungeon-basic (let [[method branch a b] args]
                     (case method
                       "compare" (bothack.dungeon/dlvl-compare (keyword branch) a b)
                       "next" (bothack.dungeon/next-dlvl (keyword branch) a)
                       "prev" (bothack.dungeon/prev-dlvl (keyword branch) a)
                       "number" (bothack.dungeon/dlvl-number a)
                       "new" (bothack.dungeon/new-dungeon)))
    :new-level (bothack.level/new-level (first args) (keyword (second args)))
    :default-response (let [v (ns-resolve 'bothack.delegator (symbol (first args)))
                            protocol @(:protocol (meta v))]
                        (if (satisfies? protocol @#'bh/prompt-escape)
                          {:handled true :response (apply @v @#'bh/prompt-escape
                                                          (repeat (dec (count (first (:arglists (meta v))))) nil))}
                          {:handled false}))
    :action-trigger (bothack.action/trigger (action-input (first args)))
    :discovery-lines
    (let [facts (atom []) game (atom {})]
      (with-redefs [bothack.itemid/add-discoveries (fn [g discoveries] (reset! facts discoveries) g)]
        (bothack.delegator/message-lines
          (bothack.action/handler (bothack.actions/->Discoveries) (bh/map->BotHack {:game game}))
          (first args)))
      @facts)
    :stairs-transition
    (let [[old-branch old-label new-label destination messages pet] args
          initial (-> (bothack.game/new-game)
                      (assoc :branch-id (keyword old-branch) :dlvl old-label)
                      (update-in [:player] merge {:x 40 :y 10})
                      bothack.dungeon/ensure-curlvl
                      (bothack.dungeon/update-at-player assoc :feature :stairs-down))
          initial (if destination (bothack.dungeon/update-at-player initial assoc :branch-id (keyword destination)) initial)
          initial (if pet (bothack.dungeon/reset-monster initial
                           (assoc (bothack.monster/known-monster 41 10 (bothack.montype/name->monster "little dog")) :friendly true)) initial)
          game (atom initial)
          pending (atom [])]
      (with-redefs [bothack.handlers/update-on-known-position
                    (fn [_ f & args] (swap! pending conj [f args]) nil)]
        (let [handler (bothack.actions/stairs-handler (bh/map->BotHack {:game game}))]
          (doseq [text messages] (bothack.delegator/message handler text))
          (swap! game assoc :dlvl new-label)
          (bothack.delegator/dlvl-changed handler old-label new-label)
          (swap! game #(-> % bothack.dungeon/ensure-curlvl
                          (bothack.dungeon/update-at-player assoc :feature :stairs-up)))
          (doseq [[f args] @pending] (apply swap! game f args))
          {:branch (:branch-id @game) :last-branch-no (:last-branch-no @game)
           :old-tags (get-in @game [:dungeon :levels (keyword old-branch) old-label :tags])
           :old-stairs (get-in @game [:dungeon :levels (keyword old-branch) old-label :tiles 9 40])
           :new-stairs (bothack.dungeon/at-player @game)
           :neighbor (bothack.position/at (bothack.dungeon/curlvl @game) {:x 41 :y 10})})))
    :action-handler (let [[spec input steps] args
                          game (atom (cond-> (update-in input [:player :state] #(when % (set (map keyword %))))
                                       (:tried input) (update-in [:tried] set)
                                       (get-in input [:player :inventory])
                                       (update-in [:player :inventory]
                                         #(into {} (for [[slot item] %]
                                                     [(first (name slot)) (cond-> item
                                                                           (:buc item) (update-in [:buc] keyword))])))))
                          calls (atom [])]
                      (with-redefs [bothack.actions/update-inventory (fn [& _] (swap! calls conj ["update-inventory"]) nil)
                                    bothack.actions/update-tile (fn [& _] (swap! calls conj ["update-tile"]) "deferred-tile")
                                    bothack.actions/possible-autoid (fn [_ slot] (swap! calls conj ["possible-autoid" slot]) nil)]
                        (let [handler (bothack.action/handler (action-input spec) (bh/map->BotHack {:game game}))]
                          {:results (mapv (fn [[name values]]
                                            (let [method @(ns-resolve 'bothack.delegator (symbol name))
                                                  values (if (= name "inventory-list")
                                                           [(into {} (for [[k v] (first values)] [(first (clojure.core/name k)) v]))]
                                                           values)]
                                              (apply method handler values))) steps)
                           :game @game :calls @calls :handler-map (map? handler)})))
    :delegator-response (let [[name value inhibited] args
                              value (if (and (= name "what-direction") (not= value "")) (keyword value) value)
                              calls (atom [])
                              d (assoc (bothack.delegator/new-delegator #(swap! calls conj ["write" %]))
                                       :inhibited inhibited)
                              method @(ns-resolve 'bothack.delegator (symbol name))]
                          (with-redefs [bothack.delegator/invoke-prompt (fn [& _] value)
                                        bothack.delegator/response-chosen (fn [_ _ result]
                                                                           (swap! calls conj ["response" result]))]
                            (let [arity (-> (meta (ns-resolve 'bothack.delegator (symbol name))) :arglists first count dec)]
                              (apply method d (repeat arity nil))))
                          @calls)
    :scraper-trace (let [[no-mark steps] args
                         current (ref (scraper/new-scraper nil no-mark))
                         calls (atom [])
                         prompt-name (fn [f] (some (fn [[sym v]] (when (identical? @v f) (name sym)))
                                                   (ns-publics 'bothack.delegator)))]
                     (with-redefs [clojure.core/send (fn [_ f & values]
                                                      (swap! calls conj (into [(prompt-name f)] values))
                                                      true)]
                       (mapv (fn [[kind value]]
                               (reset! calls [])
                               (dosync
                                 (if (= kind "reset")
                                   (ref-set current (scraper/new-scraper nil value))
                                   (let [frame (f/map->Frame (update-in value [:colors]
                                                              #(mapv (fn [row] (mapv (fn [c] (when c (keyword c))) row)) %)))]
                                     (alter current @#'scraper/apply-scraper nil frame))))
                               @calls) steps)))
    :scraper-call (let [[kind msg] args
                        prompt-name (fn [f] (some (fn [[sym v]] (when (identical? @v f) (name sym)))
                                                  (ns-publics 'bothack.delegator)))]
                    (case kind
                      "choice" (let [[f & values] (@#'scraper/choice-call msg)]
                                 (into [(prompt-name f)] values))
                      "menu" {:fn (prompt-name (@#'scraper/menu-fn msg))
                              :multi (boolean (@#'scraper/multi-menu? msg))
                              :merge (boolean (@#'scraper/merge-menu? msg))}
                      "prompt" (prompt-name (@#'scraper/prompt-fn msg))
                      "location" (prompt-name (@#'scraper/location-fn msg))))
    :data {:items (map #(assoc % :kind (u/typekw %)) it/items)
           :monsters m/monster-types
           :shopkeepers m/shopkeepers
           :rank-roles m/by-rank-map
           :desired-items (mapv vec mainbot/desired-items)
           :plural it/plural->singular
           :japanese it/jap->eng
           :exclusive data/exclusive-appearances
           :sokoban @#'soko/solutions
           :initial-boulders soko/initial-boulders
           :regex {:item (.pattern @#'i/item-re) :botl1 (.pattern @#'scraper/botl1-re)
                   :botl2 (.pattern @#'scraper/botl2-re)}
           :item-fields @#'i/item-fields
           :blind-identities (into {} (for [[name item] itemid/blind-appearances]
                                        [name (assoc item :kind (u/typekw item))]))}
    :position (let [[method a b] args a (p/position a) b (when b (p/position b))]
                (case method
                  "neighbors" (p/neighbors a)
                  "straight-neighbors" (p/straight-neighbors a)
                  "diagonal-neighbors" (p/diagonal-neighbors a)
                  "to-position" (p/to-position a)
                  "valid-position?" (p/valid-position? a)
                  "distance" (p/distance a b)
                  "distance-manhattan" (p/distance-manhattan a b)
                  "towards" (p/towards a b)
                  "adjacent?" (p/adjacent? a b)
                  "rectangle" (p/rectangle a b)
                  "rectangle-boundary" (p/rectangle-boundary a b)))
    :frame (let [frame (f/map->Frame (first args))]
             {:topline (f/topline frame) :topline-plus (f/topline+ frame)
              :cursor-line (f/cursor-line frame) :before-cursor (f/before-cursor frame)
              :topline-cursor (boolean (f/topline-cursor? frame))
              :engulfed (boolean (f/looks-engulfed? frame))})
    :label (i/parse-label (first args))
    :status (@#'scraper/parse-botls (first args))
    :strength (u/effective-str (first args))
    :moves (@#'soko/moves-for (first args) (second args))
    :prices (let [[base cha] args]
              (set (for [[b c price] @#'itemid/cost-data
                         :when (and (= b base) (= c (@#'itemid/cha-group cha)))] price)))
    :initial-ids (map :name (itemid/initial-ids (first args)))
    :ambiguous-names itemid/item-names
    :identified (identified (first args) (second args))
    :food (let [[p label] args p (player-input p) food (i/label->item label)]
            {:edible (boolean (player/edible? p food))
             :want (try (boolean (player/want-to-eat? p food))
                        (catch NumberFormatException _ "number-format-error"))})
    :monster-description (m/by-description (first args))
    :new-monster (let [[x y turn glyph color] args]
                   (monster/new-monster x y turn (first glyph) (when color (keyword color))))
    :hp (let [p (first args)] {:low (boolean (@#'mainbot/low-hp? p)) :safe (boolean (@#'mainbot/safe-hp? p))})
    :utility (let [[label with-game] args item (i/label->item label)]
               (if with-game
                 (mainbot/utility {:discoveries (itemid/new-discoveries)} item)
                 (mainbot/utility item)))
    :choose-food (let [[p entries] args
                       game {:player (assoc (player-input p) :inventory (inventory-input entries))
                             :discoveries (itemid/new-discoveries)}]
                   (when-let [[slot item] (@#'mainbot/choose-food game)] [(str slot) (:label item)]))
    :carried (let [[p entries] args
                   game {:player (assoc (player-input p) :inventory (inventory-input entries))
                         :discoveries (itemid/new-discoveries)}]
               {:nutrition (player/nutrition-sum game)
                :weight (player/weight-sum game)
                :capacity (player/capacity (:player game))})
    :fov (let [[pos grid] args]
           (mapv vec (.calculateFov (bothack.NHFov.) (:x pos) (dec (:y pos))
                      (reify bothack.NHFov$TransparencyInfo
                        (isTransparent [_ x y]
                          (boolean (and (< 0 x 79) (< 0 y 20) (get-in grid [y x]))))))))
    :tile (let [[t glyph color] args]
            (tile/parse-tile (tile-input t) (first glyph) (when color (keyword color))))
    :base-cost (let [[level direction t opts] args]
                 (pathing/base-cost (update-in level [:tags] #(set (map keyword %))) (keyword direction) (tile-input t) opts))
    :path (let [[algo start target costs limit] args
                start (p/position start) target (p/position target)
                costs (into {} (for [[x y cost] costs] [(p/position x y) cost]))
                move (fn [_ dest] (if-let [cost (costs dest)] [cost :move]))]
            (if (= algo "astar")
              (@#'pathing/a* start target move limit)
              (@#'pathing/dijkstra start #(= target %) move limit)))
    :terminal-reset (do (reset-terminal) true)
    :terminal-feed (let [out System/out]
                     (try
                       (System/setOut (java.io.PrintStream. (java.io.ByteArrayOutputStream.)))
                       (.putString @terminal (first args))
                       (@#'term/frame-from-buffer @terminal)
                       (finally (System/setOut out))))
    (throw (IllegalArgumentException. (str "Unknown oracle operation " op)))))

(doseq [line (line-seq (java.io.BufferedReader. *in*))]
  (try
    (println (str "@@BOTHACK@@" (pr-str {"ok" (plain (dispatch (edn/read-string line)))})))
    (catch Throwable e
      (println (str "@@BOTHACK@@" (pr-str {"error" (str (.getName (class e)) ": " (.getMessage e))}))))))
(shutdown-agents)
