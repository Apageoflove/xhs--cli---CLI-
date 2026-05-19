package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"xhs-cli-go/internal/config"
)

func NewLoginCmd() *cobra.Command {
	var cookieSource string
	var useQRCode bool
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "login",
		Short: "Log in by extracting cookies from browser, or via QR code",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			if useQRCode {
				env := ErrorEnvelope("QR code login is not implemented in this version. Please use browser cookie extraction or import-cookies.")
				PrintEnvelope(env, format)
				return
			}

			if cookieSource == "" {
				cookieSource = "auto"
			}

			fmt.Println("To log in, please provide your Xiaohongshu cookies.")
			fmt.Println("You can export cookies from your browser after logging in to https://www.xiaohongshu.com/")
			fmt.Println()
			fmt.Println("Please enter the 'a1' cookie value:")
			var a1 string
			fmt.Scanln(&a1)
			a1 = strings.TrimSpace(a1)

			if a1 == "" {
				env := ErrorEnvelope("No 'a1' cookie provided")
				PrintEnvelope(env, format)
				return
			}

			fmt.Println("Please enter the 'web_session' cookie value (optional):")
			var webSession string
			fmt.Scanln(&webSession)
			webSession = strings.TrimSpace(webSession)

			cookies := map[string]string{
				"a1": a1,
			}
			if webSession != "" {
				cookies["web_session"] = webSession
			}

			if err := config.SaveCookies(cookies); err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to save cookies: %v", err))
				PrintEnvelope(env, format)
				return
			}

			env := SuccessEnvelope(map[string]interface{}{
				"authenticated": true,
				"message":       "Cookies saved successfully",
			})
			PrintEnvelope(env, format)
		},
	}

	cmd.Flags().StringVar(&cookieSource, "cookie-source", "", "Browser to read cookies from (default: auto-detect)")
	cmd.Flags().BoolVar(&useQRCode, "qrcode", false, "Login via QR code")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewStatusCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "status",
		Short: "Check current login status and user info",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				env := ErrorEnvelope(err.Error())
				PrintEnvelope(env, format)
				return
			}
			defer c.Close()

			info, err := c.GetSelfInfo()
			if err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to get status: %v", err))
				PrintEnvelope(env, format)
				return
			}

			user := NormalizeUserInfo(info)
			env := SuccessEnvelope(map[string]interface{}{
				"authenticated": true,
				"user":          user,
			})
			PrintEnvelope(env, format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewWhoamiCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "whoami",
		Short: "Show detailed profile of current user",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			c, err := GetClient()
			if err != nil {
				env := ErrorEnvelope(err.Error())
				PrintEnvelope(env, format)
				return
			}
			defer c.Close()

			info, err := c.GetSelfInfo()
			if err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to get profile: %v", err))
				PrintEnvelope(env, format)
				return
			}

			user := NormalizeUserInfo(info)
			env := SuccessEnvelope(map[string]interface{}{
				"user": user,
			})
			PrintEnvelope(env, format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewLogoutCmd() *cobra.Command {
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "logout",
		Short: "Clear saved cookies and log out",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			if err := config.ClearCookies(); err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to clear cookies: %v", err))
				PrintEnvelope(env, format)
				return
			}

			env := SuccessEnvelope(map[string]interface{}{
				"logged_out": true,
			})
			PrintEnvelope(env, format)
		},
	}

	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}

func NewImportCookiesCmd() *cobra.Command {
	var filePath string
	var asJSON bool
	var asYAML bool

	cmd := &cobra.Command{
		Use:   "import-cookies",
		Short: "Import cookies from a JSON file",
		Run: func(cmd *cobra.Command, args []string) {
			format := getOutputFormat(asJSON, asYAML)

			data, err := os.ReadFile(filePath)
			if err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to read file: %v", err))
				PrintEnvelope(env, format)
				return
			}

			var cookies map[string]string
			if err := json.Unmarshal(data, &cookies); err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to parse JSON: %v", err))
				PrintEnvelope(env, format)
				return
			}

			if cookies["a1"] == "" {
				env := ErrorEnvelope("No 'a1' cookie found in the file")
				PrintEnvelope(env, format)
				return
			}

			if err := config.SaveCookies(cookies); err != nil {
				env := ErrorEnvelope(fmt.Sprintf("Failed to save cookies: %v", err))
				PrintEnvelope(env, format)
				return
			}

			env := SuccessEnvelope(map[string]interface{}{
				"imported": true,
				"message":  "Cookies imported successfully",
			})
			PrintEnvelope(env, format)
		},
	}

	cmd.Flags().StringVarP(&filePath, "file", "f", "", "Path to the JSON cookie file")
	cmd.MarkFlagRequired("file")
	cmd.Flags().BoolVar(&asJSON, "json", false, "Output as JSON")
	cmd.Flags().BoolVar(&asYAML, "yaml", false, "Output as YAML")

	return cmd
}
