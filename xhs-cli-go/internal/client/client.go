package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"math/rand"
	"net/http"
	"net/http/cookiejar"
	"strconv"
	"time"

	"xhs-cli-go/internal/config"
	"xhs-cli-go/internal/constants"
	"xhs-cli-go/internal/signing"
)

type XhsClient struct {
	cookies          map[string]string
	httpClient       *http.Client
	lastRequestTime  int64
	requestDelay     float64
	baseDelay        float64
	maxRetries       int
	verifyCount      int
	requestCount     int
}

func NewXhsClient(cookies map[string]string) *XhsClient {
	jar, _ := cookiejar.New(nil)
	return &XhsClient{
		cookies:      cookies,
		httpClient:   &http.Client{Jar: jar, Timeout: 30 * time.Second},
		requestDelay: 1.0,
		baseDelay:    1.0,
		maxRetries:   3,
	}
}

func (c *XhsClient) Close() {}

func (c *XhsClient) baseHeaders() map[string]string {
	return map[string]string{
		"user-agent":         constants.UserAgent,
		"content-type":       "application/json;charset=UTF-8",
		"cookie":             config.CookiesToString(c.cookies),
		"origin":             constants.HomeURL,
		"referer":            constants.HomeURL + "/",
		"sec-ch-ua":          fmt.Sprintf(`"Not:A-Brand";v="99", "Google Chrome";v="%s", "Chromium";v="%s"`, constants.ChromeVersion, constants.ChromeVersion),
		"sec-ch-ua-mobile":   "?0",
		"sec-ch-ua-platform": `"macOS"`,
		"sec-fetch-dest":     "empty",
		"sec-fetch-mode":     "cors",
		"sec-fetch-site":     "same-site",
		"accept":             "application/json, text/plain, */*",
		"accept-language":    "zh-CN,zh;q=0.9,en;q=0.8",
		"dnt":                "1",
		"priority":           "u=1, i",
	}
}

func (c *XhsClient) rateLimitDelay() {
	if c.requestDelay <= 0 {
		return
	}
	elapsed := time.Now().UnixMilli() - c.lastRequestTime
	elapsedSec := float64(elapsed) / 1000.0
	if elapsedSec < c.requestDelay {
		jitter := math.Max(0, rand.NormFloat64()*0.15+0.3)
		if rand.Float64() < 0.05 {
			jitter += 2.0 + rand.Float64()*3.0
		}
		sleepMs := (c.requestDelay-elapsedSec+jitter)*1000 - float64(elapsed)
		if sleepMs > 0 {
			time.Sleep(time.Duration(sleepMs) * time.Millisecond)
		}
	}
	c.lastRequestTime = time.Now().UnixMilli()
	c.requestCount++
}

func (c *XhsClient) handleResponse(resp *http.Response) (map[string]interface{}, error) {
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 461 || resp.StatusCode == 471 {
		c.verifyCount++
		cooldown := math.Min(30, float64(5*int(math.Pow(2, float64(c.verifyCount-1)))))
		c.requestDelay = math.Max(c.requestDelay, c.baseDelay*2)
		time.Sleep(time.Duration(cooldown) * time.Second)
		return nil, fmt.Errorf("captcha required (status %d)", resp.StatusCode)
	}

	c.verifyCount = 0

	if len(body) == 0 {
		return nil, nil
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("non-JSON response: %s", string(body[:minLen(len(body), 200)]))
	}

	if success, ok := result["success"].(bool); ok && success {
		if data, ok := result["data"]; ok {
			if dataMap, ok := data.(map[string]interface{}); ok {
				return dataMap, nil
			}
			return result, nil
		}
		return result, nil
	}

	if code, ok := result["code"].(float64); ok {
		switch int(code) {
		case 300012:
			return nil, fmt.Errorf("IP blocked by XHS")
		case 300015:
			return nil, fmt.Errorf("signature error")
		case -100:
			return nil, fmt.Errorf("session expired")
		}
	}

	return nil, fmt.Errorf("API error: %s", string(body[:minLen(len(body), 300)]))
}

