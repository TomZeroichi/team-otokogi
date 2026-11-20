"""Regression checks for the mobile UI assets and route wiring."""
from pathlib import Path
from fastapi.testclient import TestClient
from app import create_app


def test_ui_assets_and_pwa(tmp_path):
    client = TestClient(create_app(str(tmp_path / 'ui.sqlite3')))
    res = client.get('/')
    assert res.status_code == 200
    assert 'TEAM狭気' in res.text
    assert '/static/app.js?v=0201' in res.text
    for path, marker in [
        ('/static/style.css', '.home-rule-cards'),
        ('/static/app.js', 'data-analysis'),
        ('/static/hero.svg', '<svg'),
        ('/static/waves.svg', '<svg'),
        ('/static/icon.svg', '<svg'),
        ('/static/manifest.webmanifest', 'TEAM狭気'),
    ]:
        result = client.get(path)
        assert result.status_code == 200, path
        assert marker in result.text, path
    for size in (192, 512):
        result = client.get(f'/static/icon-{size}.png')
        assert result.status_code == 200
        assert result.headers['content-type'].startswith('image/png')


def test_mobile_navigation_in_source():
    script = (Path(__file__).resolve().parents[1] / 'static' / 'app.js').read_text()
    assert all(name in script for name in ('ホーム', 'ランキング', '記録', '分析', 'メンバー'))
    assert 'historical_mode' in script
    assert 'next_decider_id' in script
    assert "'/api/choose-mode'" in script
    assert "'/api/rounds'" in script
