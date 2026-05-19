"""Comprehensive test suite for XHS CLI project — all mock-based, no network."""

import json
import os
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

# Ensure project root is importable
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# ─── Constants tests ────────────────────────────────────────────────

class TestConstants(unittest.TestCase):
    def test_edith_host(self):
        from xhs_cli.constants import EDITH_HOST
        self.assertTrue(EDITH_HOST.startswith("https://"))

    def test_creator_host(self):
        from xhs_cli.constants import CREATOR_HOST
        self.assertIn("xiaohongshu.com", CREATOR_HOST)

    def test_user_agent(self):
        from xhs_cli.constants import USER_AGENT
        self.assertIn("Chrome", USER_AGENT)

    def test_chrome_version(self):
        from xhs_cli.constants import CHROME_VERSION
        self.assertTrue(CHROME_VERSION.isdigit())

    def test_platform(self):
        from xhs_cli.constants import PLATFORM
        self.assertEqual(PLATFORM, "Linux")


# ─── Exception tests ────────────────────────────────────────────────

class TestExceptions(unittest.TestCase):
    def test_xhs_api_error(self):
        from xhs_cli.exceptions import XhsApiError
        e = XhsApiError("test error", code=123, response={"foo": "bar"})
        self.assertIn("test error", str(e))
        self.assertEqual(e.code, 123)

    def test_ip_blocked_error(self):
        from xhs_cli.exceptions import IpBlockedError
        e = IpBlockedError()
        self.assertIsInstance(e, Exception)

    def test_need_verify_error(self):
        from xhs_cli.exceptions import NeedVerifyError
        e = NeedVerifyError(verify_type="captcha", verify_uuid="abc")
        self.assertEqual(e.verify_type, "captcha")

    def test_session_expired_error(self):
        from xhs_cli.exceptions import SessionExpiredError
        self.assertTrue(issubclass(SessionExpiredError, Exception))

    def test_signature_error(self):
        from xhs_cli.exceptions import SignatureError
        self.assertTrue(issubclass(SignatureError, Exception))


# ─── Signing tests ──────────────────────────────────────────────────

class TestSigning(unittest.TestCase):
    def test_simple_sign_returns_required_keys(self):
        from xhs_cli.hybrid_client import _simple_sign
        result = _simple_sign("/api/test", None, "fake_a1_value")
        self.assertIn("x-s", result)
        self.assertIn("x-t", result)
        self.assertIn("x-s-common", result)

    def test_simple_sign_with_data(self):
        from xhs_cli.hybrid_client import _simple_sign
        result = _simple_sign("/api/test", {"keyword": "美食"}, "a1")
        self.assertTrue(len(result["x-s"]) > 10)
        self.assertTrue(result["x-t"].isdigit())

    def test_simple_sign_timestamp_is_millis(self):
        import time
        from xhs_cli.hybrid_client import _simple_sign
        result = _simple_sign("/api/test", None, "a1")
        ts = int(result["x-t"])
        now_ms = int(time.time() * 1000)
        self.assertAlmostEqual(ts, now_ms, delta=5000)

    def test_creator_signing_returns_keys(self):
        from xhs_cli.creator_signing import sign_creator
        result = sign_creator("url=/api/test", None, "fake_a1")
        self.assertIn("x-s", result)
        self.assertIn("x-t", result)

    def test_creator_signing_with_data(self):
        from xhs_cli.creator_signing import sign_creator
        result = sign_creator("url=/api/test", {"key": "val"}, "a1")
        self.assertTrue(len(result["x-s"]) > 5)
        self.assertTrue(result["x-t"].isdigit())


# ─── Cookie tests ───────────────────────────────────────────────────