func (c *XhsClient) doRequestWithRetry(method, url string, headers map[string]string, body io.Reader) (*http.Response, error) {
	c.rateLimitDelay()
	var lastErr error

	for attempt := 0; attempt < c.maxRetries; attempt++ {
		req, err := http.NewRequest(method, url, body)
		if err != nil {
			return nil, err
		}
		for k, v := range headers {
			req.Header.Set(k, v)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = err
			wait := time.Duration(math.Pow(2, float64(attempt))) * time.Second
			time.Sleep(wait)
			continue
		}

		if resp.StatusCode == 429 || resp.StatusCode >= 500 {
			resp.Body.Close()
			lastErr = fmt.Errorf("HTTP %d", resp.StatusCode)
			wait := time.Duration(math.Pow(2, float64(attempt))) * time.Second
			time.Sleep(wait)
			continue
		}

		return resp, nil
	}

	return nil, fmt.Errorf("request failed after %d retries: %v", c.maxRetries, lastErr)
}

func (c *XhsClient) mainAPIGet(uri string, params map[string]interface{}) (map[string]interface{}, error) {
	signHeaders, _ := signing.SignMainAPI("GET", uri, c.cookies, params, nil)
	fullURI := signing.BuildGetURI(uri, params)
	apiURL := constants.EdithHost + fullURI

	headers := c.baseHeaders()
	headers["x-s"] = signHeaders.XS
	headers["x-s-common"] = signHeaders.XSCommon
	headers["x-t"] = signHeaders.XT
	headers["x-b3-traceid"] = signHeaders.XB3TraceID
	headers["x-xray-traceid"] = signHeaders.XXrayTraceID

	resp, err := c.doRequestWithRetry("GET", apiURL, headers, nil)
	if err != nil {
		return nil, err
	}
	return c.handleResponse(resp)
}

func (c *XhsClient) mainAPIPost(uri string, data map[string]interface{}, headerOverrides map[string]string) (map[string]interface{}, error) {
	signHeaders, _ := signing.SignMainAPI("POST", uri, c.cookies, nil, data)
	apiURL := constants.EdithHost + uri

	headers := c.baseHeaders()
	headers["x-s"] = signHeaders.XS
	headers["x-s-common"] = signHeaders.XSCommon
	headers["x-t"] = signHeaders.XT
	headers["x-b3-traceid"] = signHeaders.XB3TraceID
	headers["x-xray-traceid"] = signHeaders.XXrayTraceID
	for k, v := range headerOverrides {
		headers[k] = v
	}

	jsonData, _ := json.Marshal(data)
	resp, err := c.doRequestWithRetry("POST", apiURL, headers, bytes.NewReader(jsonData))
	if err != nil {
		return nil, err
	}
	return c.handleResponse(resp)
}

func (c *XhsClient) creatorGet(uri string, params map[string]interface{}) (map[string]interface{}, error) {
	fullURI := signing.BuildGetURI(uri, params)
	a1 := c.cookies["a1"]
	xs, xt := signing.SignCreator("url="+fullURI, nil, a1)
	apiURL := constants.CreatorHost + fullURI

	headers := c.baseHeaders()
	headers["x-s"] = xs
	headers["x-t"] = xt
	headers["origin"] = constants.CreatorHost
	headers["referer"] = constants.CreatorHost + "/"

	resp, err := c.doRequestWithRetry("GET", apiURL, headers, nil)
	if err != nil {
		return nil, err
	}
	return c.handleResponse(resp)
}

func (c *XhsClient) creatorPost(uri string, data map[string]interface{}) (map[string]interface{}, error) {
	a1 := c.cookies["a1"]
	xs, xt := signing.SignCreator("url="+uri, data, a1)
	apiURL := constants.CreatorHost + uri

	headers := c.baseHeaders()
	headers["x-s"] = xs
	headers["x-t"] = xt
	headers["origin"] = constants.CreatorHost
	headers["referer"] = constants.CreatorHost + "/"

	jsonData, _ := json.Marshal(data)
	resp, err := c.doRequestWithRetry("POST", apiURL, headers, bytes.NewReader(jsonData))
	if err != nil {
		return nil, err
	}
	return c.handleResponse(resp)
}

// ─── Auth Endpoints ────────────────────────────────────────────────

func (c *XhsClient) GetSelfInfo() (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v2/user/me", nil)
}

func (c *XhsClient) LoginActivate() (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/login/activate", map[string]interface{}{}, nil)
}

// ─── Reading Endpoints ─────────────────────────────────────────────

func (c *XhsClient) GetUserInfo(userID string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/user/otherinfo", map[string]interface{}{
		"target_user_id": userID,
	})
}

