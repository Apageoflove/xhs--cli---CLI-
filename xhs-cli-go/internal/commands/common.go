package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"xhs-cli-go/internal/client"
	"xhs-cli-go/internal/config"
)

type OutputFormat string

const (
	OutputFormatAuto OutputFormat = "auto"
	OutputFormatJSON OutputFormat = "json"
	OutputFormatYAML OutputFormat = "yaml"
	OutputFormatRich OutputFormat = "rich"
)

type Envelope struct {
	OK            bool        `json:"ok"`
	SchemaVersion string      `json:"schema_version"`
	Data          interface{} `json:"data,omitempty"`
	Error         string      `json:"error,omitempty"`
}

func SuccessEnvelope(data interface{}) Envelope {
	return Envelope{OK: true, SchemaVersion: "1", Data: data}
}

func ErrorEnvelope(err string) Envelope {
	return Envelope{OK: false, SchemaVersion: "1", Error: err}
}

func PrintEnvelope(env Envelope, format OutputFormat) {
	isTTY := isTerminal()

	var outputFormat OutputFormat
	switch format {
	case OutputFormatJSON:
		outputFormat = OutputFormatJSON
	case OutputFormatYAML:
		outputFormat = OutputFormatYAML
	default:
		if isTTY {
			outputFormat = OutputFormatRich
		} else {
			outputFormat = OutputFormatYAML
		}
	}

	switch outputFormat {
	case OutputFormatJSON:
		data, _ := json.MarshalIndent(env, "", "  ")
		fmt.Println(string(data))
	case OutputFormatYAML:
		fmt.Printf("ok: %v\n", env.OK)
		fmt.Printf("schema_version: \"%s\"\n", env.SchemaVersion)
		if env.Error != "" {
			fmt.Printf("error: %s\n", env.Error)
		}
		if env.Data != nil {
			fmt.Println("data:")
			printYAMLValue(env.Data, "  ")
		}
	default:
		if env.OK {
			fmt.Println("✓ Success")
			if env.Data != nil {
				printRichData(env.Data)
			}
		} else {
			fmt.Printf("✗ Error: %s\n", env.Error)
		}
	}
}

func printYAMLValue(v interface{}, indent string) {
	switch val := v.(type) {
	case map[string]interface{}:
		for k, v2 := range val {
			switch subVal := v2.(type) {
			case map[string]interface{}:
				fmt.Printf("%s%s:\n", indent, k)
				printYAMLValue(subVal, indent+"  ")
			case []interface{}:
				fmt.Printf("%s%s:\n", indent, k)
				for _, item := range subVal {
					fmt.Printf("%s- ", indent)
					printYAMLInline(item, indent+"  ")
				}
			default:
				fmt.Printf("%s%s: %v\n", indent, k, v2)
			}
		}
	case []interface{}:
		for _, item := range val {
			fmt.Printf("%s- ", indent)
			printYAMLInline(item, indent+"  ")
		}
	default:
		fmt.Printf("%s%v\n", indent, val)
	}
}

func printYAMLInline(v interface{}, indent string) {
	switch val := v.(type) {
	case map[string]interface{}:
		fmt.Println()
		for k, v2 := range val {
			fmt.Printf("%s%s: %v\n", indent, k, v2)
		}
	default:
		fmt.Printf("%v\n", v)
	}
}

func printRichData(data interface{}) {
	if dataMap, ok := data.(map[string]interface{}); ok {
		if user, ok := dataMap["user"].(map[string]interface{}); ok {
			printUserInfo(user)
			return
		}
		if items, ok := dataMap["items"].([]interface{}); ok {
			fmt.Printf("Found %d results\n", len(items))
			for i, item := range items {
				if itemMap, ok := item.(map[string]interface{}); ok {
					noteCard, _ := itemMap["note_card"].(map[string]interface{})
					title := ""
					if noteCard != nil {
						if t, ok := noteCard["title"].(string); ok {
							title = t
						}
						if title == "" {
							if t, ok := noteCard["display_title"].(string); ok {
								title = t
							}
						}
					}
					if title == "" {
						title = "(untitled)"
					}
					fmt.Printf("%d. %s\n", i+1, title)
				}
			}
			return
		}
		if comments, ok := dataMap["comments"].([]interface{}); ok {
			fmt.Printf("Comments (%d):\n", len(comments))
			for i, c := range comments {
				if cm, ok := c.(map[string]interface{}); ok {
					content, _ := cm["content"].(string)
					userInfo, _ := cm["user_info"].(map[string]interface{})
					nickname := ""
					if userInfo != nil {
						nickname, _ = userInfo["nickname"].(string)
					}
					fmt.Printf("%d. [%s] %s\n", i+1, nickname, content)
				}
			}
			return
		}
		if notes, ok := dataMap["notes"].([]interface{}); ok {
			fmt.Printf("Notes (%d):\n", len(notes))
			for i, n := range notes {
				if nm, ok := n.(map[string]interface{}); ok {
					title, _ := nm["title"].(string)
					if title == "" {
						title = "(untitled)"
					}
					fmt.Printf("%d. %s\n", i+1, title)
				}
			}
			return
		}
	}
	dataJSON, _ := json.MarshalIndent(data, "", "  ")
	fmt.Println(string(dataJSON))
}

