package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

func NewNotificationsCmd() *cobra.Command {
	var notifType string
	var cursor string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "notifications",
		Short: "View notifications (mentions, likes, connections)",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			var result map[string]interface{}

			switch notifType {
			case "mentions":
				result, err = c.GetNotificationMentions(cursor, 20)
			case "likes":
				result, err = c.GetNotificationLikes(cursor, 20)
			case "connections":
				result, err = c.GetNotificationConnections(cursor, 20)
			default:
				result, err = c.GetNotificationMentions(cursor, 20)
			}

			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get notifications: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVar(&notifType, "type", "mentions", "Notification type: mentions, likes, connections")
	cmd.Flags().StringVar(&cursor, "cursor", "", "Pagination cursor")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewUnreadCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "unread",
		Short: "Show unread notification counts",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.GetUnreadCount()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to get unread count: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}
