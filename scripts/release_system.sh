#!/bin/bash
# AI Home CoPilot - Unified Release System
# Stand: 2026-02-15
# Zweck: Sauberes, reproduzierbares Release für beide Repos

set -e

REPO_HA="/config/.openclaw/workspace/ai_home_copilot_hacs_repo"
REPO_CORE="/config/.openclaw/workspace/ha-copilot-repo"
ACTIVITY_API="http://localhost:3001/api/activity"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
log_ok() { echo -e "${GREEN}[✓]${NC} $1"; }
log_err() { echo -e "${RED}[✗]${NC} $1"; }

# Activity an Dashboard senden
notify_dashboard() {
    local type="$1" title="$2" desc="$3" badge="$4"
    curl -s -X POST "$ACTIVITY_API" -H 'Content-Type: application/json' \
        -d "{\"type\":\"$type\",\"title\":\"$title\",\"description\":\"$desc\",\"badge\":\"$badge\"}" >/dev/null 2>&1 || true
}

# ==========================================
# STATUS CHECK
# ==========================================
status() {
    log "Prüfe Repository-Status..."
    echo ""
    
    echo "=== HA Integration ==="
    cd "$REPO_HA"
    local ha_branch=$(git branch --show-current)
    local ha_changes=$(git status --short | wc -l)
    local ha_last=$(git log --oneline -1)
    echo "Branch: $ha_branch"
    echo "Uncommitted: $ha_changes"
    echo "Last: $ha_last"
    echo ""
    
    echo "=== Core Add-on ==="
    cd "$REPO_CORE"
    local core_branch=$(git branch --show-current)
    local core_changes=$(git status --short | wc -l)
    local core_last=$(git log --oneline -1)
    echo "Branch: $core_branch"
    echo "Uncommitted: $core_changes"
    echo "Last: $core_last"
    echo ""
    
    log_ok "Status complete"
}

# ==========================================
# SYNC: Pull + Status
# ==========================================
sync() {
    log "Synchronisiere mit GitHub..."
    
    cd "$REPO_HA"
    git fetch origin 2>/dev/null || true
    git pull origin development 2>/dev/null || log "HA: Keine neuen Changes"
    
    cd "$REPO_CORE"
    git fetch origin 2>/dev/null || true
    git pull origin main 2>/dev/null || log "Core: Keine neuen Changes"
    
    notify_dashboard "sync" "🔄 GitHub Sync" "Beide Repos synchronisiert" "🔄"
    log_ok "Sync complete"
}

# ==========================================
# COMMIT: Uncommitted Changes sichern
# ==========================================
commit() {
    local message="${1:-chore: Auto-sync $(date +%Y-%m-%d)}"
    
    log "Committe Changes..."
    
    cd "$REPO_HA"
    if [ -n "$(git status --short)" ]; then
        git add -A
        git commit -m "$message (HA Integration)"
        log_ok "HA Integration committed"
    else
        log "HA Integration: Keine Changes"
    fi
    
    cd "$REPO_CORE"
    if [ -n "$(git status --short)" ]; then
        git add -A
        git commit -m "$message (Core Add-on)"
        log_ok "Core Add-on committed"
    else
        log "Core Add-on: Keine Changes"
    fi
    
    notify_dashboard "commit" "💾 Changes committed" "$message" "📝"
}

# ==========================================
# PUSH: Zu GitHub
# ==========================================
push() {
    log "Pushe zu GitHub..."
    
    cd "$REPO_HA"
    local ha_branch=$(git branch --show-current)
    git push origin "$ha_branch" 2>/dev/null || log_err "HA Push fehlgeschlagen"
    
    cd "$REPO_CORE"
    local core_branch=$(git branch --show-current)
    git push origin "$core_branch" 2>/dev/null || log_err "Core Push fehlgeschlagen"
    
    notify_dashboard "push" "🚀 GitHub Push" "Beide Repos gepushed" "🚀"
    log_ok "Push complete"
}

# ==========================================
# RELEASE: Full Release Workflow
# ==========================================
release() {
    local version="$1"
    
    if [ -z "$version" ]; then
        log_err "Version erforderlich: release.sh release v0.X.X"
        exit 1
    fi
    
    log "Starte Release $version..."
    notify_dashboard "release" "🏷️ Release $version" "Release-Workflow gestartet" "🚀"
    
    # 1. Sync
    sync
    
    # 2. Commit offene Changes
    commit "chore: Pre-release commit for $version"
    
    # 3. Tag erstellen
    cd "$REPO_HA"
    git tag -a "v$version" -m "Release $version" 2>/dev/null || log "Tag existiert bereits"
    git push origin "v$version" 2>/dev/null || true
    
    cd "$REPO_CORE"
    git tag -a "v$version" -m "Release $version" 2>/dev/null || log "Tag existiert bereits"
    git push origin "v$version" 2>/dev/null || true
    
    # 4. Push
    push
    
    notify_dashboard "release" "✅ Release $version" "Erfolgreich veröffentlicht" "🎉"
    log_ok "Release $version complete!"
}

# ==========================================
# DASHBOARD: Projektdaten aktualisieren
# ==========================================
dashboard() {
    log "Aktualisiere Dashboard..."
    
    # Hole aktuelle Daten
    cd "$REPO_HA"
    local ha_version=$(git describe --tags --always 2>/dev/null || echo "dev")
    local ha_commits=$(git rev-list --count HEAD 2>/dev/null || echo "?")
    
    cd "$REPO_CORE"
    local core_version=$(git describe --tags --always 2>/dev/null || echo "dev")
    local core_commits=$(git rev-list --count HEAD 2>/dev/null || echo "?")
    
    notify_dashboard "project" "📦 HA Integration" "v$ha_version | $ha_commits commits" "🏠"
    notify_dashboard "project" "⚙️ Core Add-on" "v$core_version | $core_commits commits" "🔧"
    
    log_ok "Dashboard updated"
}

# ==========================================
# FULL: Kompletter Workflow
# ==========================================
full() {
    log "=== Full Orchestration ==="
    status
    sync
    commit "chore: Auto-sync $(date +%Y-%m-%d_%H:%M)"
    push
    dashboard
    log_ok "=== Complete ==="
}

# ==========================================
# Main
# ==========================================
case "${1:-status}" in
    status) status ;;
    sync) sync ;;
    commit) commit "${2:-chore: Auto-sync}" ;;
    push) push ;;
    release) release "$2" ;;
    dashboard) dashboard ;;
    full) full ;;
    *)
        echo "Usage: $0 {status|sync|commit|push|release|dashboard|full}"
        echo ""
        echo "Commands:"
        echo "  status    - Zeige Repository-Status"
        echo "  sync      - Pull von GitHub"
        echo "  commit    - Committe alle Changes"
        echo "  push      - Pushe zu GitHub"
        echo "  release   - Full Release mit Tag (needs version)"
        echo "  dashboard - Aktualisiere ReactBoard"
        echo "  full      - Kompletter Workflow"
        ;;
esac