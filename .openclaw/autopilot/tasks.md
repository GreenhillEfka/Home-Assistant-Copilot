# Autopilot Task Queue

## Active Tasks (Priority Order)

### 1. Interactive Brain Graph Panel (NEXT)
**Status**: Ready to start
**Model**: qwen3-coder-next:cloud (via Ollama) or Gemini CLI
**Scope**: 
- Interactive D3.js/Vis.js visualization
- Replace static SVG with live graph
- Zoom, pan, filter, search
- Click nodes for entity details
- Real-time updates via HA websocket

**Files to create/modify**:
- `ai_home_copilot_hacs_repo/custom_components/ai_home_copilot/www/brain_graph_panel.js`
- `ai_home_copilot_hacs_repo/custom_components/ai_home_copilot/views/brain_graph_panel.py`
- Update `brain_graph_viz.py` for JSON API

### 2. Multi-User Preference Learning
**Status**: Planned
**Model**: TBD
**Scope**: Learn preferences per user, not just global

### 3. Performance Optimization
**Status**: Planned
**Scope**: Cache optimization, query reduction

## Completed Tasks
- v0.7.5: Entity ID sanitization, Habitus Dashboard Cards
- v0.4.16: Core API auth fixes
- v0.4.15: Habitus Zones v2
- v0.4.14: Tag System v0.2

## Release Workflow
1. Complete task in dev branch
2. Run tests
3. Update CHANGELOG
4. Ask user for release approval (Telegram)
5. Merge to main, tag release
6. Create GitHub release with notes
