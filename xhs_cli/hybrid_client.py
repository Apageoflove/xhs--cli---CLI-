"""
Hybrid XHS client that uses xhs library's sign() for ALL API calls.

The xhs library's internal sign function works for both main and creator APIs.
We wrap it to create a drop-in replacement that fixes search.
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any

import httpx

from .constants import CHROME_VERSION, CREATOR_HOST, EDITH_HOST, HOME_URL, USER_AGENT
from .cookies import cookies_to_string
from .creator_signing import sign_creator
from .exceptions import (
    IpBlockedError,
    NeedVerifyError,
    SessionExpiredError,
    SignatureError,
    XhsApiError,
)

logger = logging.getLogger(__name__)

# Import xhs library's sign function
try:
    from xhs.help import sign as xhs_sign
    HAS_XHS_SIGN = True
except ImportError:
    HAS_XHS_SIGN = False
    logger.warning("xhs library not available, search may not work")


def _build_x_s_common(x_s: str, x_t: str, a1: str) -> str:
    """Build x-s-common header matching the format the API expects."""
    import urllib.parse

    def _mrc(e: str) -> int:
        import ctypes
        ie = [
            0, 1996959894, 3993919788, 2567524794, 124634137, 1886057615, 3915621685,
            2657392035, 249268274, 2044508324, 3772115230, 2547177864, 162941995,
            2125561021, 3887607047, 2428444049, 498536548, 1789927666, 4089016648,
            2227061214, 450548861, 1843258603, 4107580753, 2211677639, 325883990,
            1684777152, 4251122042, 2321926636, 335633487, 1661365465, 4195302755,
            2366115317, 997073096, 1281953886, 3579855332, 2724688242, 1006888145,
            1258607687, 3524101629, 2768942443, 901097722, 1119000684, 3686517206,
            2898065728, 853044451, 1172266101, 3705015759, 2882616665, 651767980,
            1373503546, 3369554304, 3218104598, 565507253, 1454621731, 3485111705,
            3099436303, 671266974, 1594198024, 3322730930, 2970347812, 795835527,
            1483230225, 3244367275, 3060149565, 1994146192, 31158534, 2563907772,
            4023717930, 1907459465, 112637215, 2680153253, 3904427059, 2013776290,
            251722036, 2517215374, 3775830040, 2137656763, 141376813, 2439277719,
            3865271297, 1802195444, 476864866, 2238001368, 4066508878, 1812370925,
            453092731, 2181625025, 4111451223, 1706088902, 314042704, 2344532202,
            4240017532, 1658658271, 366619977, 2362670323, 4224994405, 1303535960,
            984961486, 2747007092, 3569037538, 1256170817, 1037604311, 2765210733,
            3554079995, 1131014506, 879679996, 2909243462, 3663771856, 1141124467,
            855842277, 2852801631, 3708648649, 1342533948, 654459306, 3188396048,
            3373015174, 1466479909, 544179635, 3110523913, 3462522015, 1591671054,
            702138776, 2966460450, 3352799412, 1504918807, 783551873, 3082640443,
            3233442989, 3988292384, 2596254646, 62317068, 1957810842, 3939845945,
            2647816111, 81470997, 1943803523, 3814918930, 2489596804, 225274430,
            2053790376, 3826175755, 2466906013, 167816743, 2097651377, 4027552580,
            2265490386, 503444072, 1762050814, 4150417245, 2154129355, 426522225,
            1852507879, 4275313526, 2312317920, 282753626, 1742555852, 4189708143,
            2394877945, 397917763, 1622183637, 3604390888, 2714866558, 953729732,
            1340076626, 3518719985, 2797360999, 1068828381, 1219638859, 3624741850,
            2936675148, 906185462, 1090812512, 3747672003, 2825379669, 829329135,
            1181335161, 3412177804, 3160834842, 628085408, 1382605366, 3423369109,
            3138078467, 570562233, 1426400815, 3317316542, 2998733608, 733239954,
            1555261956, 3268935591, 3050360625, 752459403, 1541320221, 2607071920,
            3965973030, 1969922972, 40735498, 2617837225, 3943577151, 1913087877,
            83908371, 2512341634, 3803740692, 2075208622, 213261112, 2463272603,
            3855990285, 2094854071, 198958881, 2262029012, 4057260610, 1759359992,
            534414190, 2176718541, 4139329115, 1873836001, 414664567, 2282248934,
            4279200368, 1711684554, 285281116, 2405801727, 4167216745, 1634467795,
            376229701, 2685067896, 3608007406, 1308918612, 956543938, 2808555105,
            3495958263, 1231636301, 1047427035, 2932959818, 3654703836, 1088359270,
            936918000, 2847714899, 3736837829, 1202900863, 817233897, 3183342108,
            3401237130, 1404277552, 615818150, 3134207493, 3453421203, 1423857449,
            601450431, 3009837614, 3294710456, 1567103746, 711928724, 3020668471,
            3272380065, 1510334235, 755167117,
        ]
        o = -1
        for n in range(57):
            o = ie[(o & 255) ^ ord(e[n])] ^ (ctypes.c_uint32(o).value >> 8) & 0xFFFFFFFF
            if o > 0x7FFFFFFF:
                o -= 0x100000000
        return (o ^ -1 ^ 3988292384) & 0xFFFFFFFF
        if o > 0x7FFFFFFF:
            o -= 0x100000000
        return o

    common = {
        "s0": 5,
        "s1": "",
        "x0": "1",
        "x1": "4.2.6",
        "x2": "Linux",
        "x3": "xhs-pc-web",
        "x4": "4.86.0",
        "x5": a1,
        "x6": x_t,
        "x7": x_s,
        "x8": "",
        "x9": _mrc(x_t + x_s),
        "x10": 1,
        "x11": "normal",
    }
    payload = json.dumps(common, separators=(",", ":"), ensure_ascii=False)

    # Base64 encode
    lookup = "ZmsebBHQtNP+OwczNa/LpgG8yJq4K2WYj0DSfdikx3VT16I UlAFM9 7hECvuRX5"
    lookup = "ZmsebBHQtNP+OwczNa/LpgnG8yJq4K2WYj0DSfdikx3VT16I UlAFM9 7hECvuRX5"
    # Use proper base64
    import base64
    encoded = urllib.parse.quote(payload, safe="~()*!.'")
    raw_bytes = []
    i = 0
    while i < len(encoded):
        ch = encoded[i]
        if ch == "%":
            raw_bytes.append(int(encoded[i+1:i+3], 16))
            i += 3
        else:
            raw_bytes.append(ord(ch))
            i += 1

    return base64.b64encode(bytes(raw_bytes)).decode()


def _simple_sign(uri: str, data: dict | None, a1: str) -> dict[str, str]:
    """Generate signing headers using xhs library's sign function."""
    if not HAS_XHS_SIGN:
        raise SignatureError("xhs library sign function not available")

    result = xhs_sign(uri, data, a1=a1)
    return {
        "x-s": result["x-s"],
        "x-t": result["x-t"],
        "x-s-common": result["x-s-common"],
    }


