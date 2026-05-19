package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

func NewPostCmd() *cobra.Command {
	var title string
	var body string
	var images []string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "post",
		Short: "Publish an image note (creator platform)",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			if title == "" && body == "" {
				PrintEnvelope(ErrorEnvelope("At least --title or --body is required"), format)
				return
			}

			PrintEnvelope(ErrorEnvelope("Post command requires file upload support which is not yet implemented in Go version. Use the Python version for posting."), format)
		},
	}

	cmd.Flags().StringVar(&title, "title", "", "Note title")
	cmd.Flags().StringVar(&body, "body", "", "Note body/description")
	cmd.Flags().StringArrayVar(&images, "images", nil, "Image file paths")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewDeleteCmd() *cobra.Command {
	var yes bool
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "delete [note_id]",
		Short: "Delete a note (experimental)",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			noteID := args[0]
			format := getOutputFormat(asJSON, asYAML)

			if !yes {
				fmt.Printf("Delete note %s? This cannot be undone. [y/N] ", noteID)
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

			result, err := c.DeleteNote(noteID)
			if err != nil {
				PrintEnvelope(ErrorEnvelope(fmt.Sprintf("Failed to delete note: %v", err)), format)
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
