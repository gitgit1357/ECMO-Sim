from pathlib import Path


def _workspace_source() -> str:
    return (Path(__file__).resolve().parents[1] / "src" / "neogui" / "ecmo_workspace.py").read_text()


def test_phase8_preserves_training_positioning_and_existing_state_categories():
    source = _workspace_source()
    assert 'POSITIONING_LABEL = "SIMULATION / TRAINING ONLY"' in source
    for token in ("CYAN =", "GREEN =", "YELLOW =", "RED =", "ORANGE ="):
        assert token in source


def test_phase8_visual_pass_does_not_add_scoring_or_new_clinical_state():
    source = _workspace_source().lower()
    prohibited = ("score_button", "grade_button", "clinical_score", "diagnosis_score", "correct_action")
    assert not any(token in source for token in prohibited)


def test_phase8_navigation_and_primary_telemetry_use_consistent_hierarchy():
    source = _workspace_source()
    assert 'self.nav = tk.Frame(shell, bg=self.NAV, width=132)' in source
    assert 'wraplength=108' in source
    assert 'font=("Consolas", 17, "bold")' in source
    assert 'font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=(8, 0))' in source


def test_phase8_window_keeps_compact_minimum_while_improving_default_workspace():
    source = _workspace_source()
    assert 'self.root.geometry("1440x900")' in source
    assert 'self.root.minsize(1080, 680)' in source


def test_phase8_live_tk_workspace_renders_all_pages_at_minimum_supported_size():
    from neogui.ecmo_workspace import EcmoWorkspace

    app = EcmoWorkspace()
    try:
        app.root.geometry("1080x680")
        app.root.update()
        assert int(app.nav.cget("width")) == 112
        app.root.geometry("1440x900")
        app.root.update()
        assert int(app.nav.cget("width")) == 132
        app.root.geometry("1080x680")
        app.root.update()
        for key in ("ECMO", "MON", "VENT", "LABS", "ACT", "LOG"):
            app._show_page(key)
            app.root.update_idletasks()
            frame = app.page_frames[key]
            assert frame.winfo_width() > 0
            assert frame.winfo_height() > 0
        assert app.POSITIONING_LABEL == "SIMULATION / TRAINING ONLY"
    finally:
        app._close()


def test_phase8_resize_handler_changes_presentation_only():
    source = _workspace_source()
    start = source.index("def _on_workspace_resize")
    end = source.index("def _configure_styles", start)
    block = source[start:end]
    assert "event.width < 1240" in block
    assert "self.nav.configure(width=nav_width)" in block
    assert "self.model" not in block
    assert "_apply_snapshot" not in block
    assert ".update(" not in block


def test_phase8_secondary_pages_share_compact_title_and_content_gutters():
    source = _workspace_source()
    # One shared title-frame expression is intentionally reused across all
    # secondary learner surfaces for consistent vertical rhythm.
    assert source.count('title = tk.Frame(parent, bg=self.SCREEN, padx=20, pady=12)') >= 5
    assert 'padx=(20, 6)' in source
    assert 'padx=(6, 20)' in source


def test_phase8_console_grouping_uses_consistent_tile_and_control_spacing():
    source = _workspace_source()
    assert 'self.telemetry_bar = tk.Frame(parent, bg=self.SCREEN, padx=8, pady=7)' in source
    assert 'sticky="nsew", padx=3, pady=3' in source
    assert 'controls = tk.Frame(parent, bg="#121c22", padx=6, pady=4)' in source
