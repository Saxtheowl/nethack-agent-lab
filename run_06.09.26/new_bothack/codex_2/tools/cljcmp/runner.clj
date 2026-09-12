(ns cljcmp.runner
  "Runs the original BotHack with a deterministic RNG (shared with the Python
  port) and logs every chosen action, so both bots can be compared on the same
  recorded game.  BotHack itself is not modified."
  (:require [clojure.string :as string]
            [cljcmp.handlers-det :as handlers-det]
            [cljcmp.dbg-inv :as dbg-inv]
            [cljcmp.det-cache :as det-cache]
            [bothack.main]
            [bothack.util :refer [typekw]])
  (:gen-class))

;; The draw and its sequence number must come out of ONE atomic transition.
;; With two atoms (state, then counter) the bot's `future` thread and the main
;; thread can interleave between them, so the logged order - and the numbers -
;; would not be evidence of the real order of the draws.  Here every draw
;; carries the index it was actually assigned, so sorting the trace by index
;; recovers the true sequence no matter when the line was written.
(def ^:private lcg (atom [12345 0]))

(defn- lcg-next
  "Returns [value index] for one draw, atomically."
  []
  (let [[s n] (swap! lcg (fn [[s _n]]
                           [(mod (+ (* 1103515245 s) 12345) 2147483648)
                            (inc _n)]))]
    [(bit-shift-right s 16) n]))

(def ^:private trace-file (System/getenv "BOTHACK_RNG_TRACE"))

(defn- trace! [idx v kind n]
  (when trace-file
    (spit trace-file
          (format "%6d  %6d  %s %s  thread=%s%n"
                  idx v kind n (.getName (Thread/currentThread)))
          :append true)))

(defn install-lcg! [seed]
  (reset! lcg [seed 0])
  (alter-var-root #'clojure.core/rand-int
                  (constantly (fn [n] (let [[v idx] (lcg-next)]
                                        (trace! idx v "rand-int" n)
                                        (mod v n)))))
  (alter-var-root #'clojure.core/rand-nth
                  (constantly (fn [coll]
                                (let [[v idx] (lcg-next)
                                      c (vec coll)]
                                  (trace! idx v "rand-nth" (count c))
                                  (nth c (mod v (count c))))))))

(defn -main [& args]
  (when-not (= "0" (System/getenv "BOTHACK_PIN_HANDLERS"))
    (handlers-det/install!))
  ;; BOTHACK_DET_CACHE=0 keeps BotHack's racing future (non-reproducible)
  (when-not (= "0" (System/getenv "BOTHACK_DET_CACHE"))
    (det-cache/install!))
  (dbg-inv/install!)
  (install-lcg! (Long/parseLong (or (System/getenv "BOTHACK_SEED") "12345")))
  (apply bothack.main/-main args))
