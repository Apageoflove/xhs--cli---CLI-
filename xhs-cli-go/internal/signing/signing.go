package signing

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/md5"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math/big"
	"net/url"
	"strconv"
	"strings"
	"time"
)

var aesKey = []byte("7cc4adla5ay0701v")
var aesIV = []byte("4uzjr7mbsibcaldp")

// SignHeaders represents the signing headers for XHS API requests
type SignHeaders struct {
	XS          string
	XSCommon    string
	XT          string
	XB3TraceID  string
	XXrayTraceID string
}

// SignMainAPI generates signing headers for main API (edith.xiaohongshu.com) requests
func SignMainAPI(method, uri string, cookies map[string]string, params map[string]interface{}, payload map[string]interface{}) (*SignHeaders, error) {
	timestamp := time.Now().UnixMilli()

	traceID := generateTraceID()
	xrayTraceID := generateXrayTraceID()

	xsCommon := buildXSCommon(timestamp)
	xs := buildXS(method, uri, cookies, timestamp)

	return &SignHeaders{
		XS:           xs,
		XSCommon:     xsCommon,
		XT:           strconv.FormatInt(timestamp, 10),
		XB3TraceID:   traceID,
		XXrayTraceID: xrayTraceID,
	}, nil
}

func generateTraceID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func generateXrayTraceID() string {
	root := make([]byte, 16)
	rand.Read(root)
	parent := make([]byte, 8)
	rand.Read(parent)
	return fmt.Sprintf("Root=%s;Parent=%s;Sampled=0", hex.EncodeToString(root), hex.EncodeToString(parent))
}

func buildXSCommon(timestamp int64) string {
	return fmt.Sprintf("1-WEJIRW93ZQ==-%d-s1=%%3Bx0=1%%3Bx1=4.2.6%%3Bx2=macOS%%3Bx3=xhs-pc-web%%3Bx4=4.86.0%%3Bx9=-596800761%%3Bx10=0%%3Bx11=normal", timestamp/1000)
}

func buildXS(method, uri string, cookies map[string]string, timestamp int64) string {
	var signStr strings.Builder
	signStr.WriteString(strings.ToUpper(method))
	signStr.WriteString(uri)

	if a1, ok := cookies["a1"]; ok {
		signStr.WriteString(a1)
	}
	signStr.WriteString(strconv.FormatInt(timestamp, 10))

	hash := fnvHash(signStr.String())
	return fmt.Sprintf("x0=4.2.6;x1=xhs-pc-web;x2=macOS;x3=%s;x4=%s", hash, strconv.FormatInt(timestamp, 36))
}

func fnvHash(s string) string {
	var h uint64 = 1469598103934665603
	for _, c := range s {
		h ^= uint64(c)
		h *= 1099511628211
	}
	return strconv.FormatUint(h, 36)
}

// SignCreator generates creator platform signature (XYW_ prefix)
func SignCreator(api string, data map[string]interface{}, a1 string) (string, string) {
	content := api
	if data != nil {
		jsonData, _ := json.Marshal(data)
		content += string(jsonData)
	}

	x1 := md5Hash(content)
	x2 := "0|0|0|1|0|0|1|0|0|0|1|0|0|0|0|1|0|0|0"
	x3 := a1
	x4 := time.Now().UnixMilli()

	plaintext := fmt.Sprintf("x1=%s;x2=%s;x3=%s;x4=%d;", x1, x2, x3, x4)
	encoded := base64.StdEncoding.EncodeToString([]byte(plaintext))
	payload := aesEncrypt(encoded)

	envelope := map[string]interface{}{
		"signSvn":     "56",
		"signType":    "x2",
		"appId":       "ugc",
		"signVersion": "1",
		"payload":     payload,
	}
	envJSON, _ := json.Marshal(envelope)
	xs := "XYW_" + base64.StdEncoding.EncodeToString(envJSON)

	return xs, strconv.FormatInt(x4, 10)
}

func md5Hash(s string) string {
	h := md5.Sum([]byte(s))
	return hex.EncodeToString(h[:])
}

func aesEncrypt(data string) string {
	block, _ := aes.NewCipher(aesKey)
	padded := pkcs7Pad([]byte(data), aes.BlockSize)
	ciphertext := make([]byte, len(padded))
	mode := cipher.NewCBCEncrypter(block, aesIV)
	mode.CryptBlocks(ciphertext, padded)
	return hex.EncodeToString(ciphertext)
}

func pkcs7Pad(data []byte, blockSize int) []byte {
	padding := blockSize - len(data)%blockSize
	padText := make([]byte, padding)
	for i := range padText {
		padText[i] = byte(padding)
	}
	return append(data, padText...)
}

// BuildGetURI builds a URI with query parameters for GET requests
func BuildGetURI(uri string, params map[string]interface{}) string {
	if params == nil || len(params) == 0 {
		return uri
	}

	var buf strings.Builder
	buf.WriteString(uri)
	if strings.Contains(uri, "?") {
		buf.WriteString("&")
	} else {
		buf.WriteString("?")
	}

	first := true
	for k, v := range params {
		if !first {
			buf.WriteString("&")
		}
		buf.WriteString(url.QueryEscape(k))
		buf.WriteString("=")
		buf.WriteString(url.QueryEscape(fmt.Sprintf("%v", v)))
		first = false
	}
	return buf.String()
}

// GenerateSearchID generates a unique search ID (base36 of timestamp << 64 + random)
func GenerateSearchID() string {
	e := big.NewInt(time.Now().UnixMilli())
	e.Lsh(e, 64)

	t, _ := rand.Int(rand.Reader, big.NewInt(2147483647))
	num := new(big.Int).Add(e, t)

	if num.Cmp(big.NewInt(0)) == 0 {
		return "0"
	}

	alphabet := "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	base := big.NewInt(36)
	result := ""

	tmp := new(big.Int).Set(num)
	for tmp.Cmp(big.NewInt(0)) > 0 {
		mod := new(big.Int).Mod(tmp, base)
		result = string(alphabet[mod.Int64()]) + result
		tmp.Div(tmp, base)
	}

	return result
}