func (c *XhsClient) GetUserNotes(userID, cursor string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/user_posted", map[string]interface{}{
		"num":          30,
		"cursor":       cursor,
		"user_id":      userID,
		"image_scenes": "FD_WM_WEBP",
	})
}

func (c *XhsClient) SearchNotes(keyword string, page, pageSize int, sort string, noteType int) (map[string]interface{}, error) {
	searchID := signing.GenerateSearchID()
	return c.mainAPIPost("/api/sns/web/v1/search/notes", map[string]interface{}{
		"keyword":    keyword,
		"page":       page,
		"page_size":  pageSize,
		"search_id":  searchID,
		"sort":       sort,
		"note_type":  noteType,
		"ext_flags":  []interface{}{},
		"filters":    defaultSearchFilters(),
		"geo":        "",
		"image_formats": []string{"jpg", "webp", "avif"},
	}, nil)
}

func (c *XhsClient) GetNoteByID(noteID, xsecToken, xsecSource string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/feed", map[string]interface{}{
		"source_note_id": noteID,
		"image_formats":  []string{"jpg", "webp", "avif"},
		"extra":          map[string]interface{}{"need_body_topic": "1"},
		"xsec_source":    xsecSource,
		"xsec_token":     xsecToken,
	}, nil)
}

func (c *XhsClient) GetHomeFeed() (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/homefeed", map[string]interface{}{
		"cursor_score":        "",
		"num":                 40,
		"refresh_type":        1,
		"note_index":          0,
		"unread_begin_note_id": "",
		"unread_end_note_id":   "",
		"unread_note_count":    0,
		"category":             "homefeed_recommend",
		"search_key":           "",
		"need_num":             40,
		"image_scenes":         []string{"FD_PRV_WEBP", "FD_WM_WEBP"},
	}, nil)
}

func (c *XhsClient) GetHotFeed(category string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/homefeed", map[string]interface{}{
		"cursor_score":        "",
		"num":                 40,
		"refresh_type":        1,
		"note_index":          0,
		"unread_begin_note_id": "",
		"unread_end_note_id":   "",
		"unread_note_count":    0,
		"category":             category,
		"search_key":           "",
		"need_num":             40,
		"image_scenes":         []string{"FD_PRV_WEBP", "FD_WM_WEBP"},
	}, nil)
}

func (c *XhsClient) GetComments(noteID, cursor, xsecToken string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v2/comment/page", map[string]interface{}{
		"note_id":       noteID,
		"cursor":        cursor,
		"top_comment_id": "",
		"image_formats": "jpg,webp,avif",
		"xsec_token":    xsecToken,
	})
}

func (c *XhsClient) GetAllComments(noteID, xsecToken string, maxPages int) (map[string]interface{}, error) {
	var allComments []interface{}
	cursor := ""
	pages := 0

	for pages < maxPages {
		data, err := c.GetComments(noteID, cursor, xsecToken)
		if err != nil {
			return nil, err
		}
		if data == nil {
			break
		}

		comments, _ := data["comments"].([]interface{})
		allComments = append(allComments, comments...)
		pages++

		hasMore, _ := data["has_more"].(bool)
		nextCursor, _ := data["cursor"].(string)
		if !hasMore || nextCursor == "" {
			break
		}
		cursor = nextCursor
	}

	return map[string]interface{}{
		"comments":      allComments,
		"has_more":      false,
		"cursor":        "",
		"total_fetched": len(allComments),
		"pages_fetched": pages,
	}, nil
}

func (c *XhsClient) GetSubComments(noteID, rootCommentID string, num int, cursor string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v2/comment/sub/page", map[string]interface{}{
		"note_id":          noteID,
		"root_comment_id":  rootCommentID,
		"num":              num,
		"cursor":           cursor,
	})
}

// ─── Interaction Endpoints ─────────────────────────────────────────

func (c *XhsClient) LikeNote(noteID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/note/like", map[string]interface{}{
		"note_oid": noteID,
	}, nil)
}

func (c *XhsClient) UnlikeNote(noteID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/note/dislike", map[string]interface{}{
		"note_oid": noteID,
	}, nil)
}

func (c *XhsClient) FavoriteNote(noteID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/note/collect", map[string]interface{}{
		"note_id": noteID,
	}, nil)
}

