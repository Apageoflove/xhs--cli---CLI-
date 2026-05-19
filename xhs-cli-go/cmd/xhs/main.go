package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"xhs-cli-go/internal/commands"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "xhs",
		Short: "xhs — Xiaohongshu CLI via reverse-engineered API",
		Long:  `xhs is a CLI tool for Xiaohongshu (小红书) that allows you to search, read, and interact with the platform.`,
		Run: func(cmd *cobra.Command, args []string) {
			cmd.Help()
		},
	}

	// Auth commands
	rootCmd.AddCommand(commands.NewLoginCmd())
	rootCmd.AddCommand(commands.NewStatusCmd())
	rootCmd.AddCommand(commands.NewWhoamiCmd())
	rootCmd.AddCommand(commands.NewLogoutCmd())
	rootCmd.AddCommand(commands.NewImportCookiesCmd())

	// Search commands
	rootCmd.AddCommand(commands.NewSearchCmd())
	rootCmd.AddCommand(commands.NewSearchUserCmd())
	rootCmd.AddCommand(commands.NewTopicsCmd())

	// Reading commands
	rootCmd.AddCommand(commands.NewReadCmd())
	rootCmd.AddCommand(commands.NewCommentsCmd())
	rootCmd.AddCommand(commands.NewSubCommentsCmd())
	rootCmd.AddCommand(commands.NewUserCmd())
	rootCmd.AddCommand(commands.NewUserPostsCmd())
	rootCmd.AddCommand(commands.NewFeedCmd())
	rootCmd.AddCommand(commands.NewHotCmd())
	rootCmd.AddCommand(commands.NewMyNotesCmd())

	// Interaction commands
	rootCmd.AddCommand(commands.NewLikeCmd())
	rootCmd.AddCommand(commands.NewFavoriteCmd())
	rootCmd.AddCommand(commands.NewUnfavoriteCmd())
	rootCmd.AddCommand(commands.NewCommentCmd())
	rootCmd.AddCommand(commands.NewReplyCmd())
	rootCmd.AddCommand(commands.NewDeleteCommentCmd())

	// Social commands
	rootCmd.AddCommand(commands.NewFollowCmd())
	rootCmd.AddCommand(commands.NewUnfollowCmd())
	rootCmd.AddCommand(commands.NewFavoritesCmd())
	rootCmd.AddCommand(commands.NewLikesCmd())

	// Notification commands
	rootCmd.AddCommand(commands.NewNotificationsCmd())
	rootCmd.AddCommand(commands.NewUnreadCmd())

	// Creator commands
	rootCmd.AddCommand(commands.NewPostCmd())
	rootCmd.AddCommand(commands.NewDeleteCmd())

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