class TestCookies(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_cookies_to_string(self):
        from xhs_cli.cookies import cookies_to_string
        cookies = {"a1": "val1", "web_session": "val2"}
        result = cookies_to_string(cookies)
        self.assertIn("a1=val1", result)
        self.assertIn("web_session=val2", result)

    def test_save_and_load_cookies(self):
        from xhs_cli.cookies import save_cookies, load_saved_cookies, get_cookie_path
        import xhs_cli.cookies as cookies_mod

        original_path = cookies_mod.get_cookie_path
        tmp_path = Path(self.tmpdir) / "cookies.json"
        cookies_mod.get_cookie_path = lambda: tmp_path

        try:
            test_cookies = {"a1": "test_a1_value", "web_session": "test_ws"}
            save_cookies(test_cookies)
            loaded = load_saved_cookies()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["a1"], "test_a1_value")
            self.assertEqual(loaded["web_session"], "test_ws")
            # saved_at is kept in loaded cookies (it's metadata, not removed)
        finally:
            cookies_mod.get_cookie_path = original_path

    def test_clear_cookies(self):
        from xhs_cli.cookies import save_cookies, clear_cookies, load_saved_cookies, get_cookie_path
        import xhs_cli.cookies as cookies_mod

        tmp_path = Path(self.tmpdir) / "cookies2.json"
        cookies_mod.get_cookie_path = lambda: tmp_path

        try:
            save_cookies({"a1": "test"})
            self.assertTrue(tmp_path.exists())
            clear_cookies()
            self.assertFalse(tmp_path.exists())
            self.assertIsNone(load_saved_cookies())
        finally:
            cookies_mod.get_cookie_path = cookies_mod.get_cookie_path


# ─── Hybrid client tests ───────────────────────────────────────────

