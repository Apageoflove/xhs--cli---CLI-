package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

func NewLikeCmd() *cobra.Command {
	var undo bool
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "like [id_or_url_or_index]",
		Short: "Like or unlike a note",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			noteID, _, _ := resolveNoteRef(input, "")

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			var result map[string]interface{}
			if undo {
				result, err = c.UnlikeNote(noteID)
			} else {
				result, err = c.LikeNote(noteID)
			}

			if err != nil {
				action := "like"
				if undo {
					action = "unlike"
				}
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to %s note: %v", action, err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&undo, "undo", false, "Unlike the note")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewFavoriteCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "favorite [id_or_url_or_index]",
		Short: "Favorite (bookmark) a note",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			noteID, _, _ := resolveNoteRef(input, "")

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.FavoriteNote(noteID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to favorite note: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewUnfavoriteCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "unfavorite [id_or_url_or_index]",
		Short: "Unfavorite (unbookmark) a note",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			noteID, _, _ := resolveNoteRef(input, "")

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.UnfavoriteNote(noteID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to unfavorite note: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewCommentCmd() *cobra.Command {
	var content string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "comment [id_or_url_or_index]",
		Short: "Post a comment on a note",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			if content == "" {
				PrintEnvelope(ErrorEnvelope("Comment content is required (-c)"), format)
				return
			}

			noteID, _, _ := resolveNoteRef(input, "")

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.PostComment(noteID, content)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to post comment: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVarP(&content, "content", "c", "", "Comment text")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewReplyCmd() *cobra.Command {
	var content string
	var commentID string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "reply [id_or_url_or_index]",
		Short: "Reply to a specific comment",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			input := args[0]
			format := getOutputFormat(asJSON, asYAML)

			if content == "" {
				PrintEnvelope(ErrorEnvelope("Reply content is required (-c)"), format)
				return
			}
			if commentID == "" {
				PrintEnvelope(ErrorEnvelope("Comment ID is required (--comment-id)"), format)
				return
			}

			noteID, _, _ := resolveNoteRef(input, "")

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.ReplyComment(noteID, commentID, content)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to reply: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().StringVarP(&content, "content", "c", "", "Reply text")
	cmd.Flags().StringVar(&commentID, "comment-id", "", "Comment ID to reply to")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewDeleteCommentCmd() *cobra.Command {
	var yes bool
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "delete-comment [note_id] [comment_id]",
		Short: "Delete a comment you posted",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			noteID := args[0]
			commentID := args[1]
			format := getOutputFormat(asJSON, asYAML)

			if !yes {
				fmt.Printf("Delete comment %s on note %s? [y/N] ", commentID, noteID)
				var confirm string
				fmt.Scanln(&confirm)
				if confirm != "y" && confirm != "Y" {
					PrintEnvelope(ErrorEnvelope("Cancelled"), format)
					return
				}
			}

			c, err := GetClient()
			if err != nil {
				PrintEnvelope(ErrorEnvelope(err.Error()), format)
				return
			}
			defer c.Close()

			result, err := c.DeleteComment(noteID, commentID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to delete comment: %v", err)), format)
				return
			}

			PrintEnvelope(SuccessEnvelope(result), format)
		},
	}

	cmd.Flags().BoolVarP(&yes, "yes", "y", false, "Skip confirmation")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}
