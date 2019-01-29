package novel

import (
	"github.com/PuerkitoBio/goquery"
	"io"
	"log"
	"regexp"
	"strings"
	"util"
)

type TxtJia struct {
}

func (t *TxtJia) IsGbk() bool {
	return true
}

func (t *TxtJia) NovelInfo(reader io.Reader, n *Novel) {
	document, e := goquery.NewDocumentFromReader(reader)
	if e != nil {
		log.Fatal(e)
	}

	n.Name = strings.TrimSpace(document.Find("h2").First().Text()) // 书名

	// 封面
	cover, exists := document.Find("#BookImage").Attr("src")
	if exists {
		n.Cover = cover
	}

	// 章节页
	indexLink, exists := document.Find(".readnow").Attr("href")
	if exists {
		url, err := util.GetAbsUrl(n.IntroLink, indexLink)
		if err != nil {
			panic("parse index page error")
		}
		n.IndexLink = url
	}

	// id
	lastFindChar := strings.LastIndex(n.IndexLink[:len(n.IndexLink)-1], "/")
	n.Id = n.IndexLink[lastFindChar+1 : len(n.IndexLink)-1]

	// 分类
	intrSel := document.Find(".intr")
	n.Subject = intrSel.Find("a").Text()

	// 作者
	matched := regexp.MustCompile("作者：(.*)").FindStringSubmatch(intrSel.Text())
	if matched[1] != "" {
		n.Author = matched[1]
	}
}

func (t *TxtJia) NovelChapterList(reader io.Reader, n *Novel) {
	document, e := goquery.NewDocumentFromReader(reader)
	if e != nil {
		log.Fatal(e)
	}
	document.Find(".list li").Each(func(i int, selection *goquery.Selection) {
		href, exists := selection.Find("a").Attr("href")
		var url string
		var err error
		if exists {
			url, err = util.GetAbsUrl(n.IndexLink, href)
		}
		if err == nil {
			n.Chapters = append(n.Chapters, &Chapter{i, selection.Text(), url})
		} else {
			log.Println(err)
		}
	})
}
