package commands

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

func NewSearchCmd() *cobra.Command {
	var sort string
	var noteType string
	var page int
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "search [keyword]",
		Short: "Search notes by keyword",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			keyword := args[0]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			sortVal := ParseSort(sort)
			typeVal := ParseNoteType(noteType)

			result, err := c.SearchNotes(keyword, page, 20, sortVal, typeVal)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Search failed: %v", err)), format)
				return
			}

			cacheSearchResults(result)
			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVar(&sort, "sort", "general", "Sort order: general, popular, latest")
	cmd.Flags().StringVar(&noteType, "type", "all", "Note type: all, video, image")
	cmd.Flags().IntVar(&page, "page", 1, "Page number")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewSearchUserCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "search-user [keyword]",
		Short: "Search for users by keyword",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			keyword := args[0]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.SearchUsers(keyword)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("User search failed: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewTopicsCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "topics [keyword]",
		Short: "Search for topics/hashtags",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			keyword := args[0]
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.SearchTopics(keyword)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Topic search failed: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func cacheSearchResults(data map[string]interface{}) {
	items, ok := data["items"].([]interface{})
	if !ok {
		return
	}

	var indexEntries []map[string]string
	for _, item := range items {
		itemMap, ok := item.(map[string]interface{})
		if !ok {
			continue
		}

		noteCard, _ := itemMap["note_card"].(map[string]interface{})
		noteID := ""
		if id, ok := itemMap["id"].(string); ok {
			noteID = id
		} else if noteCard != nil {
			if id, ok := noteCard["note_id"].(string); ok {
				noteID = id
			}
		}

		xsecToken := ""
		if t, ok := itemMap["xsec_token"].(string); ok {
			xsecToken = t
		} else if noteCard != nil {
			if t, ok := noteCard["xsec_token"].(string); ok {
				xsecToken = t
			}
		}

		if noteID != "" {
			indexEntries = append(indexEntries, map[string]string{
				"note_id":     noteID,
				"xsec_token":  xsecToken,
				"xsec_source": "pc_search",
			})
		}
	}

	if len(indexEntries) > 0 {
		home, _ := os.UserHomeDir()
		cacheDir := home + "/.xiaohongshu-cli"
		os.MkdirAll(cacheDir, 0700)
		cacheData, _ := json.MarshalIndent(indexEntries, "", "  ")
		os.WriteFile(cacheDir+"/index_cache.json", cacheData, 0600)
	}
}
