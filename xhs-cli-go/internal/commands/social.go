package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

func NewFollowCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "follow [user_id]",
		Short: "Follow a user",
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

			result, err := c.FollowUser(userID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to follow user: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewUnfollowCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "unfollow [user_id]",
		Short: "Unfollow a user",
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

			result, err := c.UnfollowUser(userID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to unfollow user: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewFavoritesCmd() *cobra.Command {
	var cursor string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "favorites [user_id]",
		Short: "List favorited (bookmarked) notes",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			userID := ""
			if len(args) > 0 {
				userID = args[0]
			}

			if userID == "" {
				info, err := c.GetSelfInfo()
				if err != nil {
					PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get self info: %v", err)), format)
					return
				}
				if data, ok := info["user_id"].(string); ok {
					userID = data
				} else if sub, ok := info["user_info"].(map[string]interface{}); ok {
					userID, _ = sub["user_id"].(string)
				}
			}

			result, err := c.GetUserFavorites(userID, cursor)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get favorites: %v", err)), format)
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

func NewLikesCmd() *cobra.Command {
	var cursor string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "likes [user_id]",
		Short: "List liked notes",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			userID := ""
			if len(args) > 0 {
				userID = args[0]
			}

			if userID == "" {
				info, err := c.GetSelfInfo()
				if err != nil {
					PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get self info: %v", err)), format)
					return
				}
				if data, ok := info["user_id"].(string); ok {
					userID = data
				} else if sub, ok := info["user_info"].(map[string]interface{}); ok {
					userID, _ = sub["user_id"].(string)
				}
			}

			result, err := c.GetUserLikes(userID, cursor)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get likes: %v", err)), format)
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
