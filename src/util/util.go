package util

import (
	"bufio"
	"bytes"
	"golang.org/x/text/encoding/simplifiedchinese"
	"golang.org/x/text/transform"
	"io"
	"net/http"
	"net/url"
)

func GetHTML(url string, isGbk bool) (io.Reader, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var buffer bytes.Buffer
	writer := bufio.NewWriter(&buffer)

	if isGbk {
		reader := transform.NewReader(resp.Body, simplifiedchinese.GBK.NewDecoder())
		_, err = io.Copy(writer, reader)
	} else {
		_, err = io.Copy(writer, resp.Body)
	}
	if err != nil {
		return nil, err
	}
	return &buffer, nil
}

func GetAbsUrl(baseUrl string, relativeUrl string) (string, error) {
	base, e := url.Parse(baseUrl)
	if e != nil {
		return "", e
	}
	relative, e := url.Parse(relativeUrl)
	if e != nil {
		return "", e
	}
	return base.ResolveReference(relative).String(), nil
}
