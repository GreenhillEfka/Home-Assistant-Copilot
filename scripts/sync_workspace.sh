#!/bin/bash
# Sync Script - Synchronisiert Workspace mit React Board Context

set -e

WORKSPACE="/config/.openclaw/workspace"
REACT_BOARD="/config/.openclaw/canvas/ReactBoard"
CONTEXT_FILES=(
    "MEMORY.md"
    "AGENTS.md"
    "SOUL.md"
    "USER.md"
    "TOOLS.md"
    "HEARTBEAT.md"
    "IDENTITY.md"
)

PROJECTS=(
    "ai_home_copilot"
    "core_addon"
)

log() { echo "[$(date '+%H:%M:%S')] $1"; }

# ==========================================
# 1. Context Files zu React Board
# ==========================================
sync_context() {
    log "Syncing Context Files..."
    
    for file in "${CONTEXT_FILES[@]}"; do
        src="$WORKSPACE/$file"
        if [ -f "$src" ]; then
            log "  ✅ $file"
            # Context wird automatisch von app.js geladen
        else
            log "  ⚠️ $file nicht gefunden"
        fi
    done
}

# ==========================================
# 2. Project INDEX zu React Board
# ==========================================
sync_projects() {
    log "Syncing Projects..."
    
    for project in "${PROJECTS[@]}"; do
        project_path="$WORKSPACE/projects/$project"
        index_file="$project_path/INDEX.md"
        
        if [ -f "$index_file" ]; then
            log "  ✅ $project/INDEX.md"
            # INDEX wird automatisch geladen
        else
            log "  ⚠️ $project/INDEX.md nicht gefunden"
        fi
    done
}

# ==========================================
# 3. Activity Log
# ==========================================
log_activity() {
    local type="$1"
    local title="$2"
    local description="$3"
    
    curl -s -X POST "http://localhost:3001/api/activity" \
        -H "Content-Type: application/json" \
        -d "{\"type\": \"$type\", \"title\": \"$title\", \"description\": \"$description\", \"badge\": \"🔄\"}" \
        > /dev/null 2>&1
    
    log "Activity: $title"
}

# ==========================================
# 4. GitHub Status
# ==========================================
sync_github() {
    log "Syncing GitHub Status..."
    
    # HA Integration
    cd "$WORKSPACE/ai_home_copilot_hacs_repo"
    ha_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    ha_status=$(git status --short 2>/dev/null | wc -l)
    
    log "  HA Integration: $ha_branch ($ha_status changes)"
    
    # Core Add-on
    cd "$WORKSPACE/ha-copilot-repo"
    core_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    core_status=$(git status --short 2>/dev/null | wc -l)
    
    log "  Core Add-on: $core_branch ($core_status changes)"
    
    # Activity loggen
    log_activity "sync" "🔄 GitHub Sync" "HA: $ha_branch, Core: $core_branch"
}

# ==========================================
# 5. Vollständiger Sync
# ==========================================
full_sync() {
    log ""
    log "========================================"
    log "Workspace Sync"
    log "========================================"
    
    sync_context
    sync_projects
    sync_github
    
    log ""
    log "✅ Sync abgeschlossen!"
    log ""
}

# ==========================================
# Main
# ==========================================
case "${1:-full}" in
    context)
        sync_context
        ;;
    projects)
        sync_projects
        ;;
    github)
        sync_github
        ;;
    *)
        full_sync
        ;;
esac
