package novel

import (
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"os"
	"os/signal"
	"runtime"
	"strconv"
	"sync"
	"util"
)

type Parse interface {
	IsGbk() bool // 通过设置编码，避免自动识别编码带来的内存拷贝

	NovelInfo(reader io.Reader, n *Novel)        // 解析书籍基础信息
	NovelChapterList(reader io.Reader, n *Novel) // 解析书籍章节列表
}

type Chapter struct {
	Index int
	Title string
	Url   string
}

type Novel struct {
	IntroLink string     // 介绍页
	Cover     string     // 封面
	Name      string     // 书名
	IndexLink string     // 索引页
	Id        string     // id
	Author    string     // 作者
	Subject   string     // 分类
	Chapters  []*Chapter // 章节列表

	done chan struct{} // 终止信道
}

func NewNovel(introLink string) *Novel {
	return &Novel{IntroLink: introLink}
}

func (n *Novel) Start(parse Parse) {
	if n.IntroLink == "" {
		panic("intro page is nil")
	}
	introPage, err := util.GetHTML(n.IntroLink, parse.IsGbk())
	if err != nil {
		panic(err)
	}
	parse.NovelInfo(introPage, n) // 解析基础信息

	var indexPage io.Reader
	if n.IndexLink == "" || n.IndexLink == n.IntroLink {
		indexPage = introPage
	} else {
		indexPage, err = util.GetHTML(n.IndexLink, parse.IsGbk())
		if err != nil {
			panic(err)
		}
	}

	parse.NovelChapterList(indexPage, n) // 解析章节列表
	if len(n.Chapters) == 0 {
		log.Fatal("chapter list is empty")
	}

	// 处理退出
	n.done = make(chan struct{})
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, os.Kill)

	go func() {
		<-c // ctrl-c
		close(n.done)
	}()

	n.downloadChapters(parse)
}

func (n *Novel) cancelled() bool {
	select {
	case <-n.done:
		return true
	default:
		return false
	}
}

func (n *Novel) downloadChapters(parse Parse) {
	var count int
	var downloaded = make(chan bool)

	go func() {
		for {
			select {
			case <-downloaded:
				count++
				per := fmt.Sprintf("%d/%d\r", count, len(n.Chapters))
				_, _ = os.Stdout.Write([]byte(per))
			case <-n.done:
				return
			}
		}
	}()

	var wg sync.WaitGroup
	var sema = make(chan struct{}, runtime.NumCPU()*2)
	for _, chapterInfo := range n.Chapters[:5] {
		wg.Add(1)
		go func(info *Chapter) {
			defer wg.Done()

			// 请求信号量
			select {
			case sema <- struct{}{}:
			case <-n.done:
				return
			}
			defer func() { <-sema }()

			// 执行操作
			reader, e := util.GetHTML(info.Url, parse.IsGbk())
			if e != nil {
				log.Printf("chapter get failed: %d %s \n %s", info.Index, info.Title, e)
				return
			}
			chapterBytes, e := ioutil.ReadAll(reader)
			if e != nil {
				log.Printf("chapter reader failed: %d %s\n %s", info.Index, info.Title, e)
				return
			}
			e = ioutil.WriteFile(strconv.Itoa(info.Index)+".txt", chapterBytes, 0644)
			if e != nil {
				log.Printf("chapter write file failed: %d %s\n %s", info.Index, info.Title, e)
				return
			}
			downloaded <- true
		}(chapterInfo)
	}
	wg.Wait()
}
