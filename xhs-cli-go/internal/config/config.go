package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const (
	ConfigDirName    = ".xiaohongshu-cli"
	CookieFile     = "cookies.json"
	TokenCacheFile = "token_cache.json"
	IndexCacheFile = "index_cache.json"
	SearchSessionsFile = "search_sessions.json"
	CookieTTLDays = 7
)

// CookieData represents the cookies stored in cookies.json
type CookieData struct {
	A1         string `json:"a1"`
	WebSession string `json:"web_session"`
	SavedAt    float64 `json:"saved_at"`
	// Additional cookies may be present
	Extra map[string]string `json:"-"`
}

// LoadSavedCookies loads cookies from ~/.xiaohongshu-cli/cookies.json
func LoadSavedCookies() (map[string]string, error) {
	cookiePath, err := GetCookiePath()
	if err != nil {
		return nil, err
	}

	if _, err := os.Stat(cookiePath); os.IsNotExist(err) {
		return nil, fmt.Errorf("cookie file not found: %s", cookiePath)
	}

	data, err := os.ReadFile(cookiePath)
	if err != nil {
		return nil, fmt.Errorf("failed to read cookie file: %w", err)
	}

	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("failed to parse cookie file: %w", err)
	}

	cookies := make(map[string]string, len(raw))
	for k, v := range raw {
		// Try string first, then coerce numbers to strings
		var s string
		if err := json.Unmarshal(v, &s); err == nil {
			cookies[k] = s
		} else {
			// Handle numeric values (e.g. saved_at timestamp)
			cookies[k] = string(v)
		}
	}

	if cookies["a1"] == "" {
		return nil, fmt.Errorf("no 'a1' cookie found")
	}

	return cookies, nil
}

// SaveCookies saves cookies to ~/.xiaohongshu-cli/cookies.json
func SaveCookies(cookies map[string]string) error {
	cookiePath, err := GetCookiePath()
	if err != nil {
		return err
	}

	// Add saved_at timestamp
	cookies["saved_at"] = fmt.Sprintf("%f", float64(time.Now().Unix()))

	data, err := json.MarshalIndent(cookies, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal cookies: %w", err)
	}

	if err := os.WriteFile(cookiePath, data, 0600); err != nil {
		return fmt.Errorf("failed to write cookie file: %w", err)
	}

	return nil
}

// ClearCookies removes the saved cookies file
func ClearCookies() error {
	cookiePath, err := GetCookiePath()
	if err != nil {
		return err
	}

	if err := os.Remove(cookiePath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("failed to remove cookie file: %w", err)
	}

	return nil
}

// GetConfigDir returns or creates the config directory
func GetConfigDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %w", err)
	}

	configDir := filepath.Join(home, ConfigDirName)
	if err := os.MkdirAll(configDir, 0700); err != nil {
		return "", fmt.Errorf("failed to create config directory: %w", err)
	}

	return configDir, nil
}

// GetCookiePath returns the path to the cookies file
func GetCookiePath() (string, error) {
	configDir, err := GetConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(configDir, CookieFile), nil
}

// GetTokenCachePath returns the path to the token cache file
func GetTokenCachePath() (string, error) {
	configDir, err := GetConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(configDir, TokenCacheFile), nil
}

// GetIndexCachePath returns the path to the index cache file
func GetIndexCachePath() (string, error) {
	configDir, err := GetConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(configDir, IndexCacheFile), nil
}

// GetSearchSessionsPath returns the path to the search sessions file
func GetSearchSessionsPath() (string, error) {
	configDir, err := GetConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(configDir, SearchSessionsFile), nil
}

// CookiesToString converts a cookie map to a Cookie header string
func CookiesToString(cookies map[string]string) string {
	result := ""
	first := true
	for k, v := range cookies {
		if k == "saved_at" {
			continue
		}
		if !first {
			result += "; "
		}
		result += k + "=" + v
		first = false
	}
	return result
}
