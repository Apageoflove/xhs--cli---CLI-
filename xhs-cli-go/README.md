# xhs-cli-go

Go implementation of Xiaohongshu (小红书) CLI tool, compatible with the Python version's configuration.

## Features

### Authentication Commands
- `xhs login` - Log in by providing cookies manually
- `xhs login --qrcode` - QR code login (placeholder)
- `xhs status` - Check current login status
- `xhs whoami` - Show detailed profile of current user
- `xhs logout` - Clear saved cookies
- `xhs import-cookies -f <file>` - Import cookies from a JSON file

### Search Commands
- `xhs search <keyword>` - Search notes by keyword
- `xhs search <keyword> --sort popular` - Sort by popularity
- `xhs search <keyword> --type video` - Filter by note type
- `xhs search <keyword> --page 2` - Pagination
- `xhs search-user <keyword>` - Search users
- `xhs topics <keyword>` - Search topics/hashtags

## Configuration Compatibility

This Go version is fully compatible with the Python version's configuration:

- Config directory: `~/.xiaohongshu-cli/`
- Cookie file: `~/.xiaohongshu-cli/cookies.json`
- Token cache: `~/.xiaohongshu-cli/token_cache.json`
- Index cache: `~/.xiaohongshu-cli/index_cache.json`

You can share cookies between the Python and Go versions.

## Installation

```bash
cd xhs-cli-go
go mod tidy
go build -o xhs ./cmd/xhs
```

## Usage

### Logging in

```bash
# Import cookies from a JSON file (recommended)
xhs import-cookies -f /path/to/cookies.json

# Or provide cookies interactively
xhs login
```

The cookie file should be a JSON file with at least the `a1` cookie:
```json
{
  "a1": "your_a1_cookie_value",
  "web_session": "your_web_session_cookie_value"
}
```

### Searching

```bash
# Search notes
xhs search "美食"

# Search with sorting
xhs search "旅行" --sort popular

# Search by type
xhs search "穿搭" --type video

# Search users
xhs search-user "用户名"

# Search topics
xhs topics "美食"
```

### Output Formats

```bash
# JSON output
xhs search "美食" --json

# YAML output
xhs search "美食" --yaml

# Environment variable
OUTPUT=json xhs whoami
```

Non-TTY output defaults to YAML format automatically.

## Limitations

- Browser cookie auto-extraction is not implemented (requires browser_cookie3 equivalent in Go)
- QR code login is not implemented in this version
- Request signing is simplified - the full xhshow algorithm is complex and not fully ported
- Some anti-detection features (Gaussian jitter, etc.) are simplified
