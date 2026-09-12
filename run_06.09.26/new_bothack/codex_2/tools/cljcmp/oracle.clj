(ns cljcmp.oracle
  "A differential-testing oracle: reads test cases as JSON-ish lines on stdin
  and prints the original BotHack's answers, so the Python port can be checked
  against the real implementation function by function."
  (:require [clojure.string :as string]
            [bothack.item :as item]
            [bothack.itemid :as itemid]
            [bothack.itemtype :as itemtype]
            [bothack.montype :as montype]
            [bothack.monster :as monster]
            [bothack.behaviors]
            [bothack.bots.mainbot]
            [bothack.player]
            [bothack.tile :as tile]
            [bothack.level]
            [bothack.pathing]
            [bothack.position]
            [bothack.fov]
            [bothack.dungeon :as dungeon]
            [bothack.position :as pos]
            [bothack.util :as util]
            [bothack.game :as game]
            [bothack.scraper :as scraper]
            [bothack.frame :as frame])
  (:import [bothack NHFov NHFov$TransparencyInfo])
  (:gen-class))

(declare jsn)

(defn- esc [s]
  (str \" (-> (str s)
              (string/replace "\\" "\\\\")
              (string/replace "\"" "\\\"")
              (string/replace "\n" "\\n")
              (string/replace "\t" "\\t")
              (string/replace "\r" "\\r"))
       \"))

(defn jsn [x]
  (cond
    (nil? x) "null"
    (true? x) "true"
    (false? x) "false"
    (keyword? x) (esc (name x))
    (char? x) (esc (str x))
    (string? x) (esc x)
    (ratio? x) (format "%.10e" (double x))
    (float? x) (format "%.10e" (double x))
    (number? x) (str x)
    (set? x) (str "[" (string/join "," (map jsn (sort-by str x))) "]")
    (map? x) (str "{" (string/join "," (for [[k v] (sort-by (comp str key) x)]
                                         (str (esc (if (keyword? k) (name k) k))
                                              ":" (jsn v)))) "}")
    (sequential? x) (str "[" (string/join "," (map jsn x)) "]")
    :else (esc (str x))))

(defn- answer [line]
  (let [[op arg] (string/split line #"\t" 2)]
    (case op
      "parse-label" (jsn (item/parse-label arg))
      "parse-botls" (let [[a b] (string/split arg #"\|" 2)]
                      (jsn ((deref (ns-resolve 'bothack.scraper 'parse-botls)) [a b])))
      "by-description" (jsn (:name (montype/by-description arg)))
      "item-type" (jsn (itemid/item-type (item/label->item arg)))
      "item-id" (jsn (itemid/item-id (item/label->item arg)))
      "initial-ids" (jsn (map :name (itemid/initial-ids
                                      (item/label->item arg))))
      "appearance-of" (jsn (itemid/appearance-of (item/label->item arg)))
      "knowable" (jsn (itemid/knowable-appearance? arg))
      "room-type" (jsn (dungeon/room-type arg))
      "food"
      ;; "<race>|<intrinsics>|<str>|<corpse label>;..."
      (let [[race intr strength labels] (string/split arg #"\|" 4)
            player {:race (keyword race)
                    :intrinsics (set (map keyword
                                          (remove empty?
                                                  (string/split intr #","))))
                    :stats {:str* strength}}]
        (jsn (vec (for [l (remove empty? (string/split labels #";"))
                        :let [i (item/label->item l)]]
                    {:label l
                     :edible (boolean (bothack.player/edible? player i))
                     :want (try (boolean (bothack.player/want-to-eat? player i))
                                (catch Exception e (str "ERR")))
                     :safe-type (boolean
                                  (when-let [t (itemtype/name->item (:name i))]
                                    (when (:monster t)
                                      (bothack.player/safe-corpse-type?
                                        player i t))))}))))
      "combat"
      ;; "<px>,<py>|<hp>/<maxhp>/<ac>|<x,y,name;...>|<slot:label;...>|<rows>"
      (let [[pos hpspec mons invspec rows] (string/split arg #"\|" 5)
            [px py] (map #(Integer/parseInt %) (string/split pos #","))
            [hp maxhp ac] (map #(Integer/parseInt %)
                               (string/split hpspec #"/"))
            colours {\n nil \r :red \g :green \b :brown \B :blue
                     \m :magenta \c :cyan \G :gray \w :white \y :yellow
                     \o :orange \e :bright-green \u :bright-blue
                     \p :bright-magenta \C :bright-cyan \d :bold}
            grid (vec (string/split rows #";"))
            glyphs (vec (for [row grid] (vec (take-nth 2 row))))
            cols (vec (for [row grid]
                        (vec (map colours (take-nth 2 (rest row))))))
            level (-> (bothack.level/new-level "Dlvl:3" :main)
                      (update-in [:tiles]
                                 #(dungeon/map-tiles tile/parse-tile % glyphs
                                                     cols)))
            level (reduce (fn [lvl spec]
                            (let [[x y nm] (string/split spec #",")
                                  t (montype/name->monster nm)
                                  m (assoc (bothack.monster/new-monster
                                             (Integer/parseInt x)
                                             (Integer/parseInt y)
                                             500 (:glyph t) (:color t))
                                           :type t :awake true
                                           :first-known 495)]
                              (dungeon/reset-monster lvl m)))
                          level
                          (remove empty? (string/split mons #";")))
            game (-> (#'bothack.game/new-game)
                     (assoc :dlvl "Dlvl:3" :branch-id :main :turn 500
                            :turn* 500 :score 1000 :wishes 0)
                     (assoc-in [:player :x] px)
                     (assoc-in [:player :y] py)
                     (assoc-in [:player :hp] hp)
                     (assoc-in [:player :maxhp] maxhp)
                     (assoc-in [:player :ac] ac)
                     (assoc-in [:player :xplvl] 5)
                     (assoc-in [:player :protection] 0)
                     (assoc-in [:player :role] :valkyrie)
                     (assoc-in [:player :race] :dwarf)
                     (assoc-in [:player :alignment] :lawful)
                     (assoc-in [:player :intrinsics] #{:cold :stealth})
                     (assoc-in [:player :state] #{})
                     (assoc-in [:player :stats] {:str 18 :con 18 :cha 8
                                                 :dex 10 :int 10 :wis 10
                                                 :str* "18"})
                     (assoc-in [:player :inventory]
                               (into {}
                                     (for [e (remove empty?
                                                     (string/split invspec
                                                                   #";"))
                                           :let [[sl lbl] (string/split e #":"
                                                                       2)]]
                                       [(first sl) (item/label->item lbl)])))
                     (dungeon/add-level level))
            mb (fn [n] (deref (ns-resolve 'bothack.bots.mainbot (symbol n))))
            ;; reasons embed printed records/tiles, so keep only the text
            ;; before the first "{" so both sides are comparable
            ;; drop printed records/keywords/chars so both sides compare
            clean (fn [r] (-> (first (string/split r #"[{#]" 2))
                              (string/replace #":" "")
                              (string/replace "\\" "")
                              string/trim))
            act (fn [a] (when a
                          (cond-> {:type (name (util/typekw a))
                                   :dir (some-> (:dir a) name)
                                   :reason (vec (map clean (:reason a)))}
                            (:pos a) (assoc :pos [(:x (:pos a))
                                                  (:y (:pos a))]))))]
        (jsn {:threats (vec (sort (for [m ((mb "hostile-threats") game)]
                                    [(:x m) (:y m)])))
              ;; the order (vals (:monsters level)) yields - it decides which
              ;; monster examine-monsters picks
              :monster-order (vec (for [m (dungeon/curlvl-monsters game)]
                                    [(:x m) (:y m)]))
              :fight (act ((mb "fight") game))
              :retreat (act ((mb "retreat") game))
              :feed (act ((mb "feed") game))
              :progress (act ((mb "progress") game))
              :low-hp (boolean ((mb "low-hp?") (:player game)))
              :exposed (boolean ((mb "exposed?") game level
                                 (:player game)))
              :reequip (act ((mb "reequip") game))
              :reequip-weapon (act ((mb "reequip-weapon") game))
              :use-items (act ((mb "use-items") game))
              :itemid (act ((mb "itemid") game))
              :use-features (act ((mb "use-features") game))
              :consider-items (act ((mb "consider-items") game))
              :consider-items-here (act ((mb "consider-items-here") game))
              :examine-containers (act ((mb "examine-containers") game))
              :examine-containers-here (act ((mb "examine-containers-here")
                                             game))
              :handle-illness (act ((mb "handle-illness") game))
              :handle-starvation (act ((mb "handle-starvation") game))
              :handle-impairment (act ((mb "handle-impairment") game))
              :recover (act ((mb "recover") game true))
              :rob-peacefuls (act ((mb "rob-peacefuls") game))
              :get-protection (act ((mb "get-protection") game))
              :bag-items (act ((mb "bag-items") game))
              :shop (act ((mb "shop") game))
              :fight-covetous (act ((mb "fight-covetous") game))
              :cursed-levi (act ((mb "cursed-levi") game))
              :drop-junk (act ((mb "drop-junk") game))
              :wear-armor (act ((mb "wear-armor") game))
              :wield-weapon (act ((mb "wield-weapon") game))
              :bless-gear (act ((mb "bless-gear") game))
              :use-light (act ((mb "use-light") game level))
              :remove-rings (act ((mb "remove-rings") game))
              :enchant-gear (act ((mb "enchant-gear") game))
              :make-excal (act ((mb "make-excal") game))
              :handle-drowning (act ((mb "handle-drowning") game))
              :offer-amulet (act ((mb "offer-amulet") game))
              :wander (act ((mb "wander") game))
              ;; the farlook/examine chain lives in actions.clj and is private
              :examine-tile (act (@(ns-resolve 'bothack.actions
                                               'examine-tile) game))
              :examine-monsters (act (@(ns-resolve 'bothack.actions
                                                   'examine-monsters) game))
              :examine-features (act (@(ns-resolve 'bothack.actions
                                                   'examine-features) game))}))
      "excal"
      ;; "<px>,<py>|<ac>|<slot:label;...>|<oracle mode>|<rows>"
      ;; oracle mode: none | seen | seen-fountain
      (let [[pos acs invspec omode rows] (string/split arg #"\|" 5)
            [px py] (map #(Integer/parseInt %) (string/split pos #","))
            ac (Integer/parseInt acs)
            colours {\n nil \r :red \g :green \b :brown \B :blue
                     \m :magenta \c :cyan \G :gray \w :white \y :yellow
                     \o :orange \e :bright-green \u :bright-blue
                     \p :bright-magenta \C :bright-cyan \d :bold}
            grid (vec (string/split rows #";"))
            glyphs (vec (for [row grid] (vec (take-nth 2 row))))
            cols (vec (for [row grid]
                        (vec (map colours (take-nth 2 (rest row))))))
            level (-> (bothack.level/new-level "Dlvl:5" :main)
                      (update-in [:tiles]
                                 #(dungeon/map-tiles tile/parse-tile % glyphs
                                                     cols)))
            opos bothack.level/oracle-position
            oracle (when (not= "none" omode)
                     (let [l (-> (bothack.level/new-level "Dlvl:3" :main)
                                 (assoc :tags #{:oracle}))
                           l (reduce (fn [l p]
                                       (assoc-in l [:tiles (dec (:y p))
                                                    (:x p) :seen] true))
                                     l (pos/neighbors opos))]
                       (if (= "seen-fountain" omode)
                         (assoc-in l [:tiles (dec (:y opos)) (inc (:x opos))
                                      :feature] :fountain)
                         l)))
            game (-> (#'bothack.game/new-game)
                     (assoc :dlvl "Dlvl:5" :branch-id :main :turn 500
                            :turn* 500 :score 1000 :wishes 0)
                     (assoc-in [:player :x] px)
                     (assoc-in [:player :y] py)
                     (assoc-in [:player :hp] 40)
                     (assoc-in [:player :maxhp] 40)
                     (assoc-in [:player :ac] ac)
                     (assoc-in [:player :xplvl] 5)
                     (assoc-in [:player :protection] 0)
                     (assoc-in [:player :role] :valkyrie)
                     (assoc-in [:player :race] :dwarf)
                     (assoc-in [:player :alignment] :lawful)
                     (assoc-in [:player :intrinsics] #{:cold :stealth})
                     (assoc-in [:player :state] #{})
                     (assoc-in [:player :stats] {:str 18 :con 18 :cha 8
                                                 :dex 10 :int 10 :wis 10
                                                 :str* "18"})
                     (assoc-in [:player :inventory]
                               (into {}
                                     (for [e (remove empty?
                                                     (string/split invspec
                                                                   #";"))
                                           :let [[sl lbl] (string/split e #":"
                                                                       2)]]
                                       [(first sl) (item/label->item lbl)])))
                     (dungeon/add-level level))
            game (if oracle (dungeon/add-level game oracle) game)
            ;; a fountain on a level *above* the Oracle: seek-fountain's last
            ;; resort, which must not be reached while we stand on a fountain
            prev-lvl (when (= "seen-prev-fountain" omode)
                       (-> (bothack.level/new-level "Dlvl:2" :main)
                           (assoc-in [:tiles 5 20 :feature] :fountain)))
            game (if prev-lvl (dungeon/add-level game prev-lvl) game)
            mb (fn [n] (deref (ns-resolve 'bothack.bots.mainbot (symbol n))))
            clean (fn [r] (-> (first (string/split r #"[{#]" 2))
                              (string/replace #":" "")
                              (string/replace "\\" "")
                              string/trim))
            act (fn [a] (when a
                          (cond-> {:type (name (util/typekw a))
                                   :dir (some-> (:dir a) name)
                                   :reason (vec (map clean (:reason a)))}
                            (:pos a) (assoc :pos [(:x (:pos a))
                                                  (:y (:pos a))]))))]
        (jsn {:make-excal (act ((mb "make-excal") game))
              :seek-fountain (act ((mb "seek-fountain") game))}))
      "invorder"
      ;; "<slot>:<label>;..." -> the order (:inventory player) iterates in and
      ;; the slot choose-food picks.  choose-food is (min-by nw-ratio ...) and
      ;; min-key keeps the *last* extreme, so with two equal-ratio food stacks
      ;; the answer is decided purely by that order.
      (let [inv (into {} (for [e (remove empty? (string/split arg #";"))
                               :let [[sl lbl] (string/split e #":" 2)]]
                           (item/slot-item (first sl) lbl)))
            game (-> (#'bothack.game/new-game)
                     (assoc :dlvl "Dlvl:3" :branch-id :main :turn 500)
                     (assoc-in [:player :hp] 40)
                     (assoc-in [:player :maxhp] 40)
                     (assoc-in [:player :xplvl] 5)
                     (assoc-in [:player :role] :valkyrie)
                     (assoc-in [:player :race] :dwarf)
                     (assoc-in [:player :alignment] :lawful)
                     (assoc-in [:player :intrinsics] #{})
                     (assoc-in [:player :state] #{})
                     (assoc-in [:player :stats] {:str 18 :con 18 :cha 8
                                                 :dex 10 :int 10 :wis 10
                                                 :str* "18"})
                     (assoc-in [:player :inventory] inv))
            cf (@(ns-resolve 'bothack.bots.mainbot 'choose-food) game)]
        (jsn {:order (vec (map str (keys inv)))
              :choose-food (some-> cf first str)}))
      "maporder"
      ;; "into|a,b,c" vs "assoc|a,b,c" -> (vec (keys m)).
      ;; `into` builds through a *transient* array map, which appends, while a
      ;; chain of persistent `assoc` calls prepends - so the two give opposite
      ;; iteration orders for the same insertion sequence.  The bot builds
      ;; (:monsters level) with `into` in gather-monsters and mutates it with
      ;; `assoc` in reset-monster, so the port has to model both.
      (let [[how spec] (string/split arg #"\|" 2)
            chars? (.endsWith ^String how "-char")
            how (string/replace how #"-char$" "")
            mk (fn [k] (if chars?
                         (first k)
                         (if (.contains ^String k ":")
                           (let [[x y] (map #(Integer/parseInt %)
                                            (string/split k #":"))]
                             (bothack.position/position x y))
                           k)))
            ks (map mk (remove empty? (string/split spec #",")))
            m (if (= "into" how)
                (into {} (map (fn [k] [k 1]) ks))
                (reduce (fn [acc k] (assoc acc k 1)) {} ks))
            out (fn [k] (cond (map? k) [(:x k) (:y k)]
                              (char? k) (str k)
                              :else k))]
        (jsn (vec (map out (keys m)))))
      "menuorder"
      ;; "abc" -> (string/join (set chars)); "1a,2b,.." -> a set of Strings
      ;; (that is what take-out-what returns).  The set's iteration order is
      ;; the order the bot presses the menu keys in.
      (jsn (string/join (set (if (.contains ^String arg ",")
                               (remove empty? (string/split arg #","))
                               (seq arg)))))
      "poshash"
      ;; hash of every possible Position - the port needs Clojure's hash order
      ;; to break priority-map ties in the pathfinder exactly like the original
      (jsn (vec (for [y (range 1 22) x (range 0 80)]
                  (hash (bothack.position/position x y)))))
      "setorder"
      ;; "x,y;x,y;..." -> the order (seq (set positions)) yields them
      (let [ps (for [e (remove empty? (string/split arg #";"))
                     :let [[x y] (map #(Integer/parseInt %)
                                      (string/split e #","))]]
                 (bothack.position/position x y))]
        (jsn (vec (for [p (seq (set ps))] [(:x p) (:y p)]))))
      "inventory-logic"
      ;; "<slot>:<label>;...||<candidate label>;..."
      (let [[invspec cands] (string/split arg #"\|\|" 2)
            inv (into {} (for [e (remove empty? (string/split invspec #";"))
                               :let [[sl lbl] (string/split e #":" 2)]]
                           [(first sl) (item/label->item lbl)]))
            level (bothack.level/new-level "Dlvl:1" :main)
            game (-> (#'bothack.game/new-game)
                     (assoc :dlvl "Dlvl:1" :branch-id :main :turn 100
                            :turn* 100 :score 1234 :wishes 0)
                     (assoc-in [:player :x] 40)
                     (assoc-in [:player :y] 10)
                     (assoc-in [:player :hp] 20)
                     (assoc-in [:player :maxhp] 20)
                     (assoc-in [:player :ac] 6)
                     (assoc-in [:player :xplvl] 3)
                     (assoc-in [:player :protection] 0)
                     (assoc-in [:player :role] :valkyrie)
                     (assoc-in [:player :race] :dwarf)
                     (assoc-in [:player :alignment] :lawful)
                     (assoc-in [:player :intrinsics] #{:cold :stealth})
                     (assoc-in [:player :stats] {:str 18 :con 18 :cha 8
                                                 :dex 10 :int 10 :wis 10
                                                 :str* "18"})
                     (assoc-in [:player :inventory] inv)
                     (dungeon/add-level level))
            mb (fn [n] (deref (ns-resolve 'bothack.bots.mainbot (symbol n))))
            take? ((mb "take-selector") game)
            drop-junk ((mb "drop-junk") game)]
        (jsn {:desired (vec (sort ((mb "currently-desired") game)))
              :drop-junk (some-> drop-junk util/typekw name)
              :nutrition (bothack.player/nutrition-sum game)
              :weight (bothack.player/weight-sum game)
              :candidates
              (vec (for [c (remove empty? (string/split cands #";"))
                         :let [i (item/label->item c)]]
                     {:label c
                      :worthwhile (boolean ((mb "worthwhile?") game i))
                      :should-try (boolean ((mb "should-try?") game i))
                      :take (boolean (take? i))
                      :utility ((mb "utility") game i)}))})) 
      "nav"
      ;; "<px>,<py>|<opts>|<goalspec>|<rows>"  - rows are 2 chars per cell
      ;; (glyph + colour letter), 21 rows separated by ";"
      (let [[pos optstr goalspec rows] (string/split arg #"\|" 4)
            [px py] (map #(Integer/parseInt %) (string/split pos #","))
            colours {\n nil \r :red \g :green \b :brown \B :blue
                     \m :magenta \c :cyan \G :gray \w :white \y :yellow
                     \o :orange \e :bright-green \u :bright-blue
                     \p :bright-magenta \C :bright-cyan \d :bold}
            grid (vec (string/split rows #";"))
            glyphs (vec (for [row grid] (vec (take-nth 2 row))))
            cols (vec (for [row grid]
                        (vec (map colours (take-nth 2 (rest row))))))
            level (-> (bothack.level/new-level "Dlvl:1" :main)
                      (update-in [:tiles]
                                 #(dungeon/map-tiles tile/parse-tile % glyphs
                                                     cols)))
            game (-> (#'bothack.game/new-game)
                     (assoc :dlvl "Dlvl:1" :branch-id :main :turn 100
                            :turn* 100)
                     (assoc-in [:player :x] px)
                     (assoc-in [:player :y] py)
                     (assoc-in [:player :hp] 20)
                     (assoc-in [:player :maxhp] 20)
                     (assoc-in [:player :ac] 6)
                     (assoc-in [:player :xplvl] 1)
                     (assoc-in [:player :stats] {:str 18 :con 18 :cha 8
                                                 :dex 10 :int 10 :wis 10
                                                 :str* "18"})
                     (assoc-in [:player :intrinsics] #{})
                     (assoc-in [:player :inventory] {})
                     (dungeon/add-level level))
            opts (set (map keyword (remove empty?
                                           (string/split optstr #","))))
            goal (case goalspec
                   "explorable" #((deref (ns-resolve 'bothack.pathing 'explorable-tile?)) level %)
                   "stairs-down" #(tile/has-feature? % :stairs-down)
                   "stairs-up" #(tile/has-feature? % :stairs-up)
                   "door" tile/door?
                   "items" :new-items
                   "unwalked" #(and (tile/walkable? %) (not (:walked %)))
                   (let [[gx gy] (map #(Integer/parseInt %)
                                      (string/split goalspec #","))]
                     (bothack.position/position gx gy)))
            path (bothack.pathing/navigate game goal opts)]
        (jsn (if path
               {:found true
                :len (count (:path path))
                :target (when (:target path)
                          [(:x (:target path)) (:y (:target path))])
                :step (when (:step path) (name (util/typekw (:step path))))
                :dir (when (:step path) (some-> (:dir (:step path)) name))
                :first (when (seq (:path path))
                         [(:x (first (:path path)))
                          (:y (first (:path path)))])}
               {:found false})))
      "fov"
      (let [[pos rows] (string/split arg #"\|" 2)
            [px py] (map #(Integer/parseInt %) (string/split pos #","))
            grid (vec (string/split rows #";"))
            transparent? (fn [x y]
                           (and (< 0 y 20) (< 0 x 79)
                                (= \. (get (get grid y "") x \#))))
            fov (.calculateFov (bothack.NHFov.) (int px) (int py)
                               (reify bothack.NHFov$TransparencyInfo
                                 (isTransparent [_ x y]
                                   (boolean (transparent? x y)))))]
        (jsn (vec (for [row fov]
                    (apply str (map #(if % \1 \0) row))))))
      "infer-feature"
      (let [[cur g c] (string/split arg #"," 3)
            tile (assoc (tile/initial-tile 5 5)
                        :feature (if (= "nil" cur) nil (keyword cur)))
            nt (tile/parse-tile tile (first g) (if (= "nil" c) nil (keyword c)))]
        (jsn {:feature (:feature nt) :glyph (str (:glyph nt))
              :color (:color nt) :new-items (boolean (:new-items nt))
              :item-glyph (str (:item-glyph nt))
              :walkable (boolean (tile/walkable? nt))
              :transparent (boolean (tile/transparent? nt))
              :monster (boolean (tile/monster? nt))
              :item (boolean (tile/item? nt))
              :boulder (boolean (tile/boulder? nt))
              :door (boolean (tile/door? nt))
              :trap (boolean (tile/trap? nt))
              :diggable (boolean (tile/diggable? nt))
              :seen (boolean (:seen nt))
              :dug (boolean (:dug nt))}))
      "item-preds"
      (let [i (item/label->item arg)]
        (jsn (into (sorted-map)
                   {"charged" (boolean (item/charged? i))
                    "recharged" (boolean (item/recharged? i))
                    "safe-enchant" (boolean (item/safe-enchant? i))
                    "two-handed" (boolean (item/two-handed? i))
                    "artifact" (boolean (item/artifact? i))
                    "price-id" (boolean (item/price-id? i))
                    "container" (boolean (item/container? i))
                    "know-contents" (boolean (item/know-contents? i))
                    "boh" (boolean (item/boh? i))
                    "tin" (boolean (item/tin? i))
                    "corpse" (boolean (item/corpse? i))
                    "can-take" (boolean (item/can-take? i))
                    "candle" (boolean (item/candle? i))
                    "dagger" (boolean (item/dagger? i))
                    "ammo" (boolean (item/ammo? i))
                    "dart" (boolean (item/dart? i))
                    "rocks" (boolean (item/rocks? i))
                    "egg" (boolean (item/egg? i))
                    "gold" (boolean (item/gold? i))
                    "key" (boolean (item/key? i))
                    "shield" (boolean (item/shield? i))
                    "gloves" (boolean (item/gloves? i))
                    "boots" (boolean (item/boots? i))
                    "wished" (boolean (item/wished? i))
                    "explorable-container" (boolean
                                             (item/explorable-container? i))
                    "single" (boolean (item/single? i))
                    "safe-buc" (boolean (item/safe-buc? i))
                    "noncursed" (boolean (item/noncursed? i))
                    "subtype" (itemid/item-subtype i)
                    "weight" (itemid/item-weight i)
                    "nw-ratio" (double (item/nw-ratio i))
                    "enchantment" (item/enchantment i)
                    "utility" ((resolve 'bothack.bots.mainbot/utility) i)})))
      "monster-preds-desc"
      ;; Same predicates, but the monster's :type comes from by-description
      ;; rather than name->monster - so for a player rank ("vagrant") the :type
      ;; is a plain String, which is what FarLook actually stores.  The
      ;; name->monster path can never produce that, so it never exercised it.
      (let [t (montype/by-description arg)
            m {:type t :glyph (:glyph t) :color (:color t)}]
        (jsn (into (sorted-map)
                   {"type-is-string" (string? t)
                    "typename" (str (monster/typename m))
                    "passive" (boolean (monster/passive? m))
                    "corrosive" (boolean (monster/corrosive? m))
                    "flies" (boolean (monster/flies? m))
                    "slow" (boolean (monster/slow? m))
                    "mindless" (boolean (monster/mindless? m))
                    "demon-lord" (boolean (monster/demon-lord? m))
                    "drowner" (boolean (monster/drowner? m))
                    "werecreature" (boolean (monster/werecreature? m))
                    "sees-invisible" (boolean (monster/sees-invisible? m))
                    "follower" (boolean (monster/follower? m))
                    "amphibious" (boolean (monster/amphibious? m))
                    "unique" (boolean (monster/unique? m))
                    "ignores-e" (boolean (monster/ignores-e? m))
                    "shopkeeper" (boolean (monster/shopkeeper? m))}))) 
      "monster-preds"
      (let [t (montype/name->monster arg)
            m {:type t :glyph (:glyph t) :color (:color t)}]
        (jsn (into (sorted-map)
                   {"passive" (boolean (monster/passive? m))
                    "corrosive" (boolean (monster/corrosive? m))
                    "covetous" (boolean (monster/covetous? m))
                    "steals" (boolean (monster/steals? m))
                    "ignores-e" (boolean (monster/ignores-e? m))
                    "flies" (boolean (monster/flies? m))
                    "drowner" (boolean (monster/drowner? m))
                    "slow" (boolean (monster/slow? m))
                    "unique" (boolean (monster/unique? m))
                    "werecreature" (boolean (monster/werecreature? m))
                    "sees-invisible" (boolean (monster/sees-invisible? m))
                    "follower" (boolean (monster/follower? m))
                    "amphibious" (boolean (monster/amphibious? m))
                    "nasty" (boolean (monster/nasty? m))
                    "rider" (boolean (monster/rider? m))
                    "mindless" (boolean (monster/mindless? m))
                    "sessile" (boolean (monster/sessile? m))
                    "strong" (boolean (monster/strong? m))
                    "human" (boolean (monster/human? m))
                    "guard" (boolean (monster/guard? m))
                    "undead" (boolean (monster/undead? m))
                    "infravisible" (boolean (monster/infravisible? m))
                    "priest" (boolean (monster/priest? m))
                    "mimic" (boolean (monster/mimic? m))
                    "unicorn" (boolean (monster/unicorn? m))
                    "pudding" (boolean (monster/pudding? m))
                    "shopkeeper" (boolean (monster/shopkeeper? m))
                    "demon-lord" (boolean (monster/demon-lord? m))
                    "hostile" (boolean (monster/hostile? m))})))
      "trap-name" (jsn (get tile/trap-names arg))
      "effective-str" (jsn (util/effective-str arg))
      (str "ERR unknown op " op))))

(defn -main [& _]
  (doseq [line (line-seq (java.io.BufferedReader. *in*))]
    (when (seq line)
      (println (try (answer line)
                    (catch Exception e
                      (str "ERR " (type e) " " (.getMessage e) " @ "
                           (string/join " <- "
                                        (take 8 (map str (.getStackTrace e)))))))))
    (flush)))