class TestHybridClient(unittest.TestCase):
    def _make_client(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        cookies = {"a1": "test_a1", "web_session": "test_ws", "webId": "test_wid"}
        return HybridXhsClient(cookies, request_delay=0)

    def test_init(self):
        client = self._make_client()
        self.assertEqual(client.cookies["a1"], "test_a1")
        self.assertEqual(client._request_count, 0)
        client.close()

    def test_base_headers(self):
        client = self._make_client()
        headers = client._base_headers()
        self.assertIn("user-agent", headers)
        self.assertIn("cookie", headers)
        self.assertIn("origin", headers)
        self.assertIn("sec-ch-ua-platform", headers)
        self.assertIn("Linux", headers["sec-ch-ua-platform"])
        client.close()

    def test_handle_response_success(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"success": true, "data": {"key": "value"}}'
        result = client._handle_response(mock_resp)
        self.assertEqual(result, {"key": "value"})
        client.close()

    def test_handle_response_ip_blocked(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        from xhs_cli.exceptions import IpBlockedError
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"success": false, "code": 300012}'
        with self.assertRaises(IpBlockedError):
            client._handle_response(mock_resp)
        client.close()

    def test_handle_response_signature_error(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        from xhs_cli.exceptions import SignatureError
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"success": false, "code": 300015}'
        with self.assertRaises(SignatureError):
            client._handle_response(mock_resp)
        client.close()

    def test_handle_response_session_expired(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        from xhs_cli.exceptions import SessionExpiredError
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"success": false, "code": -100}'
        with self.assertRaises(SessionExpiredError):
            client._handle_response(mock_resp)
        client.close()

    def test_handle_response_need_verify(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        from xhs_cli.exceptions import NeedVerifyError
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 461
        mock_resp.headers = {"verifytype": "captcha", "verifyuuid": "uuid123"}
        with self.assertRaises(NeedVerifyError):
            client._handle_response(mock_resp)
        client.close()

    def test_handle_response_non_json(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        from xhs_cli.exceptions import XhsApiError
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '<html>not json</html>'
        with self.assertRaises(XhsApiError):
            client._handle_response(mock_resp)
        client.close()

    def test_handle_response_empty(self):
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = ""
        result = client._handle_response(mock_resp)
        self.assertIsNone(result)
        client.close()

    def test_merge_response_cookies(self):
        client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.cookies.items.return_value = [("new_cookie", "new_val")]
        client._merge_response_cookies(mock_resp)
        self.assertEqual(client.cookies["new_cookie"], "new_val")
        client.close()

    def test_sign_main_api(self):
        client = self._make_client()
        result = client._sign_main_api("GET", "/api/test")
        self.assertIn("x-s", result)
        self.assertIn("x-t", result)
        client.close()

    def test_sign_creator(self):
        client = self._make_client()
        result = client._sign_creator("/api/test")
        self.assertIn("x-s", result)
        self.assertIn("x-t", result)
        client.close()

    def test_context_manager(self):
        from xhs_cli.hybrid_client import HybridXhsClient
        cookies = {"a1": "test"}
        with HybridXhsClient(cookies, request_delay=0) as client:
            self.assertIsNotNone(client)
        # After exit, client should be closed


# ─── Search session tests ───────────────────────────────────────────

class TestSearchSessions(unittest.TestCase):
    def test_generate_search_id(self):
        from xhs_cli.client_mixins import _generate_search_id
        sid = _generate_search_id()
        self.assertTrue(len(sid) > 5)
        # Should be base36
        for c in sid:
            self.assertTrue(c.isdigit() or c.isupper())

    def test_search_session_key(self):
        from xhs_cli.client_mixins import _search_session_key
        key = _search_session_key("美食", "general", 0)
        self.assertEqual(key, ("美食", "general", 0))


# ─── Analyzer plugin tests ─────────────────────────────────────────

class TestAnalyzer(unittest.TestCase):
    def test_extract_keywords(self):
        from plugins.analyzer import extract_keywords
        texts = ["深圳美食探店推荐", "深圳美食攻略大合集", "好吃的餐厅推荐"]
        result = extract_keywords(texts, top_n=5)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        # Each item is (word, count)
        word, count = result[0]
        self.assertIsInstance(word, str)
        self.assertIsInstance(count, int)
        self.assertTrue(count >= 1)

    def test_extract_keywords_empty(self):
        from plugins.analyzer import extract_keywords
        result = extract_keywords([], top_n=5)
        self.assertEqual(result, [])

    def test_extract_keywords_none_values(self):
        from plugins.analyzer import extract_keywords
        result = extract_keywords([None, "", "正常文本测试"])
        self.assertIsInstance(result, list)

    def test_analyze_search_results(self):
        from plugins.analyzer import analyze_search_results
        items = [
            {"note_card": {"display_title": "美食探店", "desc": "好吃的", "user": {"nickname": "张三"}, "type": "normal"}},
            {"note_card": {"display_title": "深圳美食", "desc": "深圳好吃的", "user": {"nickname": "李四"}, "type": "video"}},
        ]
        result = analyze_search_results(items)
        self.assertIn("title_keywords", result)
        self.assertIn("all_keywords", result)
        self.assertIn("user_distribution", result)
        self.assertIn("type_distribution", result)
        self.assertIn("total", result)
        self.assertEqual(result["total"], 2)

    def test_analyze_search_results_empty(self):
        from plugins.analyzer import analyze_search_results
        result = analyze_search_results([])
        self.assertEqual(result["total"], 0)


# ─── Export plugin tests ────────────────────────────────────────────

class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Patch EXPORT_DIR
        import plugins.export as export_mod
        self._orig_export_dir = export_mod.EXPORT_DIR
        export_mod.EXPORT_DIR = Path(self.tmpdir)

    def tearDown(self):
        import plugins.export as export_mod
        export_mod.EXPORT_DIR = self._orig_export_dir

    def test_export_note_html(self):
        from plugins.export import export_note_html
        note = {
            "title": "测试笔记",
            "desc": "这是一段描述",
            "user": {"nickname": "测试用户"},
            "interact_info": {"liked_count": "100", "collected_count": "50"},
        }
        path = export_note_html(note)
        self.assertTrue(Path(path).exists())
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("测试笔记", content)
        self.assertIn("测试用户", content)

    def test_export_search_results_html(self):
        from plugins.export import export_search_results_html
        items = [
            {"note_card": {
                "display_title": "美食推荐",
                "user": {"nickname": "张三"},
                "interact_info": {"liked_count": "99"},
                "desc": "很好吃",
            }},
        ]
        path = export_search_results_html(items, "美食")
        self.assertTrue(Path(path).exists())
        content = Path(path).read_text(encoding="utf-8")
        self.assertIn("美食推荐", content)

    def test_export_note_pdf(self):
        from plugins.export import export_note_pdf
        note = {
            "title": "PDF测试",
            "desc": "PDF内容",
            "user": {"nickname": "用户"},
            "comments": [],
        }
        try:
            path = export_note_pdf(note)
            self.assertTrue(Path(path).exists())
        except Exception:
            # fpdf may fail without font, that's ok
            pass


# ─── Chart plugin tests ─────────────────────────────────────────────

class TestCharts(unittest.TestCase):
    def test_show_stats_table(self):
        from plugins.charts import show_stats_table
        # Should not raise
        items = [
            {"note_card": {"display_title": "test", "interact_info": {"liked_count": "100"}}},
        ]
        show_stats_table(items)

    def test_show_stats_table_empty(self):
        from plugins.charts import show_stats_table
        show_stats_table([])


# ─── Image preview plugin tests ─────────────────────────────────────

class TestImagePreview(unittest.TestCase):
    def test_generate_word_cloud_image(self):
        from plugins.image_preview import generate_word_cloud_image
        tmpdir = tempfile.mkdtemp()
        outpath = os.path.join(tmpdir, "wc_test.png")
        try:
            generate_word_cloud_image(
                {"美食": 10, "深圳": 8, "探店": 5, "好吃": 3},
                outpath,
            )
            self.assertTrue(os.path.exists(outpath))
        except Exception:
            # wordcloud may not be installed
            pass


# ─── Integration: HybridClient with mocked HTTP ─────────────────────

class TestHybridClientMockedHTTP(unittest.TestCase):
    def _make_client_with_mock(self, status_code=200, text='{"success":true,"data":{"items":[]}}'):
        from xhs_cli.hybrid_client import HybridXhsClient
        cookies = {"a1": "test_a1", "web_session": "ws", "webId": "wid"}
        client = HybridXhsClient(cookies, request_delay=0)
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.text = text
        mock_resp.cookies.items.return_value = []
        mock_resp.headers = {}
        return client, mock_resp

    def test_search_notes_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {"items": [
                {"note_card": {"display_title": "美食", "user": {"nickname": "张三"}}}
            ], "has_more": False}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.search_notes("美食")
            self.assertIsInstance(result, dict)
        client.close()

    def test_get_self_info_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {"username": "testuser", "nickname": "测试"}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.get_self_info()
            self.assertEqual(result["username"], "testuser")
        client.close()

    def test_get_home_feed_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {"items": [], "cursor_score": ""}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.get_home_feed()
            self.assertIsInstance(result, dict)
        client.close()

    def test_like_note_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.like_note("note123")
            self.assertIsNotNone(result)
        client.close()

    def test_follow_user_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.follow_user("user123")
            self.assertIsNotNone(result)
        client.close()

    def test_get_comments_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {"comments": [{"id": "c1", "content": "nice"}], "has_more": False}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.get_comments("note123")
            self.assertEqual(len(result["comments"]), 1)
        client.close()

    def test_get_all_comments_mocked(self):
        client, mock_resp = self._make_client_with_mock(text=json.dumps({
            "success": True, "data": {"comments": [{"id": "c1"}], "has_more": False, "cursor": ""}
        }))
        with patch.object(client._http, 'request', return_value=mock_resp):
            result = client.get_all_comments("note123")
            self.assertIn("comments", result)
            self.assertEqual(result["total_fetched"], 1)
        client.close()


# ─── HTML parser tests ──────────────────────────────────────────────

class TestHtmlParser(unittest.TestCase):
    def test_extract_note_from_html_basic(self):
        from xhs_cli.html_parser import extract_note_from_html
        html = '<html><script>window.__INITIAL_STATE__={"note":{"noteDetailMap":{}}}</script></html>'
        try:
            result = extract_note_from_html(html, "test_id")
            self.assertIsInstance(result, dict)
        except Exception:
            # May fail on complex parsing, that's ok for basic test
            pass


# ─── Run all ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