class HybridXhsClient:
    """
    XHS API client that uses xhs library's sign() for ALL endpoints.

    This fixes the search API by using a proven signing implementation
    instead of the broken xhshow XYS_ signatures.
    """

    def __init__(
        self,
        cookies: dict[str, str],
        timeout: float = 30.0,
        request_delay: float = 1.0,
        max_retries: int = 3,
    ):
        self.cookies = dict(cookies)
        self._http = httpx.Client(timeout=timeout, follow_redirects=True)
        self._request_delay = request_delay
        self._base_request_delay = request_delay
        self._max_retries = max_retries
        self._last_request_time = 0.0
        self._verify_count = 0
        self._request_count = 0
        self._last_search_results: list[dict] = []

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─── Rate limiting ──────────────────────────────────────────

    def _rate_limit_delay(self) -> None:
        if self._request_delay <= 0:
            return
        elapsed = time.time() - self._last_request_time
        if elapsed < self._request_delay:
            jitter = max(0, random.gauss(0.3, 0.15))
            if random.random() < 0.05:
                jitter += random.uniform(2.0, 5.0)
            sleep_time = self._request_delay - elapsed + jitter
            logger.debug("Rate-limit delay: %.2fs", sleep_time)
            time.sleep(sleep_time)

    def _mark_request(self) -> None:
        self._last_request_time = time.time()
        self._request_count += 1

    # ─── Headers ────────────────────────────────────────────────

    def _base_headers(self) -> dict[str, str]:
        return {
            "user-agent": USER_AGENT,
            "content-type": "application/json;charset=UTF-8",
            "cookie": cookies_to_string(self.cookies),
            "origin": HOME_URL,
            "referer": f"{HOME_URL}/",
            "sec-ch-ua": f'"Not:A-Brand";v="99", "Google Chrome";v="{CHROME_VERSION}", "Chromium";v="{CHROME_VERSION}"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "dnt": "1",
            "priority": "u=1, i",
        }

    # ─── Response handling ──────────────────────────────────────

    def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.status_code in (461, 471):
            self._verify_count += 1
            cooldown = min(30, 5 * (2 ** (self._verify_count - 1)))
            logger.warning("Captcha triggered (count=%d), cooling down %.0fs", self._verify_count, cooldown)
            self._request_delay = max(self._request_delay, self._base_request_delay * 2)
            time.sleep(cooldown)
            raise NeedVerifyError(
                verify_type=resp.headers.get("verifytype", "unknown"),
                verify_uuid=resp.headers.get("verifyuuid", "unknown"),
            )

        self._verify_count = 0
        text = resp.text
        if not text:
            return None

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise XhsApiError(f"Non-JSON response: {text[:200]}") from None

        if data.get("success"):
            return data.get("data", data.get("success"))

        code = data.get("code")
        if code == 300012:
            raise IpBlockedError()
        if code == 300015:
            raise SignatureError()
        if code == -100:
            raise SessionExpiredError()

        raise XhsApiError(f"API error: {json.dumps(data)[:300]}", code=code, response=data)

    def _merge_response_cookies(self, resp: httpx.Response) -> None:
        for name, value in resp.cookies.items():
            if value:
                self.cookies[name] = value

    # ─── HTTP with retry ────────────────────────────────────────

    def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        self._rate_limit_delay()
        last_exc: Exception | None = None
        resp = None

        for attempt in range(self._max_retries):
            try:
                resp = self._http.request(method, url, **kwargs)
                self._merge_response_cookies(resp)
                self._mark_request()
                if resp.status_code in (429, 500, 502, 503, 504):
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning("HTTP %d from %s, retrying in %.1fs (attempt %d/%d)",
                                   resp.status_code, url[:80], wait, attempt + 1, self._max_retries)
                    time.sleep(wait)
                    continue
                return resp
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning("Network error: %s, retrying in %.1fs (attempt %d/%d)",
                               exc, wait, attempt + 1, self._max_retries)
                time.sleep(wait)

        if last_exc:
            raise XhsApiError(f"Request failed after {self._max_retries} retries: {last_exc}") from last_exc
        raise XhsApiError(f"Request failed after {self._max_retries} retries: HTTP {resp.status_code if resp else 'N/A'}")

    # ─── Signing ────────────────────────────────────────────────

    def _sign_main_api(self, method: str, uri: str, data: dict | None = None) -> dict[str, str]:
        """Sign a main API request using xhs library's proven sign function."""
        a1 = self.cookies.get("a1", "")
        return _simple_sign(uri, data, a1)

    def _sign_creator(self, uri: str, data: dict | None = None) -> dict[str, str]:
        """Sign a creator API request."""
        sign = sign_creator(f"url={uri}", data, self.cookies.get("a1", ""))
        return {"x-s": sign["x-s"], "x-t": sign["x-t"]}

    # ─── Main API methods ──────────────────────────────────────

    def _main_api_get(self, uri: str, params: dict | None = None) -> Any:
        sign_headers = self._sign_main_api("GET", uri)
        # Build full URL with params
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            full_uri = f"{uri}?{query}" if "?" not in uri else f"{uri}&{query}"
        else:
            full_uri = uri
        url = f"{EDITH_HOST}{full_uri}"
        logger.debug("GET %s", url)
        resp = self._request_with_retry("GET", url, headers={**self._base_headers(), **sign_headers})
        return self._handle_response(resp)

    def _main_api_post(self, uri: str, data: dict[str, Any], header_overrides: dict | None = None) -> Any:
        sign_headers = self._sign_main_api("POST", uri, data)
        url = f"{EDITH_HOST}{uri}"
        headers = {**self._base_headers(), **sign_headers}
        if header_overrides:
            headers.update(header_overrides)
        logger.debug("POST %s", url)
        body = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        resp = self._request_with_retry("POST", url, headers=headers, content=body)
        return self._handle_response(resp)

    # ─── Creator API methods ───────────────────────────────────

    def _creator_host(self, uri: str) -> str:
        return CREATOR_HOST if uri.startswith("/api/galaxy/") or uri.startswith("/web_api/") else EDITH_HOST

    def _creator_get(self, uri: str, params: dict | None = None) -> Any:
        sign_headers = self._sign_creator(uri)
        host = self._creator_host(uri)
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items())
            full_uri = f"{uri}?{query}" if "?" not in uri else f"{uri}&{query}"
        else:
            full_uri = uri
        url = f"{host}{full_uri}"
        headers = {
            **self._base_headers(),
            **sign_headers,
            "origin": CREATOR_HOST,
            "referer": f"{CREATOR_HOST}/",
        }
        logger.debug("Creator GET %s", url)
        resp = self._request_with_retry("GET", url, headers=headers)
        return self._handle_response(resp)

    def _creator_post(self, uri: str, data: dict[str, Any]) -> Any:
        sign_headers = self._sign_creator(uri, data)
        host = self._creator_host(uri)
        url = f"{host}{uri}"
        headers = {
            **self._base_headers(),
            **sign_headers,
            "origin": CREATOR_HOST,
            "referer": f"{CREATOR_HOST}/",
        }
        logger.debug("Creator POST %s", url)
        body = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        resp = self._request_with_retry("POST", url, headers=headers, content=body)
        return self._handle_response(resp)

    # ─── Public API endpoints ──────────────────────────────────

    def get_self_info(self) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v2/user/me")

    def get_user_info(self, user_id: str) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/user/otherinfo", {"target_user_id": user_id})

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/user_posted", {
            "num": 30, "cursor": cursor, "user_id": user_id, "image_scenes": "FD_WM_WEBP",
        })

    def search_notes(
        self, keyword: str, page: int = 1, page_size: int = 20,
        sort: str = "general", note_type: int = 0,
    ) -> Any:
        from xhs.help import get_search_id
        search_id = get_search_id()
        data = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "search_id": search_id,
            "sort": sort,
            "note_type": note_type,
        }
        result = self._main_api_post("/api/sns/web/v1/search/notes", data)
        if isinstance(result, dict) and "items" in result:
            self._last_search_results = result["items"]
        return result

    def search_users(self, keyword: str, page: int = 1, page_size: int = 20) -> Any:
        from xhs.help import get_search_id
        search_id = get_search_id()
        data = {
            "search_user_request": {
                "keyword": keyword,
                "search_id": search_id,
                "page": page,
                "page_size": page_size,
                "biz_type": "web_search_user",
                "request_id": f"{int(time.time())}-{int(time.time() * 1000)}",
            }
        }
        return self._main_api_post("/api/sns/web/v1/search/usersearch", data)

    def search_topics(self, keyword: str) -> dict[str, Any]:
        return self._creator_post("/web_api/sns/v1/search/topic", {
            "keyword": keyword,
            "suggest_topic_request": {"title": "", "desc": ""},
            "page": {"page_size": 20, "page": 1},
        })

    def get_note_by_id(self, note_id: str, xsec_token: str = "", xsec_source: str = "pc_feed") -> Any:
        data = {
            "source_note_id": note_id,
            "image_scenes": ["CRD_WM_WEBP"],
            "extra": {"need_body_topic": "1"},
        }
        return self._main_api_post("/api/sns/web/v1/feed", data)

    def get_home_feed(self, category: str = "homefeed_recommend") -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/homefeed", {
            "cursor_score": "", "num": 40, "refresh_type": 1,
            "note_index": 0, "unread_begin_note_id": "", "unread_end_note_id": "",
            "unread_note_count": 0, "category": category, "search_key": "",
            "need_num": 40, "image_scenes": ["FD_PRV_WEBP", "FD_WM_WEBP"],
        })

    def get_hot_feed(self, category: str = "homefeed.fashion_v3") -> dict[str, Any]:
        return self.get_home_feed(category=category)

    def get_comments(self, note_id: str, cursor: str = "") -> Any:
        return self._main_api_get("/api/sns/web/v2/comment/page", {
            "note_id": note_id, "cursor": cursor,
        })

    def get_all_comments(self, note_id: str, max_pages: int = 20) -> dict[str, Any]:
        all_comments = []
        cursor = ""
        for _ in range(max_pages):
            data = self.get_comments(note_id, cursor=cursor)
            if not isinstance(data, dict):
                break
            all_comments.extend(data.get("comments", []))
            if not data.get("has_more") or not data.get("cursor"):
                break
            cursor = data["cursor"]
        return {"comments": all_comments, "total_fetched": len(all_comments)}

    def get_sub_comments(self, note_id: str, root_comment_id: str, num: int = 30, cursor: str = "") -> Any:
        return self._main_api_get("/api/sns/web/v2/comment/sub/page", {
            "note_id": note_id, "root_comment_id": root_comment_id,
            "num": num, "cursor": cursor,
        })

    def like_note(self, note_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/note/like", {"note_oid": note_id})

    def unlike_note(self, note_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/note/dislike", {"note_oid": note_id})

    def favorite_note(self, note_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/note/collect", {"note_id": note_id})

    def unfavorite_note(self, note_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/note/uncollect", {"note_ids": note_id})

    def post_comment(self, note_id: str, content: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/comment/post", {
            "note_id": note_id, "content": content, "at_users": [],
        })

    def reply_comment(self, note_id: str, target_comment_id: str, content: str) -> Any:
        return self._main_api_post("/api/sns/web/v1/comment/post", {
            "note_id": note_id, "content": content,
            "target_comment_id": target_comment_id, "at_users": [],
        })

    def delete_comment(self, note_id: str, comment_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/comment/delete", {
            "note_id": note_id, "comment_id": comment_id,
        })

    def follow_user(self, user_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/user/follow", {"target_user_id": user_id})

    def unfollow_user(self, user_id: str) -> dict[str, Any]:
        return self._main_api_post("/api/sns/web/v1/user/unfollow", {"target_user_id": user_id})

    def get_user_favorites(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v2/note/collect/page", {
            "user_id": user_id, "cursor": cursor, "num": 30,
        })

    def get_user_likes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/note/like/page", {
            "user_id": user_id, "cursor": cursor, "num": 30,
        })

    def get_unread_count(self) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/unread_count", {})

    def get_notification_mentions(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/you/mentions", {"num": num, "cursor": cursor})

    def get_notification_likes(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/you/likes", {"num": num, "cursor": cursor})

    def get_notification_connections(self, cursor: str = "", num: int = 20) -> dict[str, Any]:
        return self._main_api_get("/api/sns/web/v1/you/connections", {"num": num, "cursor": cursor})

    def get_creator_note_list(self, tab: int = 0, page: int = 0) -> dict[str, Any]:
        return self._creator_get("/api/galaxy/v2/creator/note/user/posted", {"tab": tab, "page": page})

    def delete_note(self, note_id: str) -> dict[str, Any]:
        return self._creator_post("/api/galaxy/creator/note/delete", {"note_id": note_id})