func printUserInfo(user map[string]interface{}) {
	fmt.Println("User Info:")
	if nickname, ok := user["nickname"].(string); ok && nickname != "" {
		fmt.Printf("  昵称: %s\n", nickname)
	}
	if redID, ok := user["red_id"].(string); ok && redID != "" {
		fmt.Printf("  小红书号: %s\n", redID)
	}
	if ip, ok := user["ip_location"].(string); ok && ip != "" {
		fmt.Printf("  IP 属地: %s\n", ip)
	}
	if desc, ok := user["desc"].(string); ok && desc != "" {
		fmt.Printf("  简介: %s\n", desc)
	}
	if fans := getFloat(user, "fans"); fans > 0 {
		fmt.Printf("  粉丝: %.0f\n", fans)
	}
	if follows := getFloat(user, "follows"); follows > 0 {
		fmt.Printf("  关注: %.0f\n", follows)
	}
	if liked := getFloat(user, "liked"); liked > 0 {
		fmt.Printf("  获赞: %.0f\n", liked)
	}
}

func isTerminal() bool {
	fileInfo, _ := os.Stdout.Stat()
	return (fileInfo.Mode() & os.ModeCharDevice) != 0
}

func GetClient() (*client.XhsClient, error) {
	cookies, err := config.LoadSavedCookies()
	if err != nil {
		return nil, fmt.Errorf("failed to load cookies: %w\nRun 'xhs login' first", err)
	}
	return client.NewXhsClient(cookies), nil
}

func NormalizeUserInfo(data map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})

	if userInfo, ok := data["user_info"].(map[string]interface{}); ok {
		data = userInfo
	}

	result["id"] = getString(data, "user_id")
	result["nickname"] = getString(data, "nickname")
	result["red_id"] = getString(data, "red_id")
	result["avatar"] = getString(data, "image")
	result["desc"] = getString(data, "desc")
	result["ip_location"] = getString(data, "ip_location")
	result["gender"] = getFloat(data, "gender")
	result["fans"] = getFloat(data, "fans")
	result["follows"] = getFloat(data, "follows")
	result["liked"] = getFloat(data, "liked")
	result["guest"] = getString(data, "nickname") == ""

	return result
}

func getString(m map[string]interface{}, key string) string {
	if v, ok := m[key].(string); ok {
		return v
	}
	return ""
}

func getFloat(m map[string]interface{}, key string) float64 {
	if v, ok := m[key].(float64); ok {
		return v
	}
	return 0
}

func getOutputFormat(asJSON, asYAML bool) OutputFormat {
	if asJSON {
		return OutputFormatJSON
	}
	if asYAML {
		return OutputFormatYAML
	}
	if envFormat := os.Getenv("OUTPUT"); envFormat != "" {
		switch envFormat {
		case "json":
			return OutputFormatJSON
		case "yaml":
			return OutputFormatYAML
		case "rich":
			return OutputFormatRich
		}
	}
	return OutputFormatAuto
}

func ParseSort(sort string) string {
	switch strings.ToLower(sort) {
	case "popular":
		return "popularity_descending"
	case "latest":
		return "time_descending"
	default:
		return "general"
	}
}

func ParseNoteType(noteType string) int {
	switch strings.ToLower(noteType) {
	case "video":
		return 1
	case "image":
		return 2
	default:
		return 0
	}
}