func (c *XhsClient) UnfavoriteNote(noteID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/note/uncollect", map[string]interface{}{
		"note_ids": noteID,
	}, nil)
}

func (c *XhsClient) PostComment(noteID, content string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/comment/post", map[string]interface{}{
		"note_id":    noteID,
		"content":    content,
		"at_users":   []interface{}{},
	}, nil)
}

func (c *XhsClient) ReplyComment(noteID, targetCommentID, content string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/comment/post", map[string]interface{}{
		"note_id":           noteID,
		"content":           content,
		"target_comment_id": targetCommentID,
		"at_users":          []interface{}{},
	}, nil)
}

func (c *XhsClient) DeleteComment(noteID, commentID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/comment/delete", map[string]interface{}{
		"note_id":     noteID,
		"comment_id":  commentID,
	}, nil)
}

// ─── Social Endpoints ──────────────────────────────────────────────

func (c *XhsClient) FollowUser(userID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/user/follow", map[string]interface{}{
		"target_user_id": userID,
	}, nil)
}

func (c *XhsClient) UnfollowUser(userID string) (map[string]interface{}, error) {
	return c.mainAPIPost("/api/sns/web/v1/user/unfollow", map[string]interface{}{
		"target_user_id": userID,
	}, nil)
}

func (c *XhsClient) GetUserFavorites(userID, cursor string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v2/note/collect/page", map[string]interface{}{
		"user_id": userID,
		"cursor":  cursor,
		"num":     30,
	})
}

func (c *XhsClient) GetUserLikes(userID, cursor string) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/note/like/page", map[string]interface{}{
		"user_id": userID,
		"cursor":  cursor,
		"num":     30,
	})
}

// ─── Notification Endpoints ────────────────────────────────────────

func (c *XhsClient) GetUnreadCount() (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/unread_count", nil)
}

func (c *XhsClient) GetNotificationMentions(cursor string, num int) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/you/mentions", map[string]interface{}{
		"num":    num,
		"cursor": cursor,
	})
}

func (c *XhsClient) GetNotificationLikes(cursor string, num int) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/you/likes", map[string]interface{}{
		"num":    num,
		"cursor": cursor,
	})
}

func (c *XhsClient) GetNotificationConnections(cursor string, num int) (map[string]interface{}, error) {
	return c.mainAPIGet("/api/sns/web/v1/you/connections", map[string]interface{}{
		"num":    num,
		"cursor": cursor,
	})
}

// ─── Creator Endpoints ─────────────────────────────────────────────

func (c *XhsClient) SearchTopics(keyword string) (map[string]interface{}, error) {
	return c.creatorPost("/web_api/sns/v1/search/topic", map[string]interface{}{
		"keyword": keyword,
		"suggest_topic_request": map[string]interface{}{
			"title": "",
			"desc":  "",
		},
		"page": map[string]interface{}{"page_size": 20, "page": 1},
	})
}

func (c *XhsClient) SearchUsers(keyword string) (map[string]interface{}, error) {
	return c.creatorPost("/web_api/sns/v1/search/user_info", map[string]interface{}{
		"keyword":    keyword,
		"search_id":  strconv.FormatInt(time.Now().UnixMilli(), 10),
		"page":       map[string]interface{}{"page_size": 20, "page": 1},
	})
}

func (c *XhsClient) DeleteNote(noteID string) (map[string]interface{}, error) {
	return c.creatorPost("/api/galaxy/creator/note/delete", map[string]interface{}{
		"note_id": noteID,
	})
}

func (c *XhsClient) GetCreatorNoteList(tab, page int) (map[string]interface{}, error) {
	return c.creatorGet("/api/galaxy/v2/creator/note/user/posted", map[string]interface{}{
		"tab":  tab,
		"page": page,
	})
}

func defaultSearchFilters() []interface{} {
	return []interface{}{
		map[string]interface{}{"tags": []string{"general"}, "type": "sort_type"},
		map[string]interface{}{"tags": []string{"不限"}, "type": "filter_note_type"},
		map[string]interface{}{"tags": []string{"不限"}, "type": "filter_note_time"},
		map[string]interface{}{"tags": []string{"不限"}, "type": "filter_note_range"},
		map[string]interface{}{"tags": []string{"不限"}, "type": "filter_pos_distance"},
	}
}

func minLen(a, b int) int {
	if a < b {
		return a
	}
	return b
}
