package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"

	"github.com/spf13/cobra"
)

func NewReadCmd() *cobra.Command {
	var xsecToken string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "read [id_or_url_or_index]",
		Short: "Read a note by ID, URL, or short index",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			noteID, token, source := resolveNoteRef(input, xsecToken)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetNoteByID(noteID, token, source)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to read note: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVar(&xsecToken, "xsec-token", "", "Explicit xsec_token")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewCommentsCmd() *cobra.Command {
	var xsecToken string
	var cursor string
	var fetchAll bool
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "comments [id_or_url_or_index]",
		Short: "View comments on a note",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			noteID, token, _ := resolveNoteRef(input, xsecToken)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			if fetchAll {
				result, err := c.GetAllComments(noteID, token, 20)
				if err != nil {
					PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get all comments: %v", err)), format)
					return
				}
				PrintEnvelope(SuccessEnvelope(result), format)
				return
			}

			result, err := c.GetComments(noteID, cursor, token)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get comments: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVar(&xsecToken, "xsec-token", "", "Explicit xsec_token")
	cmd.Flags().StringVar(&cursor, "cursor", "", "Comment page cursor")
	cmd.Flags().BoolVar(&fetchAll, "all", false, "Fetch ALL comments (auto-paginate)")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewSubCommentsCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "sub-comments [note_id] [comment_id]",
		Short: "View replies to a specific comment",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			noteID := args[0]
			commentID := args[1]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetSubComments(noteID, commentID, 30, "")
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get sub-comments: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewUserCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "user [user_id]",
		Short: "View user profile info",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			userID := args[0]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetUserInfo(userID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get user info: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewUserPostsCmd() *cobra.Command {
	var cursor string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "user-posts [user_id]",
		Short: "List a user's published notes",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			userID := args[0]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetUserNotes(userID, cursor)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get user posts: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVar(&cursor, "cursor", "", "Pagination cursor")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewFeedCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "feed",
		Short: "Browse the recommendation feed",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetHomeFeed()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get feed: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewHotCmd() *cobra.Command {
	var category string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "hot",
		Short: "Browse hot/trending notes by category",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			cat := category
			if cat == "" || cat == "food" {
				cat = "homefeed.food_v3"
			} else {
				cat = "homefeed." + cat + "_v3"
			}

			result, err := c.GetHotFeed(cat)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get hot feed: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVarP(&category, "category", "c", "food", "Category: fashion, food, cosmetics, movie, career, love, home, gaming, travel, fitness")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewMyNotesCmd() *cobra.Command {
	var page int
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "my-notes",
		Short: "List your own published notes",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetCreatorNoteList(0, page)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get my notes: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().IntVar(&page, "page", 0, "Page number")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

// resolveNoteRef resolves a note reference (ID, URL, or short index) to note_id + xsec_token
func resolveNoteRef(input, explicitToken string) (string, string, string) {
	// Try as URL
	if len(input) > 20 && (input[:4] == "http" || input[:5] == "https") {
			noteID, token := parseNoteURL(input)
			return noteID, token, "pc_feed"
	}

	// Try as numeric index (1-based)
	if idx, err := strconv.Atoi(input); err == nil && idx >= 1 {
		if noteID, token := lookupIndexCache(idx); noteID != "" {
			return noteID, explicitToken, token
		}
	}

	// Use as note ID
	return input, explicitToken, "pc_feed"
}

func parseNoteURL(urlStr string) (string, string) {
	// Extract note_id from URL like https://www.xiaohongshu.com/explore/NOTE_ID?xsec_token=TOKEN
	noteID := ""
	token := ""

	// Simple URL parsing
	parts := splitURL(urlStr)
	if len(parts) >= 2 {
		noteID = parts[len(parts)-1]
		// Check if there's a query for xsec_token
		for i, c := range noteID {
			if c == '?' {
				noteID = noteID[:i]
				break
			}
		}
	}

	// Extract xsec_token from query
	if idx := indexOf(urlStr, "xsec_token="); idx >= 0 {
		start := idx + len("xsec_token=")
		end := start
		for end < len(urlStr) && urlStr[end] != '&' && urlStr[end] != '#' {
			end++
		}
		token = urlStr[start:end]
	}

	return noteID, token
}

func splitURL(urlStr string) []string {
	var result []string
	start := 0
	inQuery := false
	for i, c := range urlStr {
		if c == '?' {
			inQuery = true
		}
		if c == '/' && !inQuery {
			if i > start {
				result = append(result, urlStr[start:i])
			}
			start = i + 1
		}
	}
	if start < len(urlStr) && !inQuery {
		result = append(result, urlStr[start:])
	}
	return result
}

func indexOf(s, substr string) int {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}

func lookupIndexCache(idx int) (string, string) {
	home, _ := os.UserHomeDir()
	data, err := os.ReadFile(home + "/.xiaohongshu-cli/index_cache.json")
	if err != nil {
		return "", ""
	}

	var entries []map[string]string
	if err := json.Unmarshal(data, &entries); err != nil {
		return "", ""
	}

	if idx < 1 || idx > len(entries) {
		return "", ""
	}

	entry := entries[idx-1]
	return entry["note_id"], entry["xsec_token"]
}
