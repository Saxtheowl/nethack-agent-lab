#!/bin/bash
# Super NetHack Wish Server - Interactive Menu
# This script is the ForceCommand for SSH connections.

export TERM="${TERM:-xterm-256color}"
DATA_DIR="/data/sessions"
SAVE_DIR="/data/saves"
BACKUP_DIR="/data/save_backups"
CLAIM_DIR="/data/claimed_wishes"
NETHACK="/usr/local/bin/nethack"
ENABLED_FLAG="/data/bots_enabled"
LOG="/data/menu_debug.log"
WISH_UTILS="/opt/nethack/bot/wish_utils.py"
ROLES=(
    Archeologist Barbarian Caveman Healer Knight Monk Priest Ranger Rogue
    Samurai Tourist Valkyrie Wizard
)

log() { echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

backup_save_for_player() {
    local player_name="$1"
    local reason="$2"
    [ -n "$player_name" ] || return 0

    mkdir -p "$BACKUP_DIR"
    local ts
    ts=$(date '+%Y%m%dT%H%M%S')
    local f base save_name dst
    for f in "$SAVE_DIR"/*.gz; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        save_name=$(echo "$base" | sed 's/^[0-9]*//' | sed 's/\.gz$//')
        [ "$save_name" = "$player_name" ] || continue
        dst="$BACKUP_DIR/${ts}_${reason}_${base}"
        cp -p "$f" "$dst"
        log "backup: $reason player='$player_name' src='$f' dst='$dst'"
    done
}

get_wish_count() {
    python3 "$WISH_UTILS" list-ready "$DATA_DIR" | wc -l
}

get_role_wish_count() {
    local role="$1"
    python3 "$WISH_UTILS" list-ready "$DATA_DIR" "$role" | wc -l
}

get_bot_status() {
    if [ -f "$ENABLED_FLAG" ]; then echo "ON"; else echo "OFF"; fi
}

load_claimed_wish_info() {
    local char_name="$1"
    [ -n "$char_name" ] || return 1

    python3 "$WISH_UTILS" claim-info "$CLAIM_DIR" "$char_name"
}

ensure_claimed_wish() {
    local session_name="$1"
    local char_name="$2"
    local role="$3"
    local hackdir="$4"

    mkdir -p "$CLAIM_DIR"
    python3 "$WISH_UTILS" ensure-claim "$CLAIM_DIR" "$session_name" "$char_name" "$role" "$hackdir"
}

update_claimed_wish_stats() {
    local char_name="$1"
    local dlvl="$2"
    local exp="$3"
    local turns="$4"

    [ -n "$char_name" ] || return 0
    python3 "$WISH_UTILS" update-stats "$CLAIM_DIR" "$char_name" "$dlvl" "$exp" "$turns" 2>/dev/null || true
}

is_wish_role() {
    local role="$1"
    local known
    for known in "${ROLES[@]}"; do
        [ "$known" = "$role" ] && return 0
    done
    return 1
}

launch_nethack_session() {
    local session_name="$1"
    local player_name="$2"
    local role="$3"
    local saved_hackdir="$4"

    local hackdir=""
    if [ -n "$saved_hackdir" ] && [ -d "$saved_hackdir" ]; then
        hackdir="$saved_hackdir"
    elif is_wish_role "$role" && [ -d "/data/hackdirs/$role" ]; then
        hackdir="/data/hackdirs/$role"
    fi

    if [ -n "$hackdir" ]; then
        log "play: launching tmux new-session $session_name (role=$role hackdir=$hackdir nethack -u $player_name)"
        tmux new-session -s "$session_name" -x 80 -y 24 \
            "cd '$hackdir' && export HACKDIR='$hackdir' NETHACKOPTIONS='@/opt/nethack/nethackrc.player'; exec '$NETHACK' -u '$player_name'"
    else
        log "play: launching tmux new-session $session_name (default hackdir nethack -u $player_name)"
        tmux new-session -s "$session_name" -x 80 -y 24 \
            "export NETHACKOPTIONS='@/opt/nethack/nethackrc.player'; exec '$NETHACK' -u '$player_name'"
    fi
}

capture_game_stats() {
    local target="$1"
    local screen status dlvl exp turns

    screen=$(tmux capture-pane -t "$target" -p 2>/dev/null | tr -d '\r')
    status=$(printf '%s\n' "$screen" | grep -E 'Dlvl:|T:[0-9]' | tail -1)
    dlvl=$(printf '%s\n' "$status" | sed -n 's/.*Dlvl:\([^ ]*\).*/\1/p')
    exp=$(printf '%s\n' "$status" | sed -n 's/.*Exp:\([^ ]*\).*/\1/p')
    turns=$(printf '%s\n' "$status" | sed -n 's/.*T:\([0-9][0-9]*\).*/\1/p')

    printf '%s\t%s\t%s\n' "$dlvl" "$exp" "$turns"
}

format_game_details() {
    local role="$1"
    local entry_type="$2"
    local dlvl="$3"
    local exp="$4"
    local turns="$5"
    local parts=()

    [ -n "$role" ] && parts+=("Classe=$role")
    [ -n "$dlvl" ] && parts+=("Dlvl=$dlvl")
    [ -n "$exp" ] && parts+=("Exp=$exp")
    [ -n "$turns" ] && parts+=("Tours=$turns")

    if [ "$entry_type" = "save" ]; then
        if [ -n "$dlvl$exp$turns" ]; then
            parts+=("Etat=sauvegarde, dernier connu")
        else
            parts+=("Etat=sauvegarde")
        fi
    elif [ -z "$dlvl$exp$turns" ]; then
        parts+=("Etat=en cours")
    fi

    local out=""
    local item
    for item in "${parts[@]}"; do
        if [ -n "$out" ]; then
            out="$out | $item"
        else
            out="$item"
        fi
    done
    [ -n "$out" ] && printf ' [%s]' "$out"
}

# Returns list of save names (character names from save files)
get_saves() {
    if [ -d "$SAVE_DIR" ]; then
        local f
        for f in "$SAVE_DIR"/*.gz; do
            [ -f "$f" ] || continue
            local base
            base=$(basename "$f")
            # Format: <uid><name>.gz — strip leading digits and .gz
            echo "$base" | sed 's/^[0-9]*//' | sed 's/\.gz$//'
        done | sort -u
    fi
}

save_exists_for_player() {
    local player_name="$1"
    local f base save_name
    for f in "$SAVE_DIR"/*.gz; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        save_name=$(echo "$base" | sed 's/^[0-9]*//' | sed 's/\.gz$//')
        [ "$save_name" = "$player_name" ] && return 0
    done
    return 1
}

show_menu() {
    clear
    local wish_count
    wish_count=$(get_wish_count)
    local bot_status
    bot_status=$(get_bot_status)

    echo "========================================"
    echo "   Super NetHack Wish Server"
    echo "========================================"
    echo ""
    echo "  [p] Jouer (nouvelle partie / reprendre)"
    echo "  [w] Rejoindre un wish game ($wish_count disponibles)"
    echo "  [s] Observer une partie en cours"
    echo "  [b] Wish bots [$bot_status]"
    echo "  [q] Quitter"
    echo ""
    echo "========================================"
    echo -n "Choix: "
}

play_game() {
    echo ""

    # Collect resumable claimed wish games: active tmux sessions + save files.
    local entries=()      # display strings
    local names=()        # character names (for -u flag)
    local types=()        # "active" or "save"
    local targets=()      # tmux session to attach for active entries
    local roles=()        # original wish role, used to restore from the right HACKDIR
    local hackdirs=()     # original HACKDIR, when preserved in wish metadata
    local details=()      # short class/status stats for display
    local active_names=()
    local wish_count=0

    # Active play tmux sessions that belong to a claimed wish save.
    local sess
    while IFS= read -r sess; do
        [ -n "$sess" ] || continue
        local pname="${sess#play-}"
        local claim_info=()
        if ! readarray -t claim_info < <(load_claimed_wish_info "$pname" 2>/dev/null); then
            continue
        fi
        local wish_label="${claim_info[0]:-wish}"
        local wish_role="${claim_info[3]:-}"
        local wish_hackdir="${claim_info[4]:-}"
        local stats dlvl exp turns
        stats=$(capture_game_stats "$sess")
        IFS=$'\t' read -r dlvl exp turns <<< "$stats"
        update_claimed_wish_stats "$pname" "$dlvl" "$exp" "$turns"

        entries+=("$wish_label - $pname (wish en cours)")
        names+=("$pname")
        types+=("active")
        targets+=("$sess")
        roles+=("$wish_role")
        hackdirs+=("$wish_hackdir")
        details+=("$(format_game_details "$wish_role" "active" "$dlvl" "$exp" "$turns")")
        active_names+=("$pname")
        ((wish_count++))
    done < <(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep '^play-' | sort)

    # Active claimed wish sessions.
    while IFS=$'\t' read -r sess char_name wish_label wish_role wish_hackdir; do
        [ -n "$sess" ] || continue
        [ -n "$char_name" ] || continue
        [ -n "$wish_label" ] || wish_label="wish"
        local stats dlvl exp turns
        stats=$(capture_game_stats "$sess")
        IFS=$'\t' read -r dlvl exp turns <<< "$stats"
        update_claimed_wish_stats "$char_name" "$dlvl" "$exp" "$turns"

        local dup=0
        local n
        for n in "${active_names[@]}"; do
            [ "$n" = "$char_name" ] && dup=1 && break
        done
        [ "$dup" -eq 1 ] && continue

        entries+=("$wish_label - $char_name (wish en cours)")
        names+=("$char_name")
        types+=("active")
        targets+=("$sess")
        roles+=("$wish_role")
        hackdirs+=("$wish_hackdir")
        details+=("$(format_game_details "$wish_role" "active" "$dlvl" "$exp" "$turns")")
        active_names+=("$char_name")
        ((wish_count++))
    done < <(python3 "$WISH_UTILS" list-claimed-active "$DATA_DIR" "$CLAIM_DIR" 2>/dev/null)

    # Wish save files on disk (skip if already listed as active).
    local sname
    while IFS= read -r sname; do
        [ -n "$sname" ] || continue
        local dup=0
        local n
        for n in "${active_names[@]}"; do
            [ "$n" = "$sname" ] && dup=1 && break
        done
        [ "$dup" -eq 1 ] && continue

        local claim_info=()
        local wish_label=""
        local wish_role=""
        local wish_hackdir=""
        local wish_dlvl=""
        local wish_exp=""
        local wish_turns=""
        if readarray -t claim_info < <(load_claimed_wish_info "$sname" 2>/dev/null); then
            wish_label="${claim_info[0]:-}"
            wish_role="${claim_info[3]:-}"
            wish_hackdir="${claim_info[4]:-}"
            wish_dlvl="${claim_info[5]:-}"
            wish_exp="${claim_info[6]:-}"
            wish_turns="${claim_info[7]:-}"
        fi
        [ -n "$wish_label" ] || continue

        entries+=("$wish_label - $sname (wish sauvegarde)")
        names+=("$sname")
        types+=("save")
        targets+=("")
        roles+=("$wish_role")
        hackdirs+=("$wish_hackdir")
        details+=("$(format_game_details "$wish_role" "save" "$wish_dlvl" "$wish_exp" "$wish_turns")")
        ((wish_count++))
    done < <(get_saves)

    if [ "$wish_count" -gt 0 ]; then
        echo "=== Parties wish existantes ==="
        echo ""
        local i=1
        local idx
        for idx in "${!entries[@]}"; do
            echo "  [$i] ${entries[$idx]}${details[$idx]}"
            ((i++))
        done
        echo ""
        echo "Entrez un numero pour reprendre, ou un nouveau nom"
    else
        echo "Aucune partie wish a reprendre."
        echo "Entrez un nom pour votre personnage"
    fi

    echo -n "(ou [b] retour): "
    read -r input

    [ "$input" = "b" ] && return
    [ -z "$input" ] && return

    local player_name="$input"
    local entry_type=""
    local attach_target=""
    local wish_role=""
    local wish_hackdir=""

    # If input is a number, pick from list.
    if [[ "$input" =~ ^[0-9]+$ ]] && [ "$input" -ge 1 ] && [ "$input" -le ${#names[@]} ]; then
        player_name="${names[$((input-1))]}"
        entry_type="${types[$((input-1))]}"
        attach_target="${targets[$((input-1))]}"
        wish_role="${roles[$((input-1))]}"
        wish_hackdir="${hackdirs[$((input-1))]}"
    fi

    # Sanitize: only allow alphanumeric and underscore.
    player_name=$(echo "$player_name" | tr -cd 'a-zA-Z0-9_')
    if [ -z "$player_name" ]; then
        echo "Nom invalide (lettres, chiffres, _ uniquement)."
        sleep 1
        return
    fi

    local session_name="play-${player_name}"
    local display_name="$player_name"
    local claim_info=()
    if readarray -t claim_info < <(load_claimed_wish_info "$player_name" 2>/dev/null); then
        display_name="${claim_info[0]} - $player_name"
        [ -n "$wish_role" ] || wish_role="${claim_info[3]:-}"
        [ -n "$wish_hackdir" ] || wish_hackdir="${claim_info[4]:-}"
    fi
    log "play: name='$player_name' session='$session_name' type='$entry_type' attach='$attach_target' role='$wish_role' hackdir='$wish_hackdir'"

    # Case 1: Active tmux session, just reattach.
    if [ "$entry_type" = "active" ] && [ -n "$attach_target" ]; then
        echo "Reconnexion a la partie $display_name..."
        sleep 1
        log "play: attaching to selected active session $attach_target"
        tmux attach-session -t "$attach_target"
        backup_save_for_player "$player_name" "after_active"
        log "play: returned from attach"
        return
    fi

    if tmux has-session -t "$session_name" 2>/dev/null; then
        echo "Reconnexion a la partie $display_name..."
        sleep 1
        log "play: attaching to existing session $session_name"
        tmux attach-session -t "$session_name"
        backup_save_for_player "$player_name" "after_active"
        log "play: returned from attach"
        return
    fi

    # Case 2: Save file exists, resume. Case 3: no save, new game.
    local has_save=""
    if save_exists_for_player "$player_name"; then
        has_save="yes"
    fi

    if [ -n "$has_save" ]; then
        backup_save_for_player "$player_name" "before_restore"
        echo "Reprise de la partie $display_name..."
    else
        echo "Nouvelle partie pour $display_name..."
    fi
    sleep 1

    # Launch nethack in a new tmux session (foreground, takes over terminal).
    launch_nethack_session "$session_name" "$player_name" "$wish_role" "$wish_hackdir"
    backup_save_for_player "$player_name" "after_play"
    log "play: tmux exited rc=$?"
}

join_wish_game() {
    echo ""
    echo "=== Choisir une classe ==="
    local i=1
    local role
    for role in "${ROLES[@]}"; do
        echo "  [$i] $role ($(get_role_wish_count "$role") disponibles)"
        ((i++))
    done

    echo ""
    echo -n "Classe (1-${#ROLES[@]}) ou [b] retour: "
    read -r role_choice

    [ "$role_choice" = "b" ] && return

    if ! [[ "$role_choice" =~ ^[0-9]+$ ]] || [ "$role_choice" -lt 1 ] || [ "$role_choice" -gt ${#ROLES[@]} ]; then
        echo "Choix invalide."
        sleep 1
        return
    fi

    local selected_role="${ROLES[$((role_choice-1))]}"
    local wish_sessions=()
    local wish_paths=()
    local wish_charnames=()
    local wish_roles=()
    local wish_hackdirs=()

    while IFS=$'\t' read -r session_name char_name path role hackdir; do
        [ -n "$session_name" ] || continue
        wish_sessions+=("$session_name")
        wish_charnames+=("$char_name")
        wish_paths+=("$path")
        wish_roles+=("$role")
        wish_hackdirs+=("$hackdir")
    done < <(python3 "$WISH_UTILS" list-ready "$DATA_DIR" "$selected_role" 2>/dev/null)

    if [ ${#wish_sessions[@]} -eq 0 ]; then
        echo ""
        if [ -f "$ENABLED_FLAG" ]; then
            echo "Aucun wish game $selected_role disponible pour le moment."
            echo "Les bots sont en train de preparer des parties pour cette classe..."
        else
            echo "Aucun wish game disponible."
            echo "Activez les bots avec [b] depuis le menu principal."
        fi
        echo ""
        read -n 1 -s -r -p "Appuyez sur une touche pour continuer..."
        return
    fi

    echo ""
    echo "=== Wish Games $selected_role Disponibles ==="
    i=1
    local idx
    for idx in "${!wish_sessions[@]}"; do
        echo "  [$i] ${wish_sessions[$idx]} (personnage: ${wish_charnames[$idx]}, classe: ${wish_roles[$idx]})"
        ((i++))
    done

    echo ""
    echo -n "Choisir (1-${#wish_sessions[@]}) ou [b] retour: "
    read -r choice

    [ "$choice" = "b" ] && return

    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#wish_sessions[@]} ]; then
        local selected="${wish_sessions[$((choice-1))]}"
        local selected_path="${wish_paths[$((choice-1))]}"
        local selected_char="${wish_charnames[$((choice-1))]}"
        local selected_role="${wish_roles[$((choice-1))]}"
        local selected_hackdir="${wish_hackdirs[$((choice-1))]}"
        local wish_label
        wish_label=$(ensure_claimed_wish "$selected" "$selected_char" "$selected_role" "$selected_hackdir")
        local stats dlvl exp turns
        stats=$(capture_game_stats "$selected")
        IFS=$'\t' read -r dlvl exp turns <<< "$stats"
        update_claimed_wish_stats "$selected_char" "$dlvl" "$exp" "$turns"

        # Mark the session as claimed
        python3 -c "
import json, sys
path = sys.argv[1]
with open(path, 'r') as fh:
    data = json.load(fh)
data['status'] = 'claimed'
with open(path, 'w') as fh:
    json.dump(data, fh)
" "$selected_path" 2>/dev/null

        echo ""
        echo "Connexion a $selected..."
        echo "Le prompt 'For what do you wish?' vous attend!"
echo ""
echo "Personnage: $selected_char"
        echo "Classe: $selected_role"
echo "Label: $wish_label"
        echo "Apres #save ou deconnexion SSH, reprenez via [p] et choisissez la ligne $wish_label"
        sleep 2

        log "wish: attaching to $selected"
        tmux attach-session -t "$selected"
        backup_save_for_player "$selected_char" "after_wish"
        log "wish: returned from attach"

        # Don't kill the session — the player might have saved
        # and want to come back. Only clean up dead sessions.
        if tmux has-session -t "$selected" 2>/dev/null; then
            # Check if the nethack process is still alive
            local pane_pid
            pane_pid=$(tmux list-panes -t "$selected" -F '#{pane_pid}' 2>/dev/null)
            if [ -n "$pane_pid" ] && ! kill -0 "$pane_pid" 2>/dev/null; then
                tmux kill-session -t "$selected" 2>/dev/null
            fi
        fi
    else
        echo "Choix invalide."
        sleep 1
    fi
}

spectate_game() {
    local sessions=()
    while IFS= read -r s; do
        [ -n "$s" ] && sessions+=("$s")
    done < <(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep -E '^(play-|wish-)' | sort)

    if [ ${#sessions[@]} -eq 0 ]; then
        echo ""
        echo "Aucune partie en cours."
        read -n 1 -s -r -p "Appuyez sur une touche pour continuer..."
        return
    fi

    echo ""
    echo "=== Parties en cours ==="
    local i=1
    for s in "${sessions[@]}"; do
        echo "  [$i] $s"
        ((i++))
    done

    echo ""
    echo -n "Observer (1-${#sessions[@]}) ou [b] retour: "
    read -r choice

    [ "$choice" = "b" ] && return

    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#sessions[@]} ]; then
        local selected="${sessions[$((choice-1))]}"
        echo "Observation de $selected (lecture seule)..."
        sleep 1
        tmux attach-session -t "$selected" -r
    else
        echo "Choix invalide."
        sleep 1
    fi
}

toggle_bots() {
    echo ""
    if [ -f "$ENABLED_FLAG" ]; then
        rm -f "$ENABLED_FLAG"
        echo "Wish bots DESACTIVES."
        echo "Les bots en cours vont s'arreter progressivement."
    else
        touch "$ENABLED_FLAG"
        echo "Wish bots ACTIVES!"
        echo "Les bots vont commencer a preparer des parties wish."
    fi
    sleep 2
}

# Main loop
while true; do
    show_menu
    read -r -n 1 key
    read -r -t 0.01 _ 2>/dev/null  # flush leftover newline
    echo ""
    case "$key" in
        p|P) play_game ;;
        w|W) join_wish_game ;;
        s|S) spectate_game ;;
        b|B) toggle_bots ;;
        q|Q) echo "Au revoir!"; exit 0 ;;
        *) echo "Choix invalide."; sleep 1 ;;
    esac
done
